import { Mem20Config } from '../config.js';
import { ConfigurationError } from '../errors.js';

describe('Mem20Config', () => {
  it('freezes defaults', () => {
    const c = new Mem20Config();
    expect(c.serverCommand).toEqual(['python3', 'mcp/mcp_server.py']);
    expect(c.healthPort).toBe(8080);
    expect(c.protocolVersion).toBe('2025-06-18');
    expect(Object.isFrozen(c)).toBe(true);
  });

  it('rejects bad healthPort', () => {
    expect(() => new Mem20Config({ healthPort: 0 })).toThrow(ConfigurationError);
  });

  it('rejects empty serverCommand', () => {
    expect(() => new Mem20Config({ serverCommand: [] })).toThrow(ConfigurationError);
  });
});
