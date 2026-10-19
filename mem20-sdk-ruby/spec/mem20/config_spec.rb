# frozen_string_literal: true

require "spec_helper"

RSpec.describe Mem20::Config do
  it "applies the documented defaults" do
    config = described_class.new

    expect(config.llm_base_url).to eq("https://integrate.api.nvidia.com/v1")
    expect(config.health_port).to eq(8080)
    expect(config.health_host).to eq("127.0.0.1")
    expect(config.timeout).to eq(30.0)
    expect(config.server_command).to eq(["python3", "mcp/mcp_server.py"])
    expect(config.protocol_version).to eq("2025-06-18")
  end

  it "rejects unknown options" do
    expect { described_class.new(nope: 1) }.to raise_error(Mem20::ConfigurationError, /nope/)
  end

  it "rejects an out-of-range health port" do
    expect { described_class.new(health_port: 70_000) }.to raise_error(Mem20::ConfigurationError)
  end

  it "rejects an empty server command" do
    expect { described_class.new(server_command: []) }.to raise_error(Mem20::ConfigurationError)
  end

  it "is mutable while being configured, then frozen" do
    config = described_class.new
    expect(config).not_to be_frozen

    config.cwd = "/opt/mem20/mem20"
    expect(config.cwd).to eq("/opt/mem20/mem20")

    config.freeze!
    expect(config).to be_frozen
    expect { config.cwd = "/other" }.to raise_error(FrozenError)
  end

  it "builds through the block DSL and freezes the result" do
    config = described_class.build do |c|
      c.cwd = "/opt/mem20/mem20"
      c.timeout = 5.0
    end

    expect(config.cwd).to eq("/opt/mem20/mem20")
    expect(config.timeout).to eq(5.0)
    expect(config).to be_frozen
  end

  it "re-validates after each writer" do
    config = described_class.new

    expect { config.health_port = 70_000 }.to raise_error(Mem20::ConfigurationError)
    expect { config.server_command = [] }.to raise_error(Mem20::ConfigurationError)
    expect { config.timeout = 0 }.to raise_error(Mem20::ConfigurationError)
  end

  it "reads the documented environment variables" do
    env = {
      "MEM20_STORE_PATH" => "/opt/mem20/store",
      "MEM20_COG_PATH" => "/opt/mem20/cog",
      "MEM20_LLM_BASE_URL" => "http://localhost:11434/v1",
      "MEM20_LLM_MODEL" => "llama3",
      "MEM20_HEALTH_PORT" => "9090",
      "NVAPI_KEY" => "nvapi-test"
    }
    config = described_class.from_options_and_env({}, env)

    expect(config.store_path).to eq("/opt/mem20/store")
    expect(config.cog_path).to eq("/opt/mem20/cog")
    expect(config.llm_base_url).to eq("http://localhost:11434/v1")
    expect(config.llm_model).to eq("llama3")
    expect(config.health_port).to eq(9090)
    expect(config.llm_api_key).to eq("nvapi-test")
  end

  it "prefers the explicit option over the environment" do
    config = described_class.from_options_and_env({ store_path: "/explicit" },
                                                  "MEM20_STORE_PATH" => "/from-env")

    expect(config.store_path).to eq("/explicit")
  end

  it "builds a child environment for the server process" do
    config = described_class.new(store_path: "/tmp/store", llm_model: "gpt-4o")
    env = config.child_env

    expect(env["MEM20_STORE_PATH"]).to eq("/tmp/store")
    expect(env["MEM20_LLM_MODEL"]).to eq("gpt-4o")
  end

  it "exposes the health URL" do
    expect(described_class.new.health_url).to eq("http://127.0.0.1:8080")
  end
end
