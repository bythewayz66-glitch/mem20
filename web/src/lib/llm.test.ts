import { describe, expect, it } from 'vitest';
import { parseCompletion, describeError, mockReply, modeLabel, LLM_MODE } from './llm';

describe('parseCompletion', () => {
  it('reads the OpenAI choices shape', () => {
    expect(parseCompletion({ choices: [{ message: { content: 'hello' } }] })).toBe('hello');
  });

  it('reads a plain string body', () => {
    expect(parseCompletion('  plain text  ')).toBe('plain text');
  });

  it('reads the Anthropic content-block shape', () => {
    expect(parseCompletion({ content: [{ type: 'text', text: 'block text' }] })).toBe('block text');
  });

  it('reads a bare reply key', () => {
    expect(parseCompletion({ reply: 'from reply' })).toBe('from reply');
  });

  it('throws on an empty string rather than returning it', () => {
    expect(() => parseCompletion('   ')).toThrow(/empty response/i);
  });

  it('throws on a payload with no recognisable text', () => {
    expect(() => parseCompletion({ unexpected: 1 })).toThrow(/Could not find reply text/i);
  });

  it('throws on a non-object, non-string payload', () => {
    expect(() => parseCompletion(42)).toThrow(/non-JSON/i);
  });
});

describe('describeError', () => {
  it('names the free-tier rate limit as a rate limit', () => {
    const msg = describeError(402, JSON.stringify({ error: { code: 'FREE_LIMIT' } }));
    expect(msg).toMatch(/rate-limited/i);
    expect(msg).toMatch(/30 seconds/i);
  });

  it('names a 429 as rate limiting', () => {
    expect(describeError(429, '')).toMatch(/rate-limiting/i);
  });

  it('names a 403 as a refusal, not a generic failure', () => {
    expect(describeError(403, '')).toMatch(/refused/i);
  });

  it('falls back to the server message when there is one', () => {
    expect(describeError(500, JSON.stringify({ error: { message: 'boom' } }))).toBe('boom');
  });

  it('falls back to the status when the body is not JSON', () => {
    expect(describeError(500, '<html>')).toMatch(/500/);
  });
});

describe('mockReply', () => {
  it('is clearly labelled as mock so it cannot pass for real', () => {
    expect(mockReply('what is memory')).toMatch(/^\[mock\]/);
  });

  it('echoes the prompt so a test can assert the round trip', () => {
    expect(mockReply('what is memory')).toContain('what is memory');
  });

  it('handles an empty prompt without throwing', () => {
    expect(mockReply('')).toContain('that');
  });
});

describe('modeLabel', () => {
  it('never claims a real model in mock mode', () => {
    // The label is derived from LLM_MODE; in the test env it is the default.
    const label = modeLabel();
    if (LLM_MODE === 'mock') {
      expect(label).toMatch(/MOCK/);
    } else {
      expect(label).not.toMatch(/MOCK/);
    }
  });

  it('names the keyless tier when running pollinations', () => {
    if (LLM_MODE === 'pollinations') {
      expect(modeLabel()).toMatch(/KEYLESS/);
    }
  });
});
