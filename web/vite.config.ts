import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The shell is published from the mem20 repo under docs/app/, so the canonical
// Pages URL is /mem20/app/. The custom domain (mem20.com, per docs/CNAME) serves
// the same tree at /app/. Relative base makes both work and keeps the build
// portable to any host.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: { port: 5180, host: true },
});
