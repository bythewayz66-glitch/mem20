# mem20 Ruby SDK — usage recipes

> Canonical repo: <https://github.com/bythewayz66-glitch/mem20> (`main`) · SDK path: `mem20-sdk-ruby/`

## Configure once

```ruby
require "mem20"

Mem20.configure do |c|
  c.cwd = "/opt/mem20/mem20"
  c.store_path = "/opt/mem20/store"
  c.timeout = 60.0
end
```

`Mem20.configure` rebuilds the config and drops the memoised client, so call it once
at boot. `Mem20.reset_client!` closes the child process if you need to reconfigure at
runtime.

## Store and recall

```ruby
client = Mem20.client

store = client.memory_store(content: "Deploys go out on Thursdays.",
                            category: "project",
                            tags: %w[deploy process])
puts Mem20::Client.text(store)
# => Stored in mem20 memory: [project] Deploys go out on Thursdays. (tags: deploy,process)
#    Record ID: ...

recall = client.memory_recall(query: "when do deploys go out", limit: 5)
puts Mem20::Client.text(recall)
```

`tags:` accepts an `Array` (the SDK joins it into the comma-separated form the server
expects) or a pre-formatted `String`.

## Call any of the 257 tools

```ruby
# By name — works for every registered tool, even ones with no binding yet.
client.tool("memory_status", {})
client.tool("memory_contradict", content: "the sky is green", origin: "user")

# Or as a dynamic binding, resolved against the live tool list.
client.memory_status
client.memory_probe
```

`client.tool_names` returns the cached list:

```ruby
puts client.tool_names.size   # 257
```

## Inspect the schemas

```ruby
tools = client.tools["tools"]
store_schema = tools.find { |t| t["name"] == "memory_store" }
puts JSON.pretty_generate(store_schema["inputSchema"])
```

## Health surface

```ruby
client.healthy?   # => true when GET :8080/health is 2xx
client.health     # => parsed JSON, or nil when the endpoint is not answering
client.ready      # => parsed JSON, or nil
client.metrics    # => parsed counters (raises TransportError when unreachable)
```

## Errors

```ruby
begin
  client.tool("memory_store", {})   # missing required `content`
rescue Mem20::ToolError => e
  warn "tool failed: #{e.message} (code=#{e.code} data=#{e.data.inspect})"
rescue Mem20::TransportError => e
  warn "transport failed: #{e.message}"
end
```

The server reports tool-level failures inside a JSON-RPC error object; the SDK raises
`Mem20::ToolError` with the numeric `#code` and the structured `#data`.

## Threads

One `Mem20::Client` owns one child process and serialises access to it with a mutex,
so a single client is safe to share:

```ruby
client = Mem20.client

threads = 8.times.map do |i|
  Thread.new do
    client.memory_store(content: "worker #{i} tick", category: "general")
  end
end
threads.each(&:join)
```

For higher throughput, give each thread its own client (`Mem20::Client.new`) — one
process per client, fully independent.

## Rails / Sidekiq

```ruby
# config/initializers/mem20.rb
require "mem20"

Mem20.configure do |c|
  c.cwd = ENV.fetch("MEM20_CWD", "/opt/mem20/mem20")
  c.store_path = ENV["MEM20_STORE_PATH"]
  c.timeout = 60.0
end

at_exit { Mem20.reset_client! }   # reap the child process on shutdown
```

```ruby
# app/jobs/remember_job.rb
class RememberJob
  def perform(content)
    Mem20.client.memory_store(content: content, category: "general")
  end
end
```

See `examples/rails_initializer.rb` for the initializer as a standalone file.

## Shut down cleanly

```ruby
Mem20.reset_client!   # closes the transport and reaps the child process
```

`Client#close` (aliased `#shutdown`) terminates the child with `TERM` and waits for it;
it is idempotent.
