# frozen_string_literal: true

require "json"
require "net/http"

module Mem20
  # Thread-safe facade over the mem20 tool surface.
  #
  #   client = Mem20::Client.new(Mem20.configuration)
  #   client.memory_store(content: "the sky is blue", category: "general")
  #   client.memory_recall(query: "sky", limit: 5)
  #
  # {#tool} reaches every one of the {Surface::TOOL_COUNT} tools the server
  # registers (see {Mem20::Surface} for how that count decomposes). The
  # convenience accessors below cover the memory primitives; the dynamic
  # bindings let you call any registered tool as if it were a method.
  class Client
    def initialize(config = nil, **options)
      @config = config || Config.from_env(**options)
      # Freeze the config so it cannot change under a running client.
      @config = @config.freeze! if @config.respond_to?(:freeze!)
      @transport = nil
      @transport_mutex = Mutex.new
      @tool_names = nil
    end

    attr_reader :config

    # Replace the lazily built transport. Used by tests (an in-process double
    # instead of a child process) and by callers bringing their own transport;
    # it is synchronised so it cannot race the lazy `#transport` build.
    def transport=(candidate)
      @transport_mutex.synchronize { @transport = candidate }
    end

    # Lazily start (and memoise) the underlying transport, completing the MCP
    # handshake before the first call.
    def transport
      @transport_mutex.synchronize do
        @transport ||= Transport::Stdio.new(@config).tap(&:initialize_session)
      end
    end

    # Call any mem20 tool by name.
    #
    # Arguments may be given as keywords or as a single Hash - both spellings
    # are documented, and both must work. Under Ruby 3.x a trailing Hash is no
    # longer converted to keywords automatically, so `tool("memory_status", {})`
    # used to raise `ArgumentError: wrong number of arguments (given 2)`.
    #
    #   client.tool("memory_recall", query: "sky", limit: 5)
    #   client.tool("memory_recall", {"query" => "sky", "limit" => 5})
    #   client.tool("memory_status")
    def tool(name, arguments = nil, **params)
      merged = arguments.nil? ? params : merge_arguments(name, arguments, params)
      transport.request("tools/call", "name" => name.to_s, "arguments" => stringify(merged))
    end

    # List the tools the server exposes.
    def tools
      transport.request("tools/list", {})
    end

    # The names of every registered tool (cached after the first call).
    def tool_names
      @tool_names ||= (tools["tools"] || []).map { |t| t["name"] }
    end

    # --- mem20 memory primitives -----------------------------------------

    # Store a fact. `tags` may be an Array (joined into the comma-separated
    # form the server expects) or a pre-formatted String.
    def memory_store(content:, category: "general", tags: nil)
      args = { "content" => content, "category" => category }
      args["tags"] = tags.is_a?(Array) ? tags.join(",") : tags.to_s if tags
      tool("memory_store", **args)
    end

    # Search stored facts.
    def memory_recall(query:, category: nil, limit: nil)
      args = { "query" => query }
      args["category"] = category if category
      args["limit"] = limit if limit
      tool("memory_recall", **args)
    end

    # The plain-text payload of a tool result envelope.
    def self.text(result)
      Array(result["content"]).filter_map { |c| c["text"] }.join("\n")
    end

    def text(result) = self.class.text(result)

    # --- background jobs -------------------------------------------------
    #
    # A long-running tool (`cog_*`, `tot_*`, `imagination_*`, `beam_search`,
    # `react_reason`, ...) answers `tools/call` with a job envelope instead of a
    # result. These helpers turn that envelope back into a value.
    #
    #   job = client.job_from(client.cog_reason(question: "why is the sky blue?"))
    #   result = client.wait_for_job(job, timeout: 120)
    #   result.value   # => the tool's payload
    #
    # A rejected job raises Mem20::JobError; it never comes back as `nil`.

    # Parse the envelope returned by a long-running tool. Accepts the
    # `tools/call` result Hash, a {Mem20::JobEnvelope}, or a bare job id.
    def job_from(response)
      JobEnvelope.from(response)
    end

    # One non-blocking `job_status` poll. Returns a {Mem20::JobResult}; raises
    # {Mem20::JobError} when the job was rejected.
    def job_status(job)
      Job.status(self, job)
    end

    # Server-side block: `job_wait` on the server, bounded by `timeout_ms`.
    def job_wait(job, timeout_ms: 30_000)
      envelope = JobEnvelope.from(job)
      result = tool(envelope.wait_tool, job_id: envelope.job_id, timeout_ms: timeout_ms)
      JobResult.from_snapshot(JobResult.snapshot(result), attempts: 1, timed_out: false)
    end

    # Poll a job until it reaches a terminal state, or until the wait window
    # closes. Returns a {Mem20::JobResult}: `#ok?` with a decoded `#value` when
    # the job finished, `#timed_out?` and still `running` when the window
    # closed first. A rejected job (`error` / `not_found`) raises
    # {Mem20::JobError}, so this never returns `nil`.
    #
    #   client.wait_for_job(job, timeout: 120, interval: 1)
    #   client.wait_for_job(job, max_attempts: 3)   # bound a hung job
    #   client.wait_for_job(job, Mem20::Job::WaitWindow.build(timeout: 5))
    #
    # `max_attempts` bounds the number of polls independently of `timeout`, so
    # a job that keeps answering `running` is still bounded.
    def wait_for_job(job, window = nil, **options)
      window ||= Job::WaitWindow.build(**options)
      Job.wait(self, job, window)
    end

    # --- health surface --------------------------------------------------

    # `GET /health` -> parsed JSON, or nil when the endpoint is not answering.
    def health
      http_json("/health")
    rescue TransportError
      nil
    end

    # `GET /ready` -> parsed JSON, or nil when the endpoint is not answering.
    def ready
      http_json("/ready")
    rescue TransportError
      nil
    end

    # True when `GET :port/health` answers with a 2xx status.
    def healthy?
      response = Net::HTTP.get_response(URI("#{@config.health_url}/health"))
      response.is_a?(Net::HTTPSuccess)
    rescue StandardError
      false
    end

    # Parsed counters from `GET :port/metrics`.
    def metrics
      http_json("/metrics")
    end

    def close
      @transport_mutex.synchronize do
        @transport&.close
        @transport = nil
      end
    end

    alias shutdown close

    # Idiomatic dynamic bindings: any tool the server registers can be called
    # as a method, e.g. `client.memory_status`.
    def method_missing(name, *args, **kwargs, &block)
      return super unless callable_tool?(name)
      raise ArgumentError, "#{name} accepts keyword arguments only" unless args.empty? && block.nil?

      tool(name.to_s, **kwargs)
    end

    def respond_to_missing?(name, include_private = false)
      callable_tool?(name) || super
    end

    private

    def callable_tool?(name)
      return @tool_names.include?(name.to_s) if @tool_names

      tool_names.include?(name.to_s)
    rescue StandardError
      false
    end

    def http_json(path)
      body = Net::HTTP.get(URI("#{@config.health_url}#{path}"))
      JSON.parse(body)
    rescue StandardError => e
      raise TransportError, "could not read #{@config.health_url}#{path}: #{e.message}"
    end

    def merge_arguments(name, arguments, params)
      unless arguments.is_a?(Hash)
        raise ArgumentError, "tool(#{name.inspect}) arguments must be a Hash, got #{arguments.class}"
      end

      arguments.to_h.merge(params)
    end

    def stringify(params)
      params.each_with_object({}) { |(k, v), acc| acc[k.to_s] = v }
    end
  end
end
