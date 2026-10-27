# frozen_string_literal: true

require_relative "mem20/version"
require_relative "mem20/errors"
require_relative "mem20/config"
require_relative "mem20/transport/stdio"
require_relative "mem20/job"
require_relative "mem20/client"

# mem20 - Ruby SDK.
#
# A persistent memory + cognition substrate for AI agents. This gem is an
# idiomatic Ruby client for the mem20 MCP server (JSON-RPC 2.0 over stdio,
# MCP protocol revision 2025-06-18).
#
#   require "mem20"
#
#   Mem20.configure { |c| c.cwd = "/opt/mem20/mem20" }
#
#   Mem20.client.memory_store(content: "hello", category: "general")
module Mem20
  class << self
    # The active configuration (defaults, then any block overrides).
    def configuration
      @configuration ||= Config.from_env
    end

    # Configure the SDK. Called with a block for a Rails-style DSL, or with
    # keyword options.
    #
    #   Mem20.configure { |c| c.cwd = "/opt/mem20/mem20" }
    #   Mem20.configure(health_port: 9090)
    #
    # The block form mutates the config being built; the returned config is
    # frozen. Any previously memoised client is dropped.
    def configure(**options, &block)
      @configuration = Config.build(**options, &block)
      @client = nil
      @configuration
    end

    def reset_configuration!
      @configuration = nil
      @client = nil
    end

    # A memoised client over the current configuration.
    def client
      @client ||= Client.new(configuration)
    end

    def reset_client!
      @client&.close
      @client = nil
    end
  end
end
