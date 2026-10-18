#!/usr/bin/env ruby
# frozen_string_literal: true

# Probe the mem20 HTTP health surface without starting a stdio session.
#
#   MEM20_HEALTH_PORT=8080 ruby -Ilib examples/health_probe.rb
require "mem20"

Mem20.configure { |c| c.health_port = Integer(ENV.fetch("MEM20_HEALTH_PORT", "8080")) }
client = Mem20.client

puts "health_url: #{client.config.health_url}"
puts "healthy?:   #{client.healthy?}"
puts "health:     #{client.health.inspect}"
puts "ready:      #{client.ready.inspect}"
puts "metrics:    #{client.metrics.inspect}"

client.close
