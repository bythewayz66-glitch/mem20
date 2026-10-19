# frozen_string_literal: true

module Mem20
  # SDK version. Tracked independently of the mem20 server version.
  VERSION = "0.2.0"

  # The mem20 server release this SDK was validated against on Sidney.
  SERVER_VERSION = "2.1.0rc2"

  # The MCP protocol revision the SDK sends in the `initialize` handshake.
  PROTOCOL_VERSION = "2025-06-18"
end
