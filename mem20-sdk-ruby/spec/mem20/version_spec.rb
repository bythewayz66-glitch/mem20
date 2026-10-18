# frozen_string_literal: true

require "spec_helper"

RSpec.describe "Mem20 version constants" do
  it "declares the SDK version" do
    expect(Mem20::VERSION).to eq("0.2.0")
  end

  it "declares the mem20 server release this SDK was validated against" do
    expect(Mem20::SERVER_VERSION).to eq("2.1.0rc2")
  end

  it "declares the MCP protocol revision sent in the handshake" do
    expect(Mem20::PROTOCOL_VERSION).to eq("2025-06-18")
  end
end
