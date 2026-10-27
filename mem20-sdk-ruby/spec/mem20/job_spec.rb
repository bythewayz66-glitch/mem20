# frozen_string_literal: true

require "spec_helper"

# The job envelope is the one part of the mem20 surface where a long-running
# tool does NOT answer with a result: `tools/call` returns a job id and the
# value has to be collected afterwards. These specs pin that contract against
# the in-process RecordingTransport double, so they need neither Python nor a
# running server and stay green in a bare sandbox.
RSpec.describe "Mem20 background jobs" do
  subject(:client) { Mem20::Client.new(Mem20::Config.new) }

  let(:transport) { RecordingTransport.new(responses) }
  let(:job_id) { "9f2c41ab77de" }

  # The envelope shape the server sends from `_handle_call_tool` for a
  # LONG_RUNNING_TOOLS entry (mcp/server.py). Those are the 24 `cognitive_substrate`
  # class tools - `cog_*`, `tot_*`, `imagination_*`, `beam_search`, `react_reason`,
  # `least_to_most`, `theory_of_mind_*`, `self_model_reflect`,
  # `memory_auto_consolidate` - and every one of them is registered.
  let(:envelope_payload) do
    { "job_id" => job_id, "status" => "running", "tool" => "cog_reason",
      "poll" => "job_status", "wait" => "job_wait" }
  end
  let(:call_result) { text_result(envelope_payload) }

  let(:responses) { { "job_status" => text_result(snapshot("ok", result: "\"done\"")) } }

  before { client.transport = transport }

  # A `tools/call` result carrying `payload` as its text content, the way the
  # server wraps a tool's JSON answer.
  def text_result(payload)
    text = payload.is_a?(String) ? payload : JSON.generate(payload)
    { "content" => [{ "type" => "text", "text" => text }], "isError" => false }
  end

  # A `job_status` / `job_wait` answer.
  def snapshot(status, result: nil, error: nil)
    payload = { "job_id" => job_id, "status" => status, "tool" => "cog_reason",
                "result" => result, "error" => error }
    text_result(payload)
  end

  describe "#job_from" do
    it "reads the job id, status and follow-up tools out of a tools/call result" do
      job = client.job_from(call_result)

      expect(job).to be_a(Mem20::JobEnvelope)
      expect(job.job_id).to eq(job_id)
      expect(job.status).to eq("running")
      expect(job.tool).to eq("cog_reason")
      expect(job.poll_tool).to eq("job_status")
      expect(job.wait_tool).to eq("job_wait")
      expect(job).to be_running
      expect(job).not_to be_terminal
    end

    it "accepts a bare job id, so a known job can be resumed" do
      job = client.job_from(job_id)

      expect(job.job_id).to eq(job_id)
      expect(job.status).to eq("running")
      expect(job.poll_tool).to eq("job_status")
    end

    it "falls back to the documented tool names when the envelope omits them" do
      job = client.job_from(text_result("job_id" => job_id, "status" => "running"))

      expect(job.poll_tool).to eq("job_status")
      expect(job.wait_tool).to eq("job_wait")
    end

    it "raises EnvelopeError for a result that is not a job envelope" do
      plain = text_result("found: ruby-roundtrip-4711")

      expect { client.job_from(plain) }
        .to raise_error(Mem20::EnvelopeError, /not valid JSON/)
    end

    it "raises EnvelopeError for JSON that carries no job_id" do
      no_id = text_result("status" => "running", "tool" => "cog_reason")

      expect { client.job_from(no_id) }
        .to raise_error(Mem20::EnvelopeError, /no job_id/)
    end

    it "raises EnvelopeError for an unknown object type" do
      expect { client.job_from(42) }.to raise_error(Mem20::EnvelopeError, /Integer/)
    end
  end

  describe "#wait_for_job" do
    context "when the job is still running on the first poll" do
      let(:responses) do
        {
          "job_status" => [snapshot("running"), snapshot("running"),
                           text_result("job_id" => job_id, "status" => "ok",
                                       "tool" => "cog_reason", "result" => "{\"answer\":42}")]
        }
      end

      it "polls until the terminal state and decodes the value" do
        result = client.wait_for_job(client.job_from(call_result), interval: 0, timeout: 5)

        expect(result).to be_a(Mem20::JobResult)
        expect(result).to be_ok
        expect(result).to be_terminal
        expect(result).not_to be_timed_out
        expect(result.value).to eq("answer" => 42)
        expect(result.attempts).to eq(3)
      end

      it "polls job_status once per attempt, always for the same job id" do
        client.wait_for_job(call_result, interval: 0, timeout: 5)

        polls = transport.requests_for("job_status")
        expect(polls.length).to eq(3)
        expect(polls.map { |(_m, params)| params["arguments"]["job_id"] }.uniq).to eq([job_id])
        expect(transport.requests_for("job_wait")).to be_empty
      end
    end

    it "returns the plain text payload when the result is not JSON" do
      responses["job_status"] = snapshot("ok", result: "the sky is blue because of Rayleigh")

      result = client.wait_for_job(job_id, interval: 0, timeout: 5)

      expect(result.value).to eq("the sky is blue because of Rayleigh")
    end

    context "when the job never leaves the running state" do
      let(:responses) { { "job_status" => snapshot("running") } }

      it "bounds a hang by the poll count instead of spinning forever" do
        result = client.wait_for_job(call_result, interval: 0, max_attempts: 3, timeout: 60)

        expect(result).to be_running
        expect(result).to be_timed_out
        expect(result).not_to be_terminal
        expect(result.attempts).to eq(3)
        expect(transport.requests_for("job_status").length).to eq(3)
      end

      it "bounds a hang by the wait window and returns rather than raising" do
        started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        result = client.wait_for_job(call_result, timeout: 0.05, interval: 0.005)
        elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - started

        expect(result).to be_running
        expect(result).to be_timed_out
        expect(elapsed).to be < 2.0
        expect(transport.requests_for("job_status").length).to be >= 2
      end

      it "stops on the deadline even with no attempt cap" do
        result = client.wait_for_job(job_id, timeout: 0.01, interval: 60)

        expect(result).to be_timed_out
      end
    end

    context "when the server rejected the job" do
      let(:responses) do
        { "job_status" => text_result("job_id" => job_id, "status" => "error",
                                      "tool" => "cog_reason", "result" => nil,
                                      "error" => "job timed out after 1800.0s in tool cog_reason") }
      end

      it "raises JobError instead of returning nil" do
        expect { client.wait_for_job(call_result, interval: 0, timeout: 5) }
          .to raise_error(Mem20::JobError) { |error|
            expect(error.job_id).to eq(job_id)
            expect(error.status).to eq("error")
            expect(error.message).to include("1800.0s")
            expect(error).to be_a(Mem20::Error)
          }
      end
    end

    context "when the job id is unknown to the server" do
      let(:responses) do
        { "job_status" => text_result("job_id" => job_id, "status" => "not_found") }
      end

      it "raises JobError, treating not_found as a terminal rejection" do
        expect { client.wait_for_job(call_result, interval: 0, timeout: 5) }
          .to raise_error(Mem20::JobError, /unknown to the server/)
      end

      it "fails on the first poll rather than retrying" do
        expect { client.wait_for_job(call_result, interval: 0, timeout: 5) }
          .to raise_error(Mem20::JobError)

        expect(transport.requests_for("job_status").length).to eq(1)
      end
    end

    context "when the tool call itself failed" do
      let(:responses) do
        { "job_status" => { "content" => [{ "type" => "text", "text" => "Error: unknown tool" }],
                            "isError" => true } }
      end

      it "raises JobError carrying the server's message" do
        expect { client.wait_for_job(call_result, interval: 0, timeout: 5) }
          .to raise_error(Mem20::JobError, /unknown tool/)
      end
    end

    context "when the snapshot is malformed" do
      let(:responses) { { "job_status" => text_result("not-json-at-all") } }

      it "raises EnvelopeError rather than guessing a status" do
        expect { client.wait_for_job(call_result, interval: 0, timeout: 5) }
          .to raise_error(Mem20::EnvelopeError)
      end
    end

    it "does not poll a job whose envelope already reached a terminal state" do
      finished = text_result(envelope_payload.merge("status" => "ok"))

      result = client.wait_for_job(finished, interval: 0, timeout: 5)

      expect(result).to be_ok
      # The envelope itself carries no tool result, and nothing is polled.
      expect(result.value).to be_nil
      expect(result.attempts).to eq(0)
      expect(transport.requests_for("job_status")).to be_empty
    end
  end

  describe "#job_status" do
    it "makes exactly one poll and returns the observation" do
      responses["job_status"] = snapshot("running")

      result = client.job_status(call_result)

      expect(result).to be_running
      expect(result).not_to be_terminal
      expect(result.attempts).to eq(1)
      expect(transport.requests_for("job_status").length).to eq(1)
    end

    it "raises JobError when the poll reports a rejection" do
      responses["job_status"] = text_result("job_id" => job_id, "status" => "error",
                                            "error" => "boom")

      expect { client.job_status(call_result) }.to raise_error(Mem20::JobError, /boom/)
    end
  end

  describe "#job_wait" do
    let(:responses) { { "job_wait" => snapshot("ok", result: "\"waited\"") } }

    it "uses the server-side wait tool with the requested timeout" do
      result = client.job_wait(call_result, timeout_ms: 2500)

      expect(result.value).to eq("waited")
      calls = transport.requests_for("job_wait")
      expect(calls.length).to eq(1)
      expect(calls.first.last["arguments"]).to eq("job_id" => job_id, "timeout_ms" => 2500)
      expect(transport.requests_for("job_status")).to be_empty
    end

    it "defaults to the server's own 30s wait window" do
      client.job_wait(call_result)

      expect(transport.requests_for("job_wait").first.last["arguments"]["timeout_ms"]).to eq(30_000)
    end
  end

  describe Mem20::JobEnvelope do
    it "reports a rejected status as rejected and terminal" do
      job = described_class.new(job_id: job_id, status: "error")

      expect(job).to be_rejected
      expect(job).to be_terminal
      expect(job).not_to be_running
    end

    it "keeps the raw payload for callers that need the full envelope" do
      job = client.job_from(call_result)

      expect(job.payload).to eq(envelope_payload)
    end
  end

  describe "the error hierarchy" do
    it "roots the job errors at Mem20::Error" do
      expect(Mem20::JobError.ancestors).to include(Mem20::Error)
      expect(Mem20::EnvelopeError.ancestors).to include(Mem20::Error)
      expect(Mem20::JobError.ancestors).to include(StandardError)
    end
  end
end
