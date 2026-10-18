# frozen_string_literal: true

module Mem20
  # Configuration object for a {Mem20::Client}.
  #
  # It is mutable while being set up - either through keyword options or the
  # block-style DSL in `Mem20.configure` - and is frozen once it is handed to a
  # client ({Mem20::Client} calls {#freeze!}), so a running client's config can
  # never change underneath it.
  #
  # Mirrors the environment variables documented for the mem20 server so a
  # single `.env` drives both halves:
  #
  #   MEM20_STORE_PATH   -> store_path
  #   MEM20_COG_PATH     -> cog_path
  #   MEM20_LLM_BASE_URL -> llm_base_url
  #   MEM20_LLM_MODEL    -> llm_model
  #   MEM20_LLM_API_KEY  -> llm_api_key (`NVAPI_KEY` / `NVIDIA_API_KEY` also honoured)
  #   MEM20_HEALTH_PORT  -> health_port
  class Config
    DEFAULTS = {
      server_command: ["python3", "mcp/mcp_server.py"],
      cwd: nil,
      store_path: nil,
      cog_path: nil,
      llm_base_url: "https://integrate.api.nvidia.com/v1",
      llm_model: nil,
      llm_api_key: nil,
      health_port: 8080,
      health_host: "127.0.0.1",
      protocol_version: Mem20::PROTOCOL_VERSION,
      timeout: 30.0,
      env: {}
    }.freeze

    # Attribute <-> environment variable pairs shared by `from_options_and_env`
    # and `#child_env`, so the two can never drift apart.
    ENV_MAP = {
      store_path: "MEM20_STORE_PATH",
      cog_path: "MEM20_COG_PATH",
      llm_base_url: "MEM20_LLM_BASE_URL",
      llm_model: "MEM20_LLM_MODEL",
      health_port: "MEM20_HEALTH_PORT"
    }.freeze

    # Any of these, in order, supplies the LLM bearer token.
    API_KEY_VARS = ["MEM20_LLM_API_KEY", "NVAPI_KEY", "NVIDIA_API_KEY"].freeze

    attr_reader(*DEFAULTS.keys)

    def initialize(**options)
      assert_known_keys!(options)
      values = normalize(DEFAULTS.merge(options))
      DEFAULTS.each_key { |key| instance_variable_set("@#{key}", values[key]) }
    end

    # Build a config, yield it for block-style setup, then freeze the result.
    #
    #   Mem20::Config.build { |c| c.cwd = "/opt/mem20/mem20" }
    def self.build(**options, &block)
      config = new(**options)
      block&.call(config)
      config.freeze!
    end

    # Build a config, filling missing values from the process environment.
    def self.from_env(**options)
      from_options_and_env(options, ENV)
    end

    # The testable form of {from_env}: takes the environment hash explicitly.
    def self.from_options_and_env(options, env)
      new(**env_values(env).merge(options))
    end

    # The documented `MEM20_*` values present in `env`, as config attributes.
    def self.env_values(env)
      values = ENV_MAP.each_with_object({}) do |(attribute, variable), acc|
        value = env[variable]
        acc[attribute] = value if value
      end
      port = env["MEM20_HEALTH_PORT"]
      values[:health_port] = port.to_i if port
      key = API_KEY_VARS.filter_map { |variable| env[variable] }.first
      values[:llm_api_key] = key if key
      values
    end

    # Freeze the configuration so nothing can mutate it under a running client.
    # `Mem20.configure` leaves the object unfrozen only while its setup block
    # runs and then freezes it; a {Mem20::Client} always freezes its config.
    def freeze!
      @server_command.freeze
      @env.freeze
      freeze
      self
    end

    # The current values as a Hash (used by the writers to re-validate the
    # whole configuration after each change).
    def to_h
      DEFAULTS.keys.to_h { |key| [key, public_send(key)] }
    end

    # Attribute writers for the block-style DSL. Each one re-validates the
    # resulting configuration and refuses to run once the object is frozen.
    DEFAULTS.each_key do |key|
      define_method("#{key}=") do |value|
        raise FrozenError, "can't modify frozen #{self.class}" if frozen?

        candidate = normalize(DEFAULTS.merge(to_h).merge(key => value))
        instance_variable_set("@#{key}", candidate[key])
      end
    end

    # Environment the child server process is launched with: the base env plus
    # the `MEM20_*` values this config carries.
    def child_env
      overrides = ENV_MAP.each_with_object({}) do |(attribute, variable), acc|
        value = public_send(attribute)
        acc[variable] = value.to_s unless value.nil?
      end
      env.merge(overrides)
    end

    def health_url
      "http://#{health_host}:#{health_port}"
    end

    private

    def assert_known_keys!(options)
      unknown = options.keys - DEFAULTS.keys
      return if unknown.empty?

      keys = unknown.join(", ")
      raise ConfigurationError, "unknown configuration option(s): #{keys}"
    end

    # Coerce the scalar attributes and refuse any invalid combination.
    def normalize(merged)
      values = merged.dup
      values[:env] = values[:env].dup
      values[:server_command] = Array(values[:server_command])
      values[:timeout] = Float(values[:timeout])
      values[:health_port] = Integer(values[:health_port])
      validate!(values)
      values
    end

    def validate!(config)
      validate_server_command!(config)
      validate_timeout!(config)
      validate_health_port!(config)
      validate_protocol_version!(config)
    end

    def validate_server_command!(config)
      return unless Array(config[:server_command]).empty?

      raise ConfigurationError, "server_command must not be empty"
    end

    def validate_timeout!(config)
      return if config[:timeout].positive?

      raise ConfigurationError, "timeout must be positive"
    end

    def validate_health_port!(config)
      return if (1..65_535).cover?(config[:health_port])

      raise ConfigurationError, "health_port out of range: #{config[:health_port]}"
    end

    def validate_protocol_version!(config)
      version = config[:protocol_version]
      return if version.is_a?(String) && !version.empty?

      raise ConfigurationError, "protocol_version must be a non-empty String"
    end
  end
end
