import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative base so the same bundle works at /mem20/agentz/ on GitHub Pages
  // and from a local file server.
  base: "./",
  build: {
    outDir: "../built/react_editor",
    emptyOutDir: true,
    target: "es2020",
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.js"],
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:48022",
        changeOrigin: true,
      },
    },
  },
});
