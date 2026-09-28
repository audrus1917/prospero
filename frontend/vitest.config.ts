import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vitest/config";

/** Vitest configuration shared by the Vue component tests. */
export default defineConfig({
  // Teach the test runner how to compile Vue single-file components.
  plugins: [vue()],
  test: {
    // Components depend on browser APIs such as document, history, and events.
    environment: "jsdom",
  },
});
