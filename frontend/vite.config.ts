import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // -------------------------------------------------------
  // Development proxy
  //
  // During local development the React app runs on :5173
  // and the FastAPI backend runs on :8000.
  //
  // All API calls are proxied to the backend so there is
  // no CORS issue and no need to change API URLs between
  // development and production.
  // -------------------------------------------------------
  server: {
    proxy: {
      "/ask": "http://localhost:8000",
      "/clarify": "http://localhost:8000",
      "/execute": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/schema": "http://localhost:8000",
    },
  },

  // -------------------------------------------------------
  // Test configuration (Vitest)
  // -------------------------------------------------------
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },

  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
