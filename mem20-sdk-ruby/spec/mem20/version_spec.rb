# frozen_string_literal: true

RSpec.describe "Mem20 versions" do
  it "has an SDK version" do
    expect(Mem20::VERSION).to match(/\A\d+\.\d+\.\d+\z/)
  end

  it "pins the server release it was verified against" do
    expect(Mem20::SERVER_VERSION).to eq("3.1.2")
  end
end
