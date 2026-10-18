# frozen_string_literal: true

module Mem20
  # Base class for every error raised by the SDK.
  class Error < StandardError; end

  # Raised when the SDK is misconfigured (bad options, invalid values, ...).
  class ConfigurationError < Error; end

  # Raised when a tool call fails on the server side (JSON-RPC error object).
  # The server signals tool-level failures through this object; the SDK turns
  # it into a Ruby exception carrying the numeric code and any structured data.
  class ToolError < Error
    attr_reader :code, :data

    def initialize(message, code: nil, data: nil)
      super(message)
      @code = code
      @data = data
    end
  end

  # Raised when the transport cannot reach (or died before answering) the server.
  class TransportError < Error; end
end
