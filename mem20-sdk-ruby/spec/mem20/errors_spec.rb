# frozen_string_literal: true

require "spec_helper"

RSpec.describe "Mem20 error hierarchy" do
  it "roots every error at Mem20::Error" do
    expect(Mem20::ConfigurationError.ancestors).to include(Mem20::Error)
    expect(Mem20::ToolError.ancestors).to include(Mem20::Error)
    expect(Mem20::TransportError.ancestors).to include(Mem20::Error)
    expect(Mem20::Error.ancestors).to include(StandardError)
  end

  it "carries the JSON-RPC code and data on a ToolError" do
    error = Mem20::ToolError.new("boom", code: -32_602, data: { "tool" => "memory_store" })

    expect(error.message).to eq("boom")
    expect(error.code).to eq(-32_602)
    expect(error.data).to eq("tool" => "memory_store")
  end
end
