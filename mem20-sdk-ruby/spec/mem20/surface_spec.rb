# frozen_string_literal: true

RSpec.describe Mem20::Surface do
  it "states the surface the server actually exposes" do
    expect(described_class::TOOL_COUNT).to eq(270)
    expect(described_class::DOMAIN_COUNT).to eq(27)
    expect(described_class::DOMAIN_TOOLS).to eq(268)
  end

  it "accounts for the total as domain tools plus the infra job tools" do
    expect(described_class::TOOL_COUNT)
      .to eq(described_class::DOMAIN_TOOLS + described_class::INFRA_TOOLS.size)
  end

  it "names the two infra tools registered outside any domain" do
    expect(described_class::INFRA_TOOLS).to eq(%w[job_status job_wait])
  end

  it "reports an internally consistent surface" do
    expect(described_class.consistent?).to be(true)
  end

  it "summarises both halves so a reader cannot mistake 268 for the total" do
    expect(described_class.summary)
      .to eq("270 tools across 27 domains (268 domain tools + " \
             "2 infra tools: job_status, job_wait)")
  end

  # The regression this guards: the README, docs/USAGE.md, docs/EVIDENCE.md and
  # the gemspec once quoted 268, 270 and 257 respectively for the same surface.
  it "keeps the documented count and the surface constant in agreement" do
    root = File.expand_path("../..", __dir__)
    documented = %w[README.md docs/USAGE.md docs/INSTALL.md mem20-sdk.gemspec]
                 .select { |f| File.exist?(File.join(root, f)) }
                 .to_h { |f| [f, File.read(File.join(root, f))] }

    documented.each do |file, body|
      expect(body).not_to include("257"), "#{file} still quotes the stale 257-tool surface"
      expect(body).not_to match(/268 tools across 26 domains/),
                             "#{file} still quotes 268 tools across 26 domains"
      expect(body).not_to match(/tool_names\.size\s+#\s*268/),
                             "#{file} still predicts 268 from tool_names.size"
    end

    # Wherever a total is stated, it must be the same one.
    expect(documented["README.md"]).to include(described_class::TOOL_COUNT.to_s)
    expect(documented["mem20-sdk.gemspec"]).to include("#{described_class::TOOL_COUNT}-tool")
  end
end
