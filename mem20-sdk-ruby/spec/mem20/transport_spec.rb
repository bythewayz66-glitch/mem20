# frozen_string_literal: true

require "spec_helper"
require "rbconfig"

# These specs spawn a real child process and speak real JSON-RPC 2.0 over its
# stdio pipes, so they exercise the framing, the handshake and the error path
# end to end rather than through an in-process double.
RSpec.describe Mem20::Transport::Stdio do
  let(:server) { File.expand_path("../support/mini_mcp_server.rb", __dir__) }
  let(:config) do
    Mem20::Config.new(server_command: [RbConfig.ruby, server], timeout: 15.0)
  end

  it "completes the MCP handshake and reports the negotiated protocol" do
    transport = described_class.new(config)
    session = transport.initialize_session

    expect(session.protocol_version).to eq("2025-06-18")
    expect(session.server_info["name"]).to eq("mini-mem20")
  ensure
    transport&.close
  end

  it "round-trips a tool call and returns the known value" do
    transport = described_class.new(config)
    transport.initialize_session
    result = transport.request("tools/call",
                               "name" => "echo",
                               "arguments" => { "token" => "ruby-roundtrip-4711" })

    expect(result.dig("content", 0, "text")).to eq("echo:ruby-roundtrip-4711")
  ensure
    transport&.close
  end

  it "raises ToolError carrying the JSON-RPC code for an error reply" do
    transport = described_class.new(config)
    transport.initialize_session

    expect do
      transport.request("tools/call", "name" => "fail", "arguments" => {})
    end.to raise_error(Mem20::ToolError) { |e| expect(e.code).to eq(-32_602) }
  ensure
    transport&.close
  end

  it "skips notifications while awaiting a response" do
    transport = described_class.new(config)
    transport.notify("notifications/initialized", {})
    transport.initialize_session
    result = transport.request("tools/list")

    expect(result["tools"].map { |t| t["name"] }).to eq(["echo", "fail"])
  ensure
    transport&.close
  end

  it "reports the child process id and reaps it on close" do
    transport = described_class.new(config)
    pid = transport.pid

    expect(pid).to be_an(Integer)
    expect(Process.kill(0, pid)).to eq(1)
    transport.close
    expect { Process.kill(0, pid) }.to raise_error(Errno::ESRCH)
  end
end
