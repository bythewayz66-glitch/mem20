#!/usr/bin/env ruby
# frozen_string_literal: true

# A minimal JSON-RPC 2.0 server over newline-delimited stdio. It implements
# just enough of the MCP surface for the transport specs to exercise the real
# write/read loop in a child process: `initialize`, `tools/list` and
# `tools/call`.
require "json"

# Defined before the read loop, because top-level `def` is an expression: a
# definition placed after a loop that never returns would never be reached.
def tool_reply(id, message)
  name = message.dig("params", "name")
  args = message.dig("params", "arguments") || {}

  case name
  when "echo"
    { "jsonrpc" => "2.0", "id" => id,
      "result" => { "content" => [{ "type" => "text", "text" => "echo:#{args["token"]}" }] } }
  when "fail"
    { "jsonrpc" => "2.0", "id" => id,
      "error" => { "code" => -32_602, "message" => "invalid params" } }
  else
    { "jsonrpc" => "2.0", "id" => id,
      "error" => { "code" => -32_601, "message" => "unknown tool: #{name}" } }
  end
end

$stdout.sync = true

while (line = $stdin.gets)
  line = line.strip
  next if line.empty?

  message = JSON.parse(line)
  method = message["method"]
  id = message["id"]

  reply = case method
          when "initialize"
            { "jsonrpc" => "2.0", "id" => id,
              "result" => {
                "protocolVersion" => "2025-06-18",
                "capabilities" => { "tools" => { "listChanged" => false } },
                "serverInfo" => { "name" => "mini-mem20", "version" => "0.0.1" }
              } }
          when "tools/list"
            { "jsonrpc" => "2.0", "id" => id,
              "result" => {
                "tools" => [
                  { "name" => "echo", "description" => "returns its input" },
                  { "name" => "fail", "description" => "always reports an error" }
                ]
              } }
          when "tools/call"
            tool_reply(id, message)
          else
            next unless id # a notification needs no reply

            { "jsonrpc" => "2.0", "id" => id,
              "error" => { "code" => -32_601, "message" => "unknown method: #{method}" } }
          end

  $stdout.puts(JSON.generate(reply))
end
