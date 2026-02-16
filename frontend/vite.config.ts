// TODO: Configure Vite with React plugin.
// Proxy /api requests to http://localhost:8000 so the frontend can call the backend without CORS issues in dev.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
