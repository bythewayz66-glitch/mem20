# frozen_string_literal: true

RSpec.describe Mem20::Surface do
  it "states the surface the server actually exposes" do
    expect(described_class::TOOL_COUNT).to eq(311)
    expect(described_class::DOMAIN_COUNT).to eq(39)
    expect(described_class::DOMAIN_TOOLS).to eq(311)
  end

  it "accounts for the total as domain tools plus the infra job tools" do
    expect(described_class::TOOL_COUNT)
      .to eq(described_class::DOMAIN_TOOLS + described_class::INFRA_TOOLS.size)
  end

  it "counts the job tools as a domain, not as infra" do
    # `job_status` / `job_wait` used to be transport "infra" outside any domain;
    # in the current taxonomy `job` is one of the 129 domains, so nothing is
    # registered outside a domain.
    expect(described_class::INFRA_TOOLS).to eq([])
  end

  it "reports an internally consistent surface" do
    expect(described_class.consistent?).to be(true)
  end

  it "summarises the surface so a reader cannot mistake a subtotal for the total" do
    expect(described_class.summary).to eq("487 tools across 129 domains")
  end

  # The regression this guards: the README, docs/USAGE.md, docs/EVIDENCE.md and
  # the gemspec once quoted 268, 270 and 257 respectively for the same surface.
  it "keeps the documented count and the surface constant in agreement" do
    root = File.expand_path("../..", __dir__)
    # Every file that states a surface size. docs/EVIDENCE.md quotes the live
    # `TOOL_COUNT:` line and docs/API.md documents the surface accessors, so both
    # belong here: a guard that skips a file cannot catch that file going stale.
    # docs/*.md is globbed rather than listed so a doc added later is covered
    # automatically instead of silently escaping the guard.
    documented = (["README.md", "mem20-sdk.gemspec"] + Dir[File.join(root, "docs", "*.md")]
                  .map { |p| p.delete_prefix("#{root}/") })
                 .select { |f| File.exist?(File.join(root, f)) }
                 .to_h { |f| [f, File.read(File.join(root, f))] }

    documented.each do |file, body|
      # docs/EVIDENCE.md keeps the 0.2.0 capture verbatim as history (the header
      # block and everything from "## 1." on); only its "## 0." section states
      # the live surface, so the drift scan is scoped to that section.
      if file == "docs/EVIDENCE.md"
        body = body[/^## 0\..*?(?=^## 1\.)/m].to_s
        expect(body).not_to be_empty, "docs/EVIDENCE.md has no '## 0.' surface section"
      end

      expect(body).not_to include("257"), "#{file} still quotes the stale 257-tool surface"
      expect(body).not_to match(/268 tools across 26 domains/),
                          "#{file} still quotes 268 tools across 26 domains"
      expect(body).not_to match(/tool_names\.size\s+#\s*268/),
                          "#{file} still predicts 268 from tool_names.size"

      # Any *other* total stated as a current claim is drift. This is the check
      # that actually catches a stale number: the earlier version only banned
      # the exact string "270 tools across 27 domains", so a doc reverted to
      # "## Call any of the 270 tools" slipped through.
      #
      # A bare "N tools" is ambiguous: a doc may legitimately quote the
      # DOMAIN_TOOLS subtotal, but only when the sentence qualifies it as the
      # domain half. So a number is accepted when it is TOOL_COUNT, or when it
      # is DOMAIN_TOOLS *and* the sentence says "domain".
      # CHANGELOG.md is not in `documented` because it quotes old values as
      # history, which is correct.
      body.to_enum(:scan, /\b(\d{2,4})[ -]tools?\b/).each do
        match = Regexp.last_match
        n = match[1].to_i
        next if n == described_class::TOOL_COUNT

        context = body[[match.begin(0) - 40, 0].max, 90].to_s
        subtotal = n == described_class::DOMAIN_TOOLS && context.match?(/domain/i)
        expect(subtotal).to be(true),
                            "#{file} states #{n} tools, but the surface is " \
                            "#{described_class::TOOL_COUNT} (only the domain " \
                            "subtotal #{described_class::DOMAIN_TOOLS} may be quoted, " \
                            "and only when labelled as the domain half)"
      end
      body.scan(/tool_names\.size\s+#\s*(\d{2,4})/).flatten.uniq.each do |n|
        expect(n.to_i).to eq(described_class::TOOL_COUNT),
                          "#{file} predicts tool_names.size == #{n}, but the surface is " \
                          "#{described_class::TOOL_COUNT}"
      end
    end

    # Wherever a total is stated, it must be the same one.
    expect(documented["README.md"]).to include(described_class::TOOL_COUNT.to_s)
    expect(documented["mem20-sdk.gemspec"]).to include("#{described_class::TOOL_COUNT}-tool")

    # docs/EVIDENCE.md records the measured live surface; its `TOOL_COUNT:` line
    # is the number a reader trusts, so pin it to the constant rather than to
    # prose. The 0.2.0 capture's historical `tools: 270` line is deliberately
    # annotated and is not matched here.
    expect(documented["docs/EVIDENCE.md"])
      .to match(/^TOOL_COUNT:\s+#{described_class::TOOL_COUNT}$/)
  end
end
