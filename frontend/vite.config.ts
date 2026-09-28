import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

/** Build and development-server configuration for the Vue SPA. */
export default defineConfig(({ command }) => ({
  // FastAPI mounts production assets under /static. The development server,
  // however, serves the application directly from its root.
  base: command === "build" ? "/static/" : "/",
  // Compile Vue single-file components used throughout frontend/src.
  plugins: [vue()],
  build: {
    // Write production files directly to the Python package so FastAPI can
    // serve them without a separate Node.js server.
    outDir: fileURLToPath(new URL("../src/job_agent/static", import.meta.url)),
    // Prevent obsolete hashed assets from surviving between builds.
    emptyOutDir: true,
  },
  server: {
    // Conventional Vite port documented in the project README.
    port: 5173,
    // Proxy same-origin-looking browser requests to the local FastAPI server,
    // avoiding CORS configuration during frontend development.
    proxy: {
      "/applications": "http://127.0.0.1:8000",
      "/documents": "http://127.0.0.1:8000",
      "/vacancies": "http://127.0.0.1:8000",
    },
  },
}));
