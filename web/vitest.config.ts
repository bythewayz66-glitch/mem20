import { defineConfig } from 'vitest/config';

// The shell's tests are pure-logic tests over src/lib/*. They need no DOM, so
// the node environment is enough and keeps the run fast. WebCrypto (used by
// ledger.ts) is present in Node 20 as globalThis.crypto.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
    setupFiles: ['src/test-setup.ts'],
  },
});
