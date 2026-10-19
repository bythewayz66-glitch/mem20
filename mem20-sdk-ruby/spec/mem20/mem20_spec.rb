# frozen_string_literal: true

require "spec_helper"

RSpec.describe Mem20 do
  after { described_class.reset_configuration! }

  it "builds a frozen configuration from a block" do
    config = described_class.configure do |c|
      c.cwd = "/opt/mem20/mem20"
      c.timeout = 5.0
    end

    expect(config.cwd).to eq("/opt/mem20/mem20")
    expect(config.timeout).to eq(5.0)
    expect(config).to be_frozen
    expect(described_class.configuration).to equal(config)
  end

  it "accepts keyword options" do
    config = described_class.configure(health_port: 9090)

    expect(config.health_port).to eq(9090)
  end

  it "drops the memoised client when reconfigured" do
    described_class.client
    expect(described_class.instance_variable_get(:@client)).not_to be_nil

    described_class.configure { |c| c.cwd = "/opt/mem20/mem20" }
    expect(described_class.instance_variable_get(:@client)).to be_nil
  end

  it "resets configuration and client" do
    described_class.configure { |c| c.timeout = 5.0 }
    described_class.reset_configuration!

    expect(described_class.instance_variable_get(:@configuration)).to be_nil
  end
end
