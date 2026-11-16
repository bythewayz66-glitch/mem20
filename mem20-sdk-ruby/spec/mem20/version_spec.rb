# frozen_string_literal: true

require "spec_helper"

RSpec.describe "Mem20 version constants" do
  it "declares the SDK version" do
    expect(Mem20::VERSION).to eq("0.3.0")
  end

  it "declares the mem20 server release this SDK was validated against" do
    # The repository's VERSION file is 4.0.0 at the commit this gem targets;
    # the SDK version and the server version move independently.
    expect(Mem20::SERVER_VERSION).to eq("4.0.0")
  end

  it "declares the MCP protocol revision sent in the handshake" do
    expect(Mem20::PROTOCOL_VERSION).to eq("2025-06-18")
  end

  it "keeps the three versions distinct so a reader cannot conflate them" do
    expect(Mem20::VERSION).not_to eq(Mem20::SERVER_VERSION)
  end
end
