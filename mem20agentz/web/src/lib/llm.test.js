import { describe, it, expect, vi, afterEach } from "vitest";
import {
  buildMessages,
  parseCompletion,
  describeError,
  mockReply,
  complete,
  LLM_MODE,
  LLM_ENDPOINT,
  LLM_MODEL,
} from "./llm.js";

const agent = {
  id: "atlas",
  name: "Atlas",
  model: "openai-fast",
  systemPrompt: "You are Atlas.",
};

const agentsById = new Map([
  ["atlas", { name: "Atlas" }],
  ["pixel", { name: "Pixel" }],
]);

afterEach(() => {
  vi.restoreAllMocks();
});

describe("llm transport", () => {
  it("defaults to the keyless pollinations endpoint", () => {
    expect(LLM_ENDPOINT).toBe("https://text.pollinations.ai/openai");
    expect(LLM_MODEL).toBe("openai-fast");
  });

  it("builds a system preamble with the room roster", () => {
    const turns = buildMessages(agent, [], agentsById, { roomMembers: ["Pixel", "Ledger"] });
    expect(turns[0].role).toBe("system");
    expect(turns[0].content).toContain("You are Atlas.");
    expect(turns[0].content).toContain("Pixel, Ledger");
  });

  it("labels another agent's turn with its name so it is not read as own words", () => {
    const turns = buildMessages(
      agent,
      [{ authorType: "agent", authorId: "pixel", text: "hello" }],
      agentsById,
    );
    const assistant = turns.find((t) => t.role === "assistant");
    expect(assistant.content).toBe("[Pixel] hello");
  });

  it("passes user turns through unchanged", () => {
    const turns = buildMessages(agent, [{ authorType: "user", text: "question" }], agentsById);
    const user = turns.find((t) => t.role === "user");
    expect(user.content).toBe("question");
  });

  it("notes a directed @mention in the preamble", () => {
    const turns = buildMessages(agent, [], agentsById, { directed: true });
    expect(turns[0].content).toContain("@mention");
  });

  it("parses the OpenAI choices shape", () => {
    expect(parseCompletion({ choices: [{ message: { content: "hi there" } }] })).toBe("hi there");
  });

  it("parses a plain string body", () => {
    expect(parseCompletion("plain reply")).toBe("plain reply");
  });

  it("parses the Anthropic content-block shape", () => {
    expect(parseCompletion({ content: [{ type: "text", text: "block reply" }] })).toBe("block reply");
  });

  it("throws on an empty reply rather than returning ''", () => {
    expect(() => parseCompletion({ choices: [{ message: { content: "   " } }] })).toThrow();
    expect(() => parseCompletion("")).toThrow();
  });

  it("names a rate limit as a rate limit", () => {
    const msg = describeError(402, JSON.stringify({ error: { code: "FREE_LIMIT" } }));
    expect(msg).toContain("rate-limited");
    expect(msg).toContain("30 seconds");
  });

  it("names a 429 as rate limiting", () => {
    expect(describeError(429, "")).toContain("rate-limiting");
  });

  it("surfaces the server message when there is one", () => {
    expect(describeError(500, JSON.stringify({ error: { message: "boom" } }))).toBe("boom");
  });

  it("mockReply is deterministic and names the mode to switch to", () => {
    const r = mockReply(agent, "what is a ledger");
    expect(r).toContain("[mock]");
    expect(r).toContain("Atlas");
    expect(r).toContain("VITE_LLM_MODE=pollinations");
    expect(mockReply(agent, "what is a ledger")).toBe(r);
  });

  it("mockReply never touches the network", () => {
    const spy = vi.spyOn(globalThis, "fetch");
    const r = mockReply(agent, "x");
    expect(r).toContain("[mock]");
    expect(spy).not.toHaveBeenCalled();
  });

  it("complete() posts an OpenAI-compatible body to the endpoint", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ choices: [{ message: { content: "real answer" } }] }),
    });
    const out = await complete(agent, [{ authorType: "user", text: "hi" }], agentsById);
    expect(out).toBe("real answer");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(LLM_ENDPOINT);
    const body = JSON.parse(init.body);
    expect(body.model).toBe("openai-fast");
    expect(Array.isArray(body.messages)).toBe(true);
  });

  it("complete() throws on a non-2xx instead of fabricating a reply", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 402,
      text: async () => JSON.stringify({ error: { code: "FREE_LIMIT" } }),
    });
    await expect(complete(agent, [], agentsById)).rejects.toThrow(/rate-limited/);
  });

  it("LLM_MODE is a known mode", () => {
    expect(["pollinations", "live", "mock"]).toContain(LLM_MODE);
  });
});
