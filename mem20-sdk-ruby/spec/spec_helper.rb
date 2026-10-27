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
#
# A table entry is either a single result or an Array of results returned in
# order, which is how the job specs script a job moving running -> ok across
# successive polls. The last entry of an Array repeats, so an endless
# "still running" job needs only one element.
class RecordingTransport
  DEFAULT_RESULT = { "content" => [], "isError" => false }.freeze

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
    return { "tools" => [] } unless method == "tools/call"

    resolve(@results.fetch(params["name"], DEFAULT_RESULT))
  end

  # Every recorded request for one tool name.
  def requests_for(name)
    @requests.select { |(_method, params)| params["name"] == name }
  end

  def close; end

  private

  def resolve(value)
    return value unless value.is_a?(Array)
    return value.first if value.length <= 1

    value.shift
  end
end
