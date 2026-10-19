# frozen_string_literal: true

# Drop-in Rails initializer for the mem20 Ruby SDK.
# Copy to config/initializers/mem20.rb.
#
#   MEM20_CWD        directory holding mcp/mcp_server.py (default /opt/mem20/mem20)
#   MEM20_STORE_PATH memory store directory
#   MEM20_LLM_BASE_URL / MEM20_LLM_MODEL / MEM20_LLM_API_KEY  as documented
require "mem20"

Mem20.configure do |c|
  c.cwd = ENV.fetch("MEM20_CWD", "/opt/mem20/mem20")
  c.store_path = ENV["MEM20_STORE_PATH"]
  c.timeout = Float(ENV.fetch("MEM20_TIMEOUT", "60.0"))
end

# Reap the child process when the process exits (Puma, Sidekiq, rake tasks).
at_exit { Mem20.reset_client! }
