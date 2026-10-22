import { ConfigurationError } from './errors.js';
import { PROTOCOL_VERSION } from './version.js';

export interface Mem20ConfigOptions {
  /** argv for the server process, default python3 mcp/mcp_server.py */
  serverCommand?: string[];
  /** Working directory for the server (checkout root). */
  cwd?: string;
  storePath?: string;
  cogPath?: string;
  llmBaseUrl?: string;
  llmModel?: string;
  llmApiKey?: string;
  healthHost?: string;
  healthPort?: number;
  protocolVersion?: string;
  /** Per-request timeout in ms. */
  timeoutMs?: number;
}

export class Mem20Config {
  readonly serverCommand: string[];
  readonly cwd?: string;
  readonly storePath?: string;
  readonly cogPath?: string;
  readonly llmBaseUrl?: string;
  readonly llmModel?: string;
  readonly llmApiKey?: string;
  readonly healthHost: string;
  readonly healthPort: number;
  readonly protocolVersion: string;
  readonly timeoutMs: number;

  constructor(opts: Mem20ConfigOptions = {}) {
    const cmd = opts.serverCommand ?? ['python3', 'mcp/mcp_server.py'];
    if (!cmd.length || cmd.some((c) => !c)) {
      throw new ConfigurationError('serverCommand must be a non-empty argv list');
    }
    const port = opts.healthPort ?? Number(process.env.MEM20_HEALTH_PORT || 8080);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new ConfigurationError(`healthPort out of range: ${port}`);
    }
    const timeoutMs = opts.timeoutMs ?? 30_000;
    if (!(timeoutMs > 0)) {
      throw new ConfigurationError('timeoutMs must be positive');
    }

    this.serverCommand = Object.freeze([...cmd]) as string[];
    this.cwd = opts.cwd;
    this.storePath = opts.storePath ?? process.env.MEM20_STORE_PATH;
    this.cogPath = opts.cogPath ?? process.env.MEM20_COG_PATH;
    this.llmBaseUrl = opts.llmBaseUrl ?? process.env.MEM20_LLM_BASE_URL;
    this.llmModel = opts.llmModel ?? process.env.MEM20_LLM_MODEL;
    this.llmApiKey =
      opts.llmApiKey ??
      process.env.MEM20_LLM_API_KEY ??
      process.env.NVAPI_KEY ??
      process.env.NVIDIA_API_KEY;
    this.healthHost = opts.healthHost ?? '127.0.0.1';
    this.healthPort = port;
    this.protocolVersion = opts.protocolVersion ?? PROTOCOL_VERSION;
    this.timeoutMs = timeoutMs;
    Object.freeze(this);
  }

  childEnv(): NodeJS.ProcessEnv {
    const env: NodeJS.ProcessEnv = { ...process.env };
    if (this.storePath) env.MEM20_STORE_PATH = this.storePath;
    if (this.cogPath) env.MEM20_COG_PATH = this.cogPath;
    if (this.llmBaseUrl) env.MEM20_LLM_BASE_URL = this.llmBaseUrl;
    if (this.llmModel) env.MEM20_LLM_MODEL = this.llmModel;
    if (this.llmApiKey) {
      env.MEM20_LLM_API_KEY = this.llmApiKey;
      env.NVAPI_KEY = this.llmApiKey;
    }
    env.MEM20_HEALTH_PORT = String(this.healthPort);
    return env;
  }
}
