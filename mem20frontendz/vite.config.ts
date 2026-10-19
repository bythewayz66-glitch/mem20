import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * mem20frontendz build config.
 *
 * `base` is the monorepo path: this app lives at <repo>/mem20frontendz, and
 * GitHub Pages serves project sites from that same sub-path, so one value
 * covers both Pages and a subfolder deploy.
 *
 * The three proxies are not a convenience — they are required:
 *   • the MCP server (:8082) sends no CORS preflight headers, so a browser
 *     cannot call it cross-origin at all;
 *   • the kanban door (:8221) is a different origin;
 *   • the control plane issues an httpOnly session cookie, which needs a
 *     same-origin hop to be sent on every request.
 * In production, put these three prefixes behind the same reverse proxy that
 * serves the built assets.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');

  const doorTarget = env.MEM20_DOOR_URL || 'http://127.0.0.1:8221';
  const controlTarget = env.MEM20_CONTROL_URL || 'http://127.0.0.1:8200';
  const mcpTarget = env.MEM20_MCP_URL || 'http://127.0.0.1:8082';

  return {
    plugins: [react()],
    base: '/mem20frontendz/',
    build: {
      outDir: 'dist',
      sourcemap: false,
      // The captured registry is ~103 kB of JSON and the kanban capture ~82 kB.
      // One shared chunk keeps first paint fast without a network waterfall.
      chunkSizeWarningLimit: 900,
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api/door': {
          target: doorTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/door/, ''),
        },
        '/api/control': {
          target: controlTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/control/, ''),
        },
        '/api/mcp': {
          target: mcpTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/mcp/, ''),
        },
      },
    },
    preview: {
      port: 4173,
      host: true,
      proxy: {
        '/api/door': {
          target: doorTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/door/, ''),
        },
        '/api/control': {
          target: controlTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/control/, ''),
        },
        '/api/mcp': {
          target: mcpTarget,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api\/mcp/, ''),
        },
      },
    },
  };
});
