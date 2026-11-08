# frozen_string_literal: true

require_relative "lib/mem20/version"

Gem::Specification.new do |spec|
  spec.name          = "mem20-sdk"
  spec.version       = Mem20::VERSION
  spec.authors       = ["mem20"]
  spec.email         = ["mem20@users.noreply.github.com"]

  spec.summary       = "Ruby client for the mem20 MCP server"
  spec.description   = "Native Ruby client for mem20: JSON-RPC 2.0 over stdio, " \
                       "MCP handshake, tool discovery and invocation over the " \
                       "311-tool mem20 surface (39 domains)."
  spec.homepage      = "https://github.com/bythewayz66-glitch/mem20"
  spec.license       = "MIT"
  spec.required_ruby_version = ">= 3.0"

  spec.metadata["homepage_uri"]    = spec.homepage
  spec.metadata["source_code_uri"] = spec.homepage
  spec.metadata["changelog_uri"]   = "#{spec.homepage}/blob/main/mem20-sdk-ruby/CHANGELOG.md"

  spec.files = Dir[
    "lib/**/*.rb",
    "docs/**/*.md",
    "examples/**/*.rb",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
  ]
  spec.require_paths = ["lib"]

  # No runtime dependencies: the gem speaks JSON-RPC over a pipe with the
  # standard library only. `rspec` and `rubocop` are development dependencies
  # and are declared in the Gemfile, not here, so installing the gem never
  # pulls a test framework into a production bundle.
end
