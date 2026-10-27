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

  # Raised when a background job did not produce a result: the server reported
  # `error`, timed the job out, or no longer knows the job id (`not_found`).
  #
  # A rejected job raises rather than returning `nil`, so a non-nil return from
  # `Client#wait_for_job` always means a real answer.
  class JobError < Error
    attr_reader :job_id, :status

    def initialize(message, job_id: nil, status: nil)
      super(message)
      @job_id = job_id
      @status = status
    end
  end

  # Raised when a response cannot be read as a job envelope: the payload is not
  # JSON, or it is JSON without a `job_id` / `status`.
  class EnvelopeError < Error; end

  # Raised when the transport cannot reach (or died before answering) the server.
  class TransportError < Error; end
end
