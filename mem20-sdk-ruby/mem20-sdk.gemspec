# frozen_string_literal: true

require_relative "lib/mem20/version"

Gem::Specification.new do |spec|
  spec.name          = "mem20-sdk"
  spec.version       = Mem20::VERSION
  spec.authors       = ["bythewayz66"]
  spec.email         = ["bythewayz66@users.noreply.github.com"]

  spec.summary       = "Ruby SDK for mem20 - persistent memory + cognition " \
                       "substrate for AI agents."
  spec.description   = "Idiomatic Ruby client for the mem20 MCP server " \
                       "(JSON-RPC 2.0 over stdio, protocol 2025-06-18). " \
                       "Provides a typed, thread-safe facade over the " \
                       "270-tool mem20 surface (27 domains)."
  spec.homepage      = "https://github.com/bythewayz66-glitch/mem20"
  spec.license       = "MIT"
  spec.required_ruby_version = ">= 3.1.0"

  spec.metadata["homepage_uri"]      = spec.homepage
  spec.metadata["source_code_uri"]   = "#{spec.homepage}/tree/main/mem20-sdk-ruby"
  spec.metadata["changelog_uri"]     = "#{spec.homepage}/blob/main/mem20-sdk-ruby/CHANGELOG.md"
  spec.metadata["documentation_uri"] = "#{spec.homepage}/tree/main/mem20-sdk-ruby/docs"
  spec.metadata["rubygems_mfa_required"] = "true"

  spec.files = Dir[
    "lib/**/*.rb",
    "docs/**/*.md",
    "examples/**/*.rb",
    "README.md",
    "CHANGELOG.md",
    "LICENSE"
  ]
  spec.require_paths = ["lib"]
  # Development dependencies live in the Gemfile (see Gemspec/DevelopmentDependencies).
end
