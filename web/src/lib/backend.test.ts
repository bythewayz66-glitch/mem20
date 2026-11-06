import { describe, expect, it, vi, afterEach } from 'vitest';
import { bridge, isOk, reasonOf, BRIDGE_ROUTES, DEFAULT_BRIDGE, type Probe } from './backend';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Probe helpers', () => {
  it('isOk is true only for the ok state', () => {
    expect(isOk({ state: 'ok', data: 1 })).toBe(true);
    expect(isOk({ state: 'unreachable', detail: 'x' })).toBe(false);
    expect(isOk({ state: 'error', detail: 'x' })).toBe(false);
  });

  it('reasonOf is empty for ok and names the failure otherwise', () => {
    expect(reasonOf({ state: 'ok', data: 1 })).toBe('');
    expect(reasonOf({ state: 'unreachable', detail: 'refused' })).toMatch(/not reachable/i);
    expect(reasonOf({ state: 'error', detail: 'boom' })).toMatch(/error/i);
  });
});

describe('bridge client', () => {
  it('returns unreachable, not a throw, when the connection is refused', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    const r = await bridge.status();
    expect(r.state).toBe('unreachable');
    if (r.state === 'unreachable') expect(r.detail).toMatch(/Failed to fetch/);
  });

  it('treats a 503 as unreachable, because that is what the bridge raises when MCP is down', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ detail: 'mem20 MCP server unreachable' }),
      }),
    );
    const r = await bridge.status();
    expect(r.state).toBe('unreachable');
  });

  it('treats a 500 as an error, not as unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'engine blew up' }),
      }),
    );
    const r = await bridge.memory();
    expect(r.state).toBe('error');
    if (r.state === 'error') expect(r.detail).toBe('engine blew up');
  });

  it('returns parsed data on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ count: 2, records: [{ id: 'a' }, { id: 'b' }] }),
      }),
    );
    const r = await bridge.memory();
    expect(r.state).toBe('ok');
    if (r.state === 'ok') expect(r.data.count).toBe(2);
  });

  it('never invents a zero when the backend is down', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    const r = await bridge.memory();
    // The critical assertion: there is no `data` to read a fake 0 from.
    expect(r.state).not.toBe('ok');
    expect('data' in r).toBe(false);
  });

  it('posts the recall body in the shape bridge/server.py expects', async () => {
    const spy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ count: 0, records: [] }),
    });
    vi.stubGlobal('fetch', spy);
    await bridge.recall('topic', ['t'], 7);
    const [, init] = spy.mock.calls[0];
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ query: 'topic', tags: ['t'], k: 7 });
  });
});

describe('BRIDGE_ROUTES', () => {
  it('documents the routes the shell actually calls', () => {
    const paths = BRIDGE_ROUTES.map((r) => r.path);
    expect(paths).toContain('/api/status');
    expect(paths).toContain('/api/memory?limit=N');
    expect(paths).toContain('/api/recall');
  });

  it('defaults to the address bridge/server.py listens on', () => {
    expect(DEFAULT_BRIDGE).toBe('http://127.0.0.1:8000');
  });
});
