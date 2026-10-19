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
  # {#tool} reaches every one of the 257 tools the server registers. The
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

    # Lazily start (and memoise) the underlying transport, completing the MCP
    # handshake before the first call.
    def transport
      @transport_mutex.synchronize do
        @transport ||= Transport::Stdio.new(@config).tap(&:initialize_session)
      end
    end

    # Call any mem20 tool by name.
    def tool(name, **params)
      transport.request("tools/call", "name" => name.to_s, "arguments" => stringify(params))
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

    def stringify(params)
      params.each_with_object({}) { |(k, v), acc| acc[k.to_s] = v }
    end
  end
end
