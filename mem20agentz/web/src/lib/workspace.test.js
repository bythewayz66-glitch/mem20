import { describe, it, expect, beforeEach } from "vitest";
import * as W from "./workspace.js";

describe("workspace store", () => {
  let s;
  beforeEach(() => {
    s = W.initialState();
  });

  it("starts with agents, channels, and no messages", () => {
    expect(s.agents.length).toBe(3);
    expect(s.channels.length).toBe(3);
    expect(s.messages.length).toBe(0);
    expect(s.activeChannelId).toBe("general");
  });

  it("creates a message with a unique id and timestamp", () => {
    const a = W.createMessage({ channelId: "general", authorType: "user", text: "hi" });
    const b = W.createMessage({ channelId: "general", authorType: "user", text: "hi" });
    expect(a.id).not.toBe(b.id);
    expect(a.at).toBeGreaterThan(0);
    expect(a.text).toBe("hi");
  });

  it("filters messages by channel", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "user", text: "a" }));
    st = W.addMessage(st, W.createMessage({ channelId: "graph", authorType: "user", text: "b" }));
    expect(W.messagesFor(st, "general").length).toBe(1);
    expect(W.messagesFor(st, "graph").length).toBe(1);
    expect(W.messagesFor(st, "trust").length).toBe(0);
  });

  it("counts unread agent messages but never the user's own", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "user", text: "me" }));
    st = W.addMessage(st, W.createMessage({ channelId: "general", authorType: "agent", authorId: "atlas", text: "reply" }));
    expect(W.unreadCount(st, "general")).toBe(1);
  });

  it("clears unread when the channel is opened", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "agent", authorId: "atlas", text: "x" }));
    expect(W.unreadCount(st, "general")).toBe(1);
    st = W.setActiveChannel(st, "general");
    expect(W.unreadCount(st, "general")).toBe(0);
  });

  it("sums unread across channels", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "agent", authorId: "atlas", text: "x" }));
    st = W.addMessage(st, W.createMessage({ channelId: "graph", authorType: "agent", authorId: "pixel", text: "y" }));
    expect(W.totalUnread(st)).toBe(2);
  });

  it("searches messages, tasks, and memory case-insensitively", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "user", text: "Ledger integrity" }));
    st = W.addTask(st, W.createTask({ channelId: "general", title: "audit the ledger" }));
    st = W.addMemory(st, W.createMemory({ text: "ledger is append-only" }));
    const r = W.search(st, "LEDGER");
    expect(r.messages.length).toBe(1);
    expect(r.tasks.length).toBe(1);
    expect(r.memory.length).toBe(1);
  });

  it("returns empty search for a blank query", () => {
    const r = W.search(s, "   ");
    expect(r.messages.length).toBe(0);
    expect(r.tasks.length).toBe(0);
    expect(r.memory.length).toBe(0);
  });

  it("treats a never-run trigger as due", () => {
    const st = W.addTrigger(s, W.createTrigger({ channelId: "general", agentId: "atlas", prompt: "p", everyMs: 1000 }));
    expect(W.dueTriggers(st, Date.now()).length).toBe(1);
  });

  it("does NOT treat lastRunAt=0 as never-run", () => {
    let st = W.addTrigger(s, W.createTrigger({ channelId: "general", agentId: "atlas", prompt: "p", everyMs: 60000 }));
    const id = st.triggers[0].id;
    st = W.updateTrigger(st, id, { lastRunAt: 0 });
    // epoch 0 is 1970 — far more than 60s ago, so it IS due, but for the
    // right reason: elapsed time, not a falsy check.
    expect(W.dueTriggers(st, 1000).length).toBe(0);
    expect(W.dueTriggers(st, 61000).length).toBe(1);
  });

  it("skips paused triggers", () => {
    let st = W.addTrigger(s, W.createTrigger({ channelId: "general", agentId: "atlas", prompt: "p", everyMs: 1000 }));
    st = W.updateTrigger(st, st.triggers[0].id, { enabled: false });
    expect(W.dueTriggers(st, Date.now()).length).toBe(0);
  });

  it("advances a task continuation and moves it in progress", () => {
    let st = W.addTask(s, W.createTask({ channelId: "general", title: "t", assigneeId: "atlas" }));
    const id = st.tasks[0].id;
    expect(st.tasks[0].continuations).toBe(0);
    st = W.continueTask(st, id);
    expect(st.tasks[0].continuations).toBe(1);
    expect(st.tasks[0].status).toBe("in_progress");
    st = W.continueTask(st, id);
    expect(st.tasks[0].continuations).toBe(2);
  });

  it("ignores continueTask for an unknown id", () => {
    const st = W.continueTask(s, "nope");
    expect(st.tasks.length).toBe(0);
  });

  it("updates an agent persona", () => {
    const st = W.updateAgent(s, "atlas", { name: "Atlas Prime" });
    expect(W.agentById(st, "atlas").name).toBe("Atlas Prime");
    expect(W.agentById(st, "pixel").name).toBe("Pixel");
  });

  it("round-trips through serialize/deserialize", () => {
    let st = W.addMessage(s, W.createMessage({ channelId: "general", authorType: "user", text: "persist me" }));
    st = W.addMemory(st, W.createMemory({ text: "remember this" }));
    const back = W.deserialize(W.serialize(st));
    expect(back.messages.length).toBe(1);
    expect(back.messages[0].text).toBe("persist me");
    expect(back.memory.length).toBe(1);
  });

  it("falls back to a fresh workspace on corrupt input", () => {
    expect(W.deserialize("{not json").messages.length).toBe(0);
    expect(W.deserialize("null").agents.length).toBe(3);
    expect(W.deserialize("").channels.length).toBe(3);
  });

  it("keeps defaults when a persisted blob is missing arrays", () => {
    const back = W.deserialize(JSON.stringify({ activeChannelId: "graph" }));
    expect(back.agents.length).toBe(3);
    expect(back.messages.length).toBe(0);
    expect(back.activeChannelId).toBe("graph");
  });

  it("stores attachments on a message", () => {
    const m = W.createMessage({ channelId: "general", authorType: "user", text: "see file" });
    m.attachments = [{ name: "a.png", type: "image/png", dataUrl: "data:image/png;base64,xx" }];
    const st = W.addMessage(s, m);
    expect(st.messages[0].attachments.length).toBe(1);
    expect(st.messages[0].attachments[0].name).toBe("a.png");
  });

  it("keeps a quote reference on a message", () => {
    const m = W.createMessage({
      channelId: "general",
      authorType: "user",
      text: "replying",
      quote: { id: "msg_1", authorId: "atlas", text: "original" },
    });
    expect(m.quote.text).toBe("original");
    expect(m.quote.authorId).toBe("atlas");
  });
});
