import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The shell is published from the mem20 repo under docs/app/, so the canonical
// Pages URL is /mem20/app/. The former custom domain used by this project is
// retired and no longer resolves — do not reintroduce it as a base or host.
// Relative base keeps the build portable to any host.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: { port: 5180, host: true },
});
