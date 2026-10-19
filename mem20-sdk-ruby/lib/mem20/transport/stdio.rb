# frozen_string_literal: true

require "json"
require "open3"
require "timeout"

module Mem20
  module Transport
    # JSON-RPC 2.0 client over newline-delimited stdio, matching the transport
    # the mem20 server exposes (MCP revision 2025-06-18).
    #
    # One instance owns one child process and serialises access to it, so a
    # single client can be shared between threads.
    class Stdio
      # The MCP handshake result, as the SDK presents it to callers.
      Session = Struct.new(:protocol_version, :server_info, :capabilities, keyword_init: true)

      attr_reader :pid

      def initialize(config)
        @config = config
        @mutex = Mutex.new
        @next_id = 0
        @stderr_buffer = +""
        start_process
      end

      # Send a request and wait for the matching response.
      def request(method, params = {})
        @mutex.synchronize do
          ensure_alive!
          id = (@next_id += 1)
          write_message(id: id, method: method, params: params)
          read_response(id)
        end
      end

      # Fire-and-forget notification (no reply expected).
      def notify(method, params = {})
        @mutex.synchronize do
          ensure_alive!
          write_message(method: method, params: params)
        end
        nil
      end

      # Perform the MCP initialize handshake once, before any tool call.
      # Returns a {Session} with the protocol revision the server negotiated.
      def initialize_session
        return @session if @session

        result = request(
          "initialize",
          protocolVersion: @config.protocol_version,
          capabilities: {},
          clientInfo: { name: "mem20-sdk-ruby", version: Mem20::VERSION }
        )
        notify("notifications/initialized", {})
        @session = Session.new(
          protocol_version: result["protocolVersion"],
          server_info: result["serverInfo"] || {},
          capabilities: result["capabilities"] || {}
        )
      end

      def close
        return if @process.nil?

        [@stdin, @stdout, @stderr].each do |io|
          io&.close
        rescue StandardError
          nil
        end
        begin
          Process.kill("TERM", @pid)
        rescue StandardError
          nil
        end
        begin
          Process.wait(@pid)
        rescue StandardError
          nil
        end
      ensure
        @process = nil
        @pid = nil
        @session = nil
      end

      private

      def start_process
        opts = { err: :pipe, in: :pipe, out: :pipe }
        opts[:chdir] = @config.cwd if @config.cwd
        @process = Open3.popen3(@config.child_env, *@config.server_command, **opts)
        @stdin, @stdout, @stderr, @wait_thread = @process
        @pid = @wait_thread.pid
        @session = nil
      rescue SystemCallError => e
        raise TransportError, "failed to start mem20 server " \
                              "(#{Array(@config.server_command).join(" ")}): #{e.message}"
      end

      # Every outgoing message carries the JSON-RPC 2.0 envelope. The mem20
      # server validates `jsonrpc` and silently ignores a request without it,
      # so it is added here rather than at each call site.
      def write_message(payload)
        @stdin.puts(JSON.generate({ "jsonrpc" => "2.0" }.merge(payload)))
        @stdin.flush
      rescue Errno::EPIPE, IOError => e
        raise TransportError, "mem20 server closed the stdio pipe: #{e.message} (#{stderr_tail})"
      end

      def read_response(id)
        deadline = monotonic + @config.timeout
        loop do
          remaining = deadline - monotonic
          raise TransportError, "timed out waiting for response to request ##{id}" if remaining <= 0

          line = nil
          Timeout.timeout(remaining) { line = @stdout.gets }
          raise TransportError, "mem20 server closed stdout (#{stderr_tail})" if line.nil?

          line = line.strip
          next if line.empty?

          message = parse_line(line)
          next if message["id"] != id # notification / unrelated reply

          return message["result"] if message.key?("result")

          error = message["error"] || {}
          raise ToolError.new(error["message"] || "mem20 tool call failed",
                              code: error["code"], data: error["data"])
        end
      end

      def parse_line(line)
        JSON.parse(line)
      rescue JSON::ParserError => e
        raise TransportError, "invalid JSON from mem20 server: #{e.message}"
      end

      def ensure_alive!
        return if @wait_thread&.alive?

        raise TransportError, "mem20 server process has exited (#{stderr_tail})"
      end

      def stderr_tail(limit: 2000)
        return "" unless @stderr

        begin
          @stderr_buffer << @stderr.read_nonblock(4096)
        rescue StandardError
          nil
        end
        tail = @stderr_buffer[-limit..] || @stderr_buffer
        tail.strip
      end

      def monotonic
        Process.clock_gettime(Process::CLOCK_MONOTONIC)
      end
    end
  end
end
