# frozen_string_literal: true

require_relative "../lib/mem20"

RSpec.configure do |config|
  config.expect_with(:rspec) { |c| c.syntax = :expect }
  config.disable_monkey_patching!
  config.order = :random
  Kernel.srand config.seed
end

# An in-process transport double that never spawns a child process. It records
# every request the client sent and answers from a fixed result table, so the
# client specs can run without a Python interpreter or a mem20 checkout.
# The transport specs use a real child process instead.
class RecordingTransport
  attr_reader :requests

  def initialize(results = {})
    @results = results
    @requests = []
  end

  def initialize_session
    { "protocolVersion" => Mem20::PROTOCOL_VERSION }
  end

  def request(method, params = {})
    @requests << [method, params]
    if method == "tools/call"
      @results.fetch(params["name"], { "content" => [], "isError" => false })
    else
      { "tools" => [] }
    end
  end

  def close; end
end
