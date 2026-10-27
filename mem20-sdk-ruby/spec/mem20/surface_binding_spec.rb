# frozen_string_literal: true

# Covers the two documented call shapes for `Client#tool` and the contract that
# the SDK can reach the *whole* surface, not just the memory convenience
# accessors.
RSpec.describe Mem20::Client do
  subject(:client) { described_class.new(Mem20::Config.new) }

  let(:transport) { RecordingTransport.new }
  let(:tool_list) { ["memory_status", "memory_probe", "lie_status", "job_wait"] }

  before do
    allow(client).to receive(:transport).and_return(transport)
    allow(transport).to receive(:request).and_wrap_original do |original, method, params = {}|
      if method == "tools/list"
        { "tools" => tool_list.map { |n| { "name" => n } } }
      else
        original.call(method, params)
      end
    end
  end

  def sent_arguments
    transport.requests.last.last["arguments"]
  end

  describe "#tool argument shapes" do
    # Ruby 3.x stopped converting a trailing Hash into keywords, so
    # `tool("memory_status", {})` raised ArgumentError while every document
    # showed exactly that call.
    it "accepts an empty positional Hash, as the README and docs show" do
      expect { client.tool("memory_status", {}) }.not_to raise_error
      expect(sent_arguments).to eq({})
    end

    it "accepts a positional Hash of String keys" do
      client.tool("memory_recall", { "query" => "sky", "limit" => 5 })
      expect(sent_arguments).to eq("query" => "sky", "limit" => 5)
    end

    it "accepts a positional Hash of Symbol keys and stringifies them" do
      client.tool("memory_recall", { query: "sky" })
      expect(sent_arguments).to eq("query" => "sky")
    end

    it "accepts keyword arguments" do
      client.tool("memory_recall", query: "sky", limit: 5)
      expect(sent_arguments).to eq("query" => "sky", "limit" => 5)
    end

    it "accepts a tool with no arguments at all" do
      client.tool("memory_status")
      expect(sent_arguments).to eq({})
    end

    it "lets explicit keywords win over the positional Hash" do
      client.tool("memory_recall", { "query" => "old" }, query: "new")
      expect(sent_arguments).to eq("query" => "new")
    end

    it "rejects a non-Hash second argument with a clear message" do
      expect { client.tool("memory_recall", "sky") }
        .to raise_error(ArgumentError, /arguments must be a Hash, got String/)
    end
  end

  describe "dynamic bindings" do
    it "resolves any registered tool as a method, including non-memory domains" do
      expect(client).to respond_to(:lie_status)
      expect(client).to respond_to(:job_wait)
      expect(client).not_to respond_to(:definitely_not_a_tool)
    end

    it "includes the infra job tools in the tool list it binds against" do
      expect(client.tool_names).to include("job_wait", "lie_status")
    end
  end
end
