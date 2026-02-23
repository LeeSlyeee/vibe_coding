import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  base: "/admin/",
  server: {
    port: 5175,
    proxy: {
      "/api": {
        target: "https://150.230.7.76.nip.io",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
