export class Mem20Error extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'Mem20Error';
  }
}

export class ConfigurationError extends Mem20Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

export class TransportError extends Mem20Error {
  readonly stderrTail?: string;
  constructor(message: string, stderrTail?: string) {
    super(stderrTail ? `${message}\n--- server stderr ---\n${stderrTail}` : message);
    this.name = 'TransportError';
    this.stderrTail = stderrTail;
  }
}

export class ToolError extends Mem20Error {
  readonly code: number | string;
  readonly data?: unknown;
  constructor(message: string, code: number | string, data?: unknown) {
    super(message);
    this.name = 'ToolError';
    this.code = code;
    this.data = data;
  }
}
