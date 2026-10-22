import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { createInterface } from 'node:readline';
import { TransportError } from './errors.js';
import type { Mem20Config } from './config.js';

interface Pending {
  resolve: (v: unknown) => void;
  reject: (e: Error) => void;
  timer: NodeJS.Timeout;
}

export class StdioTransport {
  private child: ChildProcessWithoutNullStreams | null = null;
  private nextId = 1;
  private pending = new Map<number, Pending>();
  private stderrBuf = '';
  private closed = false;

  constructor(private readonly config: Mem20Config) {}

  async start(): Promise<void> {
    if (this.child) return;
    const [cmd, ...args] = this.config.serverCommand;
    this.child = spawn(cmd, args, {
      cwd: this.config.cwd,
      env: this.config.childEnv(),
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.child.on('error', (err) => {
      this.failAll(new TransportError(`spawn failed: ${err.message}`, this.stderrTail()));
    });
    this.child.on('exit', (code, signal) => {
      this.failAll(
        new TransportError(
          `server exited code=${code} signal=${signal}`,
          this.stderrTail(),
        ),
      );
      this.child = null;
    });

    this.child.stderr.setEncoding('utf8');
    this.child.stderr.on('data', (chunk: string) => {
      this.stderrBuf = (this.stderrBuf + chunk).slice(-4096);
    });

    const rl = createInterface({ input: this.child.stdout, crlfDelay: Infinity });
    rl.on('line', (line) => this.onLine(line));
  }

  private stderrTail(): string {
    return this.stderrBuf;
  }

  private onLine(line: string): void {
    let msg: { id?: number; result?: unknown; error?: { code: number; message: string; data?: unknown }; method?: string };
    try {
      msg = JSON.parse(line);
    } catch {
      return;
    }
    if (msg.method && msg.id === undefined) {
      // notification — ignore
      return;
    }
    if (msg.id === undefined) return;
    const p = this.pending.get(msg.id);
    if (!p) return;
    clearTimeout(p.timer);
    this.pending.delete(msg.id);
    if (msg.error) {
      p.reject(
        Object.assign(new Error(msg.error.message), {
          code: msg.error.code,
          data: msg.error.data,
          isToolError: true,
        }),
      );
    } else {
      p.resolve(msg.result);
    }
  }

  private failAll(err: Error): void {
    for (const [, p] of this.pending) {
      clearTimeout(p.timer);
      p.reject(err);
    }
    this.pending.clear();
  }

  async request(method: string, params?: Record<string, unknown>): Promise<unknown> {
    await this.start();
    if (!this.child || this.closed) {
      throw new TransportError('transport closed', this.stderrTail());
    }
    const id = this.nextId++;
    const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params: params ?? {} }) + '\n';

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new TransportError(`timeout after ${this.config.timeoutMs}ms on ${method}`, this.stderrTail()));
      }, this.config.timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.child!.stdin.write(payload, (err) => {
        if (err) {
          clearTimeout(timer);
          this.pending.delete(id);
          reject(new TransportError(`write failed: ${err.message}`, this.stderrTail()));
        }
      });
    });
  }

  async notify(method: string, params?: Record<string, unknown>): Promise<void> {
    await this.start();
    if (!this.child) throw new TransportError('transport closed', this.stderrTail());
    const payload = JSON.stringify({ jsonrpc: '2.0', method, params: params ?? {} }) + '\n';
    this.child.stdin.write(payload);
  }

  async close(): Promise<void> {
    this.closed = true;
    this.failAll(new TransportError('closed'));
    if (this.child) {
      this.child.stdin.end();
      this.child.kill('SIGTERM');
      this.child = null;
    }
  }
}
