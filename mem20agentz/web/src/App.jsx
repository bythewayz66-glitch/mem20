import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as W from "./lib/workspace.js";
import { complete, ping, LLM_MODE, LLM_MODEL } from "./lib/llm.js";

/* ------------------------------------------------------------ OREO backend */

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

/* ------------------------------------------------------------------ pieces */

function Avatar({ agent, size = 28 }) {
  return (
    <span
      className="avatar"
      style={{
        width: size,
        height: size,
        background: agent ? agent.color : "#30363d",
        fontSize: size * 0.5,
      }}
      title={agent ? agent.name : "You"}
    >
      {agent ? agent.emoji : "🙂"}
    </span>
  );
}

function ModePill() {
  const label =
    LLM_MODE === "mock"
      ? "MOCK MODE"
      : LLM_MODE === "live"
        ? "LIVE ENDPOINT"
        : `REAL LLM · ${LLM_MODEL.toUpperCase()}`;
  return (
    <span className={`mode-pill mode-${LLM_MODE}`} title={`VITE_LLM_MODE=${LLM_MODE}`}>
      {label}
    </span>
  );
}

/* ------------------------------------------------------------- graph view */

function GraphView() {
  const [model, setModel] = useState(null);
  const [graph, setGraph] = useState(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [spoken, setSpoken] = useState("");
  const [error, setError] = useState("");
  const [skill, setSkill] = useState(null);
  const [offline, setOffline] = useState(false);

  const refresh = useCallback(async () => {
    const g = await api("/api/graph");
    setGraph(g);
    return g;
  }, []);

  useEffect(() => {
    (async () => {
      try {
        setModel(await api("/api/model"));
        await refresh();
      } catch (e) {
        setOffline(true);
        setError(String(e.message || e));
      }
    })();
  }, [refresh]);

  async function act(kind) {
    setBusy(true);
    setError("");
    setSpoken("");
    setSkill(null);
    try {
      const out = await api(`/api/${kind}`, { text });
      setSpoken(out.spoken || (out.skill && out.skill.executed ? "Applied." : ""));
      if (out.skill) setSkill(out.skill);
      await refresh();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="graph-view">
      <header className="graph-head">
        <h2>OREO build surface</h2>
        {model && (
          <p className="model">
            engine <code>{model.engine}</code> · build <code>{model.build}</code>
            {model.deterministic ? " · deterministic" : ""}
          </p>
        )}
      </header>

      {offline && (
        <p className="notice">
          The OREO Python backend is not reachable from this static deploy. The graph
          editor needs <code>mem20agentz</code> running locally on port 48022; the
          workspace above works without it.
        </p>
      )}
      {error && !offline && <p className="error">{error}</p>}

      <section className="control">
        <textarea
          rows={3}
          value={text}
          placeholder='e.g. "Connect the db to the dashboard with a secure auth."'
          onChange={(e) => setText(e.target.value)}
        />
        <div className="buttons">
          <button onClick={() => act("say")} disabled={busy || !text.trim()}>
            Say (NL edit)
          </button>
          <button className="assist" onClick={() => act("assist")} disabled={busy || !text.trim()}>
            Assist (agent round-trip)
          </button>
        </div>
      </section>

      {spoken && <p className="spoken">{spoken}</p>}
      {skill && (
        <p className="skill">
          skill <code>oreo_graph_edit</code> registered · executed {String(skill.executed)} ·
          steps {Array.isArray(skill.steps) ? skill.steps.length : "n/a"}
        </p>
      )}

      <div className="panels">
        <section>
          <h3>Nodes ({graph?.graph?.nodes?.length ?? 0})</h3>
          <ul>
            {(graph?.graph?.nodes ?? []).map((n, i) => (
              <li className="node" key={i}>
                <span className="label">{n.label}</span>
                <code>{n.name}</code>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h3>Relationships ({graph?.graph?.relationships?.length ?? 0})</h3>
          <ul>
            {(graph?.graph?.relationships ?? []).map((r, i) => (
              <li className="rel" key={i}>
                <strong>{r.type}</strong>
                <span>
                  {r.from} {"->"} {r.to}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {graph?.ascii && <pre className="ascii">{graph.ascii}</pre>}
    </div>
  );
}

/* --------------------------------------------------------------- workspace */

export default function App() {
  const [state, setState] = useState(() => W.load());
  const [view, setView] = useState("chat");
  const [draft, setDraft] = useState("");
  const [quote, setQuote] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [busyAgent, setBusyAgent] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskAssignee, setTaskAssignee] = useState("");
  const [trgPrompt, setTrgPrompt] = useState("");
  const [trgAgent, setTrgAgent] = useState("");
  const [trgEvery, setTrgEvery] = useState(60);
  const [memText, setMemText] = useState("");
  const [probe, setProbe] = useState(null);
  const [editingAgent, setEditingAgent] = useState(null);
  const fileRef = useRef(null);
  const scrollRef = useRef(null);

  /* persist on every change */
  useEffect(() => {
    W.save(state);
  }, [state]);

  const channel = state.channels.find((c) => c.id === state.activeChannelId) || state.channels[0];
  const msgs = useMemo(() => W.messagesFor(state, channel.id), [state, channel.id]);
  const tasks = useMemo(() => W.tasksFor(state, channel.id), [state, channel.id]);
  const triggers = useMemo(() => W.triggersFor(state, channel.id), [state, channel.id]);
  const agentsById = useMemo(() => new Map(state.agents.map((a) => [a.id, a])), [state.agents]);
  const results = useMemo(() => W.search(state, query), [state, query]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs.length, busyAgent]);

  /* ------------------------------------------------------------- sending */

  const runAgent = useCallback(
    async (agent, history, directed) => {
      setBusyAgent(agent.id);
      setError("");
      try {
        const roomMembers = state.agents.filter((a) => a.id !== agent.id).map((a) => a.name);
        const reply = await complete(agent, history, agentsById, { directed, roomMembers });
        setState((s) =>
          W.addMessage(
            s,
            W.createMessage({
              channelId: channel.id,
              authorType: "agent",
              authorId: agent.id,
              text: reply,
            }),
          ),
        );
      } catch (e) {
        setError(`${agent.name}: ${e.message || e}`);
      } finally {
        setBusyAgent(null);
      }
    },
    [agentsById, channel.id, state.agents],
  );

  async function send() {
    const text = draft.trim();
    if (!text && attachments.length === 0) return;

    const msg = W.createMessage({
      channelId: channel.id,
      authorType: "user",
      text,
      quote: quote ? { id: quote.id, authorId: quote.authorId, text: quote.text } : null,
    });
    msg.attachments = attachments;

    let next = W.addMessage(state, msg);
    next = W.markRead(next, channel.id, msg.at);
    setState(next);
    setDraft("");
    setQuote(null);
    setAttachments([]);

    /* @mention routes to named agents; otherwise the first agent answers. */
    const mentioned = state.agents.filter((a) =>
      new RegExp(`@${a.name}\\b`, "i").test(text),
    );
    const targets = mentioned.length > 0 ? mentioned : state.agents.slice(0, 1);
    const history = [...W.messagesFor(next, channel.id)];

    for (const agent of targets) {
      await runAgent(agent, history, mentioned.length > 0);
    }
  }

  function onFiles(e) {
    const files = Array.from(e.target.files || []);
    files.forEach((f) => {
      const reader = new FileReader();
      reader.onload = () => {
        setAttachments((a) => [
          ...a,
          { name: f.name, type: f.type, size: f.size, dataUrl: String(reader.result) },
        ]);
      };
      reader.readAsDataURL(f);
    });
    e.target.value = "";
  }

  /* ------------------------------------------------------------- triggers */

  useEffect(() => {
    const t = setInterval(() => {
      const due = W.dueTriggers(state);
      if (due.length === 0) return;
      due.forEach(async (trg) => {
        const agent = agentsById.get(trg.agentId);
        if (!agent) return;
        setState((s) => W.updateTrigger(s, trg.id, { lastRunAt: Date.now() }));
        const history = [
          ...W.messagesFor(state, trg.channelId),
          { authorType: "user", text: trg.prompt },
        ];
        try {
          const reply = await complete(agent, history, agentsById, { directed: true });
          setState((s) =>
            W.addMessage(
              s,
              W.createMessage({
                channelId: trg.channelId,
                authorType: "agent",
                authorId: agent.id,
                text: `⏱ ${reply}`,
              }),
            ),
          );
        } catch (e) {
          setError(`${agent.name} (trigger): ${e.message || e}`);
        }
      });
    }, 5000);
    return () => clearInterval(t);
  }, [state, agentsById]);

  /* ---------------------------------------------------------------- render */

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">◍</span>
          <div>
            <strong>mem20 agentZ</strong>
            <small>OREO workspace</small>
          </div>
        </div>

        <div className="side-section">
          <h4>Channels</h4>
          {state.channels.map((c) => {
            const n = W.unreadCount(state, c.id);
            return (
              <button
                key={c.id}
                className={`chan ${c.id === channel.id ? "active" : ""}`}
                onClick={() => setState((s) => W.setActiveChannel(s, c.id))}
              >
                <span className="hash">#</span>
                <span className="chan-name">{c.name}</span>
                {n > 0 && <span className="badge">{n}</span>}
              </button>
            );
          })}
        </div>

        <div className="side-section">
          <h4>Agents</h4>
          {state.agents.map((a) => (
            <button key={a.id} className="roster-row" onClick={() => setEditingAgent(a.id)}>
              <Avatar agent={a} size={24} />
              <span className="roster-name">{a.name}</span>
              <span className="dot" />
            </button>
          ))}
        </div>

        <div className="side-section">
          <h4>Search</h4>
          <input
            className="search"
            value={query}
            placeholder="Search everything…"
            onChange={(e) => setQuery(e.target.value)}
          />
          {query.trim() && (
            <div className="search-results">
              <p className="sr-count">
                {results.messages.length} messages · {results.tasks.length} tasks ·{" "}
                {results.memory.length} memories
              </p>
              {results.messages.slice(0, 6).map((m) => (
                <button
                  key={m.id}
                  className="sr-item"
                  onClick={() => setState((s) => W.setActiveChannel(s, m.channelId))}
                >
                  <span className="sr-chan">#{m.channelId}</span>
                  <span className="sr-text">{m.text.slice(0, 60)}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="side-foot">
          <ModePill />
          <button
            className="probe"
            onClick={async () => setProbe(await ping())}
            title="Test the LLM endpoint"
          >
            Test LLM
          </button>
          {probe && (
            <p className={`probe-out ${probe.ok ? "ok" : "bad"}`}>
              {probe.ok ? "✓" : "✕"} {probe.message}
            </p>
          )}
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>
              <span className="hash">#</span>
              {channel.name}
            </h1>
            <p className="topic">{channel.topic}</p>
          </div>
          <nav className="tabs">
            <button className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}>
              Chat
            </button>
            <button className={view === "graph" ? "on" : ""} onClick={() => setView("graph")}>
              OREO graph
            </button>
          </nav>
        </header>

        {view === "graph" ? (
          <GraphView />
        ) : (
          <>
            <div className="messages" ref={scrollRef}>
              {msgs.length === 0 && (
                <div className="empty">
                  <p>No messages in #{channel.name} yet.</p>
                  <p className="hint">
                    Ask a question, or <code>@Atlas</code> to address one agent directly.
                  </p>
                </div>
              )}
              {msgs.map((m) => {
                const agent = m.authorId ? agentsById.get(m.authorId) : null;
                return (
                  <article key={m.id} className={`msg ${m.authorType}`}>
                    <Avatar agent={agent} />
                    <div className="msg-body">
                      <div className="msg-head">
                        <strong>{agent ? agent.name : "You"}</strong>
                        <time>{new Date(m.at).toLocaleTimeString()}</time>
                        <button className="quote-btn" onClick={() => setQuote(m)}>
                          quote
                        </button>
                      </div>
                      {m.quote && (
                        <blockquote className="quoted">
                          <strong>
                            {m.quote.authorId
                              ? (agentsById.get(m.quote.authorId) || {}).name || "agent"
                              : "You"}
                          </strong>
                          <span>{m.quote.text.slice(0, 140)}</span>
                        </blockquote>
                      )}
                      <p className="msg-text">{m.text}</p>
                      {m.attachments && m.attachments.length > 0 && (
                        <div className="atts">
                          {m.attachments.map((a, i) =>
                            a.type && a.type.startsWith("image/") ? (
                              <img key={i} src={a.dataUrl} alt={a.name} />
                            ) : (
                              <span key={i} className="att-file">
                                📎 {a.name}
                              </span>
                            ),
                          )}
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
              {busyAgent && (
                <article className="msg agent">
                  <Avatar agent={agentsById.get(busyAgent)} />
                  <div className="msg-body">
                    <div className="msg-head">
                      <strong>{(agentsById.get(busyAgent) || {}).name}</strong>
                    </div>
                    <p className="typing">thinking…</p>
                  </div>
                </article>
              )}
            </div>

            {error && <p className="error bar">{error}</p>}

            <div className="composer">
              {quote && (
                <div className="quote-bar">
                  <span>
                    Quoting <strong>{(agentsById.get(quote.authorId) || {}).name || "You"}</strong>:{" "}
                    {quote.text.slice(0, 80)}
                  </span>
                  <button onClick={() => setQuote(null)}>×</button>
                </div>
              )}
              {attachments.length > 0 && (
                <div className="att-bar">
                  {attachments.map((a, i) => (
                    <span key={i} className="att-chip">
                      📎 {a.name}
                      <button
                        onClick={() => setAttachments((x) => x.filter((_, j) => j !== i))}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="composer-row">
                <button className="clip" onClick={() => fileRef.current?.click()} title="Attach">
                  📎
                </button>
                <input
                  ref={fileRef}
                  type="file"
                  multiple
                  hidden
                  onChange={onFiles}
                />
                <textarea
                  rows={2}
                  value={draft}
                  placeholder={`Message #${channel.name} — @Atlas to address one agent`}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                />
                <button className="send" onClick={send} disabled={!!busyAgent}>
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </main>

      <aside className="rail">
        <section className="rail-block">
          <h4>Tasks ({tasks.length})</h4>
          <div className="rail-form">
            <input
              value={taskTitle}
              placeholder="New task…"
              onChange={(e) => setTaskTitle(e.target.value)}
            />
            <select value={taskAssignee} onChange={(e) => setTaskAssignee(e.target.value)}>
              <option value="">unassigned</option>
              {state.agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                if (!taskTitle.trim()) return;
                setState((s) =>
                  W.addTask(
                    s,
                    W.createTask({
                      channelId: channel.id,
                      title: taskTitle,
                      assigneeId: taskAssignee || null,
                    }),
                  ),
                );
                setTaskTitle("");
              }}
            >
              Add
            </button>
          </div>
          {tasks.map((t) => (
            <div key={t.id} className="task-card">
              <div className="task-top">
                <span className={`status ${t.status}`}>{t.status}</span>
                {t.assigneeId && <Avatar agent={agentsById.get(t.assigneeId)} size={18} />}
              </div>
              <p className="task-title">{t.title}</p>
              <div className="task-foot">
                <span className="cont">↻ {t.continuations} continuations</span>
                <button
                  onClick={() => {
                    setState((s) => W.continueTask(s, t.id));
                    const agent = agentsById.get(t.assigneeId) || state.agents[0];
                    const history = [
                      ...W.messagesFor(state, channel.id),
                      { authorType: "user", text: `Continue task: ${t.title}` },
                    ];
                    runAgent(agent, history, true);
                  }}
                >
                  Continue
                </button>
              </div>
            </div>
          ))}
        </section>

        <section className="rail-block">
          <h4>Triggers ({triggers.length})</h4>
          <div className="rail-form">
            <input
              value={trgPrompt}
              placeholder="Prompt to run on a timer…"
              onChange={(e) => setTrgPrompt(e.target.value)}
            />
            <select value={trgAgent} onChange={(e) => setTrgAgent(e.target.value)}>
              <option value="">pick agent</option>
              {state.agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            <select value={trgEvery} onChange={(e) => setTrgEvery(Number(e.target.value))}>
              <option value={30}>every 30s</option>
              <option value={60}>every 1m</option>
              <option value={300}>every 5m</option>
            </select>
            <button
              onClick={() => {
                if (!trgPrompt.trim() || !trgAgent) return;
                setState((s) =>
                  W.addTrigger(
                    s,
                    W.createTrigger({
                      channelId: channel.id,
                      agentId: trgAgent,
                      prompt: trgPrompt,
                      everyMs: trgEvery * 1000,
                    }),
                  ),
                );
                setTrgPrompt("");
              }}
            >
              Add
            </button>
          </div>
          {triggers.map((t) => (
            <div key={t.id} className="trg-card">
              <p className="trg-prompt">{t.prompt}</p>
              <div className="trg-foot">
                <span>
                  {(agentsById.get(t.agentId) || {}).name} · every {t.everyMs / 1000}s
                </span>
                <button
                  onClick={() => setState((s) => W.updateTrigger(s, t.id, { enabled: !t.enabled }))}
                >
                  {t.enabled ? "pause" : "resume"}
                </button>
              </div>
              <span className="trg-last">
                {t.lastRunAt ? `last run ${new Date(t.lastRunAt).toLocaleTimeString()}` : "never run"}
              </span>
            </div>
          ))}
          <p className="rail-note">
            Triggers fire only while this tab is open — there is no server-side scheduler.
          </p>
        </section>

        <section className="rail-block">
          <h4>Memory ({state.memory.length})</h4>
          <div className="rail-form">
            <input
              value={memText}
              placeholder="Remember this…"
              onChange={(e) => setMemText(e.target.value)}
            />
            <button
              onClick={() => {
                if (!memText.trim()) return;
                setState((s) =>
                  W.addMemory(s, W.createMemory({ text: memText, channelId: channel.id })),
                );
                setMemText("");
              }}
            >
              Store
            </button>
          </div>
          {state.memory.slice(-8).reverse().map((m) => (
            <div key={m.id} className="mem-card">
              <p>{m.text}</p>
              <span className="mem-src">
                {m.source} · {new Date(m.at).toLocaleTimeString()}
              </span>
            </div>
          ))}
          <p className="rail-note">Stored in this browser only. Not shared across devices.</p>
        </section>
      </aside>

      {editingAgent && (
        <div className="modal" onClick={() => setEditingAgent(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            {(() => {
              const a = agentsById.get(editingAgent);
              if (!a) return null;
              return (
                <>
                  <h3>
                    <Avatar agent={a} /> {a.name}
                  </h3>
                  <label>
                    Name
                    <input
                      value={a.name}
                      onChange={(e) => setState((s) => W.updateAgent(s, a.id, { name: e.target.value }))}
                    />
                  </label>
                  <label>
                    Emoji
                    <input
                      value={a.emoji}
                      onChange={(e) => setState((s) => W.updateAgent(s, a.id, { emoji: e.target.value }))}
                    />
                  </label>
                  <label>
                    Model
                    <input
                      value={a.model}
                      onChange={(e) => setState((s) => W.updateAgent(s, a.id, { model: e.target.value }))}
                    />
                  </label>
                  <label>
                    System prompt
                    <textarea
                      rows={5}
                      value={a.systemPrompt}
                      onChange={(e) =>
                        setState((s) => W.updateAgent(s, a.id, { systemPrompt: e.target.value }))
                      }
                    />
                  </label>
                  <button className="close" onClick={() => setEditingAgent(null)}>
                    Done
                  </button>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
