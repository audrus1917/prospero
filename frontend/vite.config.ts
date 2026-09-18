import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/" : "/",
  plugins: [vue()],
  build: {
    outDir: fileURLToPath(new URL("../src/job_agent/static", import.meta.url)),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/applications": "http://127.0.0.1:8000",
      "/documents": "http://127.0.0.1:8000",
      "/vacancies": "http://127.0.0.1:8000",
    },
  },
}));
