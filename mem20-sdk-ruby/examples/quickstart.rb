#!/usr/bin/env ruby
# frozen_string_literal: true

# End-to-end quickstart against a real mem20 server.
#
#   MEM20_CWD=/opt/mem20/mem20 ruby -Ilib examples/quickstart.rb
#
# It performs the MCP handshake, stores a fact, recalls it by a distinctive
# token, and reports whether the token came back — the same store→recall
# round-trip used for the SDK's own verification.

require "mem20"

cwd = ENV.fetch("MEM20_CWD", "/opt/mem20/mem20")

Mem20.configure do |c|
  c.cwd = cwd
  c.timeout = 60.0
end

client = Mem20.client
session = client.transport.initialize_session

server_name = session.server_info["name"]
reported_version = session.server_info["version"].inspect

puts "server:       #{server_name} (reported version #{reported_version})"
puts "protocol:     #{session.protocol_version}"
puts "tools:        #{client.tool_names.size}"
puts "sdk version:  #{Mem20::VERSION}"

TOKEN = "ruby-quickstart-#{Time.now.to_i}"

started = Process.clock_gettime(Process::CLOCK_MONOTONIC)

store = client.memory_store(content: "quickstart token #{TOKEN}",
                            category: "project",
                            tags: ["quickstart", "ruby"])
puts "\nstore -> #{Mem20::Client.text(store).lines.first&.strip}"

recall = client.memory_recall(query: TOKEN, limit: 5)
recalled = Mem20::Client.text(recall)
puts "recall -> #{recalled.lines.first&.strip}"

elapsed_ms = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - started) * 1000).round(3)
puts "\nround-trip: #{elapsed_ms} ms"
puts "token '#{TOKEN}' recovered: #{recalled.include?(TOKEN)}"

client.close

exit(recalled.include?(TOKEN) ? 0 : 1)
