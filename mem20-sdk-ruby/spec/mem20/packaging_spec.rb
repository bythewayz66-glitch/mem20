# frozen_string_literal: true

require "spec_helper"
require "rubygems/package"
require "tmpdir"
require "fileutils"

# Packaging is the part of a gem that no other spec touches: the library can be
# perfect and still ship a .gem that is missing a file, carries a stale version,
# or cannot be installed. These examples load the real gemspec and, where it
# matters, build the real .gem and read its contents back.

# Defined at file scope, not inside the describe block: RuboCop's
# Lint/ConstantDefinitionInBlock is right that a constant defined inside a
# block gets re-evaluated per example group and leaks into Object.
PACKAGING_SPEC_ROOT = File.expand_path("../..", __dir__)

RSpec.describe "mem20-sdk packaging" do
  def gemspec
    @gemspec ||= Gem::Specification.load(File.join(PACKAGING_SPEC_ROOT, "mem20-sdk.gemspec"))
  end

  it "loads as a valid Gem::Specification" do
    expect(gemspec).to be_a(Gem::Specification)
    expect { gemspec.validate }.not_to raise_error
  end

  it "takes its version from Mem20::VERSION rather than repeating it" do
    expect(gemspec.version.to_s).to eq(Mem20::VERSION)
  end

  it "declares the Ruby floor the code actually needs" do
    expect(gemspec.required_ruby_version).to eq(Gem::Requirement.new(">= 3.1.0"))
  end

  it "ships no runtime dependencies" do
    expect(gemspec.runtime_dependencies).to be_empty
  end

  it "points every metadata URI at the canonical repo" do
    ["homepage_uri", "source_code_uri", "changelog_uri", "documentation_uri", "bug_tracker_uri"]
      .each do |key|
        expect(gemspec.metadata[key]).to start_with("https://github.com/bythewayz66-glitch/mem20"),
                                         "metadata[#{key}] does not point at the canonical repo"
      end
  end

  it "requires MFA for pushes and pins the push host" do
    expect(gemspec.metadata["rubygems_mfa_required"]).to eq("true")
    expect(gemspec.metadata["allowed_push_host"]).to eq("https://rubygems.org")
  end

  it "packages every library file, and nothing outside the declared globs" do
    on_disk = Dir[File.join(PACKAGING_SPEC_ROOT, "lib/**/*.rb")]
              .map { |p| p.delete_prefix("#{PACKAGING_SPEC_ROOT}/") }.sort
    expect(gemspec.files.grep(%r{\Alib/}).sort).to eq(on_disk)
  end

  it "packages the docs, examples and top-level files a reader needs" do
    ["README.md", "CHANGELOG.md", "LICENSE", "docs/API.md", "docs/INSTALL.md", "docs/USAGE.md",
     "docs/EVIDENCE.md", "examples/quickstart.rb"].each do |path|
      expect(gemspec.files).to include(path), "#{path} is missing from spec.files"
    end
  end

  it "keeps spec.files sorted so two builds of one tree are byte-identical" do
    expect(gemspec.files).to eq(gemspec.files.sort)
  end

  it "never packages a built .gem, a lockfile or the specs" do
    expect(gemspec.files.grep(/\.gem\z/)).to be_empty
    expect(gemspec.files).not_to include("Gemfile.lock")
    expect(gemspec.files.grep(%r{\Aspec/})).to be_empty
  end

  it "builds a .gem whose payload matches spec.files" do
    Dir.mktmpdir do |dir|
      built = Dir.chdir(PACKAGING_SPEC_ROOT) do
        Gem::DefaultUserInteraction.use_ui(Gem::SilentUI.new) do
          Gem::Package.build(gemspec)
        end
      end
      FileUtils.mv(File.join(PACKAGING_SPEC_ROOT, built), File.join(dir, built))

      payload = Gem::Package.new(File.join(dir, built)).contents

      expect(payload.sort).to eq(gemspec.files.sort)
      expect(payload).to include("lib/mem20/surface.rb", "lib/mem20/transport/stdio.rb")
    end
  end
end
