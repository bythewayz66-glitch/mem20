# frozen_string_literal: true

require "json"

module Mem20
  # Background-job support.
  #
  # The mem20 server runs a fixed set of long tools (`cog_*`, `tot_*`,
  # `imagination_*`, `beam_search`, `react_reason`, ...) as background jobs: the
  # `tools/call` request answers at once with a *job envelope* instead of a
  # result, and the value has to be collected afterwards through `job_status`
  # (one poll) or `job_wait` (server-side block).
  #
  # {JobEnvelope} models that envelope, {JobResult} is one observation of a job,
  # {WaitWindow} bounds the polling loop, and {Job.wait} runs it.
  module Job
    # Matches the server's own `MEM20_JOB_TIMEOUT` default, so a client wait does
    # not give up before the server-side job does. A wait is always bounded:
    # running out of time returns the still-running job rather than blocking
    # forever or raising.
    DEFAULT_WAIT_TIMEOUT = 1800.0

    # Seconds between two `job_status` polls.
    DEFAULT_POLL_INTERVAL = 0.5

    # States a job never leaves. `not_found` counts as terminal: the server has
    # no record of that id and will not produce one later.
    TERMINAL_STATUSES = ["ok", "error", "not_found"].freeze

    # States that mean the job did not produce a result.
    REJECTED_STATUSES = ["error", "not_found"].freeze

    # Bounds one {Job.wait}: the wall-clock window, the pause between polls and
    # an optional cap on the number of polls. A cap is what bounds a *hung* job
    # - one that answers every poll instantly with `running` and would therefore
    # never hit the deadline on its own.
    #
    # `sleeper` is the pause itself (a `#call(delay)`), injected so the polling
    # behaviour is testable without real delays.
    WaitWindow = Struct.new(:timeout, :interval, :max_attempts, :sleeper, keyword_init: true) do
      def self.build(timeout: DEFAULT_WAIT_TIMEOUT, interval: DEFAULT_POLL_INTERVAL,
                     max_attempts: nil, sleeper: nil)
        new(timeout: timeout, interval: interval, max_attempts: max_attempts, sleeper: sleeper)
      end

      def deadline
        timeout.nil? ? nil : Job.monotonic + timeout.to_f
      end

      def pause_seconds(deadline)
        return interval.to_f if deadline.nil?

        [interval.to_f, deadline - Job.monotonic].min
      end
    end

    # Wrap a job envelope, a `tools/call` result or a bare job id.
    #
    #   Job.envelope(call_result)   # -> JobEnvelope
    #   Job.envelope("9f2c41ab77de") # -> JobEnvelope (resume a known job)
    def self.envelope(object)
      JobEnvelope.from(object)
    end

    # One non-blocking poll. Raises {JobError} if the job was rejected.
    def self.status(client, job)
      envelope = JobEnvelope.from(job)
      JobResult.from_snapshot(fetch(client, envelope), attempts: 1)
    end

    # Poll `job` until it reaches a terminal state, or until the {WaitWindow}
    # closes. Returns a {JobResult}: `#ok?` with the decoded `#value` when the
    # job finished, `#timed_out?` and still `running` when the window closed
    # first. A job the server rejected (`error` / `not_found`) raises
    # {JobError}, so a returned result is never a silently ignored nil.
    def self.wait(client, job, window = WaitWindow.build)
      envelope = JobEnvelope.from(job)
      return JobResult.from_snapshot(envelope.to_h) if envelope.terminal?

      poll(client, envelope, window)
    end

    # One `job_status` call, normalised to a snapshot Hash.
    def self.fetch(client, envelope)
      JobResult.snapshot(client.tool(envelope.poll_tool, job_id: envelope.job_id))
    end

    # The polling loop behind {Job.wait}.
    def self.poll(client, envelope, window)
      attempts, snapshot = poll_until_terminal(client, envelope, window)
      JobResult.from_snapshot(snapshot, attempts: attempts,
                                        timed_out: !JobResult.terminal_status?(snapshot["status"]))
    end

    # Poll until the job is terminal, the attempt cap is hit or the deadline
    # passes; returns the poll count and the last observation.
    def self.poll_until_terminal(client, envelope, window)
      deadline = window.deadline
      snapshot = nil
      attempts = 0
      loop do
        attempts += 1
        snapshot = fetch(client, envelope)
        return [attempts, snapshot] if stop_after?(snapshot, attempts, window, deadline)

        pause(window.pause_seconds(deadline), window.sleeper)
      end
    end

    def self.stop_after?(snapshot, attempts, window, deadline)
      JobResult.terminal_status?(snapshot["status"]) ||
        exhausted?(attempts, window.max_attempts, deadline)
    end

    def self.exhausted?(attempts, max_attempts, deadline)
      (max_attempts && attempts >= max_attempts) || (deadline && monotonic >= deadline)
    end

    # Sleep, but never past the deadline.
    def self.pause(delay, sleeper)
      return if delay <= 0

      sleeper ? sleeper.call(delay) : Kernel.sleep(delay)
    end

    def self.monotonic
      Process.clock_gettime(Process::CLOCK_MONOTONIC)
    end

    private_class_method :poll, :poll_until_terminal, :stop_after?, :exhausted?, :pause
  end

  # The envelope a long-running mem20 tool returns instead of a result:
  #
  #   { "job_id" => "9f2c...", "status" => "running", "tool" => "cog_reason",
  #     "poll" => "job_status", "wait" => "job_wait" }
  #
  # The server wraps it in the usual MCP `content` envelope, so
  # {JobEnvelope.from} accepts the whole `tools/call` result.
  class JobEnvelope
    DEFAULT_POLL_TOOL = "job_status"
    DEFAULT_WAIT_TOOL = "job_wait"

    attr_reader :job_id, :status, :tool, :poll_tool, :wait_tool, :payload

    # Accept a {JobEnvelope}, a `tools/call` result Hash, or a bare job id.
    def self.from(object)
      case object
      when JobEnvelope then object
      when String then new(job_id: object)
      when Hash then from_result(object)
      else raise EnvelopeError, "expected a Mem20::JobEnvelope, a tools/call result Hash " \
                                "or a job_id String, got #{object.class}"
      end
    end

    # Parse the `tools/call` result of a long-running tool.
    def self.from_result(result)
      text = Client.text(result)
      raise JobError.new(text, status: "error") if result["isError"]

      payload = parse_payload(text)
      job_id = payload["job_id"]
      if job_id.nil? || job_id.to_s.empty?
        raise EnvelopeError, "tools/call result is not a job envelope (no job_id): #{text[0, 200]}"
      end

      new(job_id: job_id, status: payload.fetch("status", "running"), tool: payload["tool"],
          payload: payload)
    end

    def self.parse_payload(text)
      payload = JSON.parse(text)
      unless payload.is_a?(Hash)
        raise EnvelopeError, "job payload must be a JSON object, got #{payload.class}"
      end

      payload
    rescue JSON::ParserError
      raise EnvelopeError, "job payload is not valid JSON: #{text[0, 200].inspect}"
    end

    def initialize(job_id:, status: "running", tool: nil, payload: {})
      @payload = payload
      @job_id = job_id.to_s
      @status = status.to_s
      @tool = tool
      @poll_tool = payload.fetch("poll", DEFAULT_POLL_TOOL)
      @wait_tool = payload.fetch("wait", DEFAULT_WAIT_TOOL)
    end

    def running? = status == "running"

    def ok? = status == "ok"

    # A job the server gave up on: `error`, or an id it no longer knows.
    def rejected? = Job::REJECTED_STATUSES.include?(status)

    def terminal? = Job::TERMINAL_STATUSES.include?(status)

    def to_h
      { "job_id" => job_id, "status" => status, "tool" => tool }
    end

    def inspect
      "#<#{self.class.name} job_id=#{job_id.inspect} status=#{status.inspect} tool=#{tool.inspect}>"
    end
  end

  # One observation of a background job.
  #
  # Returned for a job that finished successfully, or one that is still running
  # when the observation window closed ({#timed_out?}). A job the server
  # rejected raises {JobError} instead of returning a result, so a
  # `wait_for_job` return value is always meaningful and can never be `nil`.
  class JobResult
    attr_reader :job_id, :status, :tool, :value, :error, :attempts

    def self.terminal_status?(status)
      Job::TERMINAL_STATUSES.include?(status.to_s)
    end

    # Parse a `job_status` / `job_wait` `tools/call` result into a snapshot Hash.
    def self.snapshot(result)
      text = Client.text(result)
      raise JobError.new(text, status: "error") if result["isError"]

      payload = JobEnvelope.parse_payload(text)
      return payload unless payload["status"].nil?

      raise EnvelopeError, "job snapshot has no status: #{text[0, 200].inspect}"
    end

    # Build the result, raising for a rejected job.
    def self.from_snapshot(snapshot, attempts: 0, timed_out: false)
      status = snapshot["status"].to_s
      if Job::REJECTED_STATUSES.include?(status)
        raise JobError.new(rejection_message(snapshot, status),
                           job_id: snapshot["job_id"], status: status)
      end

      new(snapshot, attempts: attempts, timed_out: timed_out)
    end

    def self.rejection_message(snapshot, status)
      job_id = snapshot["job_id"]
      detail = snapshot["error"] || "no error detail reported"
      return "job #{job_id} failed: #{detail}" unless status == "not_found"

      "job #{job_id} is unknown to the server (not_found; it may have expired)"
    end

    # Tool payloads arrive as strings; decode them when they are JSON and keep
    # the raw string otherwise (plenty of mem20 tools return plain prose).
    def self.decode(value)
      return value unless value.is_a?(String)

      JSON.parse(value)
    rescue JSON::ParserError
      value
    end

    def initialize(snapshot, attempts: 0, timed_out: false)
      @job_id = snapshot["job_id"]
      @status = snapshot["status"].to_s
      @tool = snapshot["tool"]
      @value = self.class.decode(snapshot["result"])
      @error = snapshot["error"]
      @attempts = attempts
      @timed_out = timed_out
    end

    def ok? = status == "ok"

    def running? = status == "running"

    def terminal? = JobResult.terminal_status?(status)

    def timed_out? = @timed_out

    def to_h
      { "job_id" => job_id, "status" => status, "tool" => tool, "value" => value,
        "error" => error, "attempts" => attempts, "timed_out" => timed_out? }
    end

    def inspect
      "#<#{self.class.name} job_id=#{job_id.inspect} status=#{status.inspect} " \
        "attempts=#{attempts} timed_out=#{timed_out?}>"
    end
  end
end
