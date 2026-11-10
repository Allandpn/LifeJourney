import { defineConfig } from "vite";

// Durante o desenvolvimento, as chamadas a /api vão para o servidor Python.
// changeOrigin: false mantém o endereço do aplicativo no cabeçalho Host, que o
// servidor compara com a origem do pedido para recusar pedidos de outros sites.
export default defineConfig({
  server: {
    host: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: false },
    },
  },
});
