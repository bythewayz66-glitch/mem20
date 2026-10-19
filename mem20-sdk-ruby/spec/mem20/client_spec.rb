# frozen_string_literal: true

require "spec_helper"

RSpec.describe Mem20::Client do
  subject(:client) { described_class.new(Mem20::Config.new) }

  let(:transport) { RecordingTransport.new("memory_recall" => recall_result) }
  let(:recall_result) do
    { "content" => [{ "type" => "text", "text" => "found: ruby-roundtrip-4711" }] }
  end

  before { client.instance_variable_set(:@transport, transport) }

  it "calls a mem20 tool through tools/call" do
    client.tool("memory_store", content: "hello", category: "general")

    method, params = transport.requests.last
    expect(method).to eq("tools/call")
    expect(params["name"]).to eq("memory_store")
    expect(params["arguments"]).to eq("content" => "hello", "category" => "general")
  end

  it "stringifies symbol argument keys" do
    client.tool(:memory_recall, query: "hello")

    _method, params = transport.requests.last
    expect(params["name"]).to eq("memory_recall")
    expect(params["arguments"].keys).to eq(["query"])
  end

  it "lists tools through the client" do
    expect(client.tools).to eq("tools" => [])
  end

  it "joins an Array of tags into the comma-separated form the server expects" do
    client.memory_store(content: "sky", category: "general", tags: ["weather", "colour"])

    _method, params = transport.requests.last
    expect(params["arguments"]["tags"]).to eq("weather,colour")
  end

  it "omits tags when none are supplied" do
    client.memory_store(content: "sky")

    _method, params = transport.requests.last
    expect(params["arguments"]).to eq("content" => "sky", "category" => "general")
  end

  it "passes category and limit through memory_recall" do
    client.memory_recall(query: "sky", category: "project", limit: 5)

    _method, params = transport.requests.last
    expect(params["arguments"]).to eq("query" => "sky", "category" => "project", "limit" => 5)
  end

  it "extracts the plain-text payload from a result envelope" do
    expect(client.text(recall_result)).to eq("found: ruby-roundtrip-4711")
  end

  it "exposes the frozen configuration" do
    expect(client.config).to be_frozen
    expect(client.config).to be_a(Mem20::Config)
  end
end
