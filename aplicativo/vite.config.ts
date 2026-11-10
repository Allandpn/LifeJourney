import { defineConfig } from "vite";

// Durante o desenvolvimento, as chamadas a /api vão para o servidor Python.
export default defineConfig({
  server: {
    host: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
