# frozen_string_literal: true

module Mem20
  # The SDK's own release.
  VERSION = "0.2.0"

  # The mem20 server release this SDK was built and tested against.
  #
  # This is NOT the SDK version. The two version independently: a 0.2.0 gem
  # talking to a 3.1.2 server is the supported arrangement. Prefer
  # `client.server_info` when you need to know what you are really talking to;
  # this constant is the baseline the gem was verified against.
  SERVER_VERSION = "3.1.2"
end
