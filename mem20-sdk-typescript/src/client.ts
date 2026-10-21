import { Mem20Config, type Mem20ConfigOptions } from './config.js';
import { ToolError, TransportError } from './errors.js';
import { StdioTransport } from './transport.js';
import { PROTOCOL_VERSION, VERSION } from './version.js';

export class Mem20Client {
  private readonly config: Mem20Config;
  private readonly transport: StdioTransport;
  private initialized = false;
  private toolNames: string[] | null = null;

  constructor(opts: Mem20ConfigOptions = {}) {
    this.config = new Mem20Config(opts);
    this.transport = new StdioTransport(this.config);
  }

  static create(opts?: Mem20ConfigOptions): Mem20Client {
    return new Mem20Client(opts);
  }

  private async ensureSession(): Promise<void> {
    if (this.initialized) return;
    await this.transport.request('initialize', {
      protocolVersion: this.config.protocolVersion,
      capabilities: {},
      clientInfo: { name: '@mem20/sdk', version: VERSION },
    });
    await this.transport.notify('notifications/initialized');
    this.initialized = true;
  }

  async tools(): Promise<string[]> {
    await this.ensureSession();
    if (this.toolNames) return this.toolNames;
    const result = (await this.transport.request('tools/list', {})) as {
      tools?: { name: string }[];
    };
    this.toolNames = (result.tools ?? []).map((t) => t.name);
    return this.toolNames;
  }

  async tool(name: string, args: Record<string, unknown> = {}): Promise<unknown> {
    await this.ensureSession();
    try {
      return await this.transport.request('tools/call', { name, arguments: args });
    } catch (e) {
      const err = e as Error & { isToolError?: boolean; code?: number | string; data?: unknown };
      if (err.isToolError) {
        throw new ToolError(err.message, err.code ?? -1, err.data);
      }
      throw e;
    }
  }

  async memoryStore(opts: {
    content: string;
    category?: string;
    tags?: string[] | string;
  }): Promise<unknown> {
    return this.tool('memory_store', {
      content: opts.content,
      category: opts.category ?? 'general',
      tags: opts.tags ?? [],
    });
  }

  async memoryRecall(opts: { query: string; limit?: number }): Promise<unknown> {
    return this.tool('memory_recall', {
      query: opts.query,
      limit: opts.limit ?? 5,
    });
  }

  /** Extract plain text from a typical tool result envelope when present. */
  static text(result: unknown): string {
    if (result == null) return '';
    if (typeof result === 'string') return result;
    const r = result as Record<string, unknown>;
    if (typeof r.content === 'string') return r.content;
    if (Array.isArray(r.content)) {
      return r.content
        .map((c) => (typeof c === 'object' && c && 'text' in c ? String((c as { text: string }).text) : JSON.stringify(c)))
        .join('\n');
    }
    return JSON.stringify(result);
  }

  private async getJson(path: string): Promise<unknown | null> {
    const url = `http://${this.config.healthHost}:${this.config.healthPort}${path}`;
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(this.config.timeoutMs) });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  async health(): Promise<unknown | null> {
    return this.getJson('/health');
  }

  async ready(): Promise<unknown | null> {
    return this.getJson('/ready');
  }

  async healthy(): Promise<boolean> {
    const h = await this.health();
    return h != null;
  }

  async metrics(): Promise<unknown> {
    const m = await this.getJson('/metrics');
    if (m == null) throw new TransportError('metrics endpoint unreachable');
    return m;
  }

  async close(): Promise<void> {
    await this.transport.close();
    this.initialized = false;
    this.toolNames = null;
  }
}
