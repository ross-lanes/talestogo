import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    // Disable host checking when behind Cloudflare proxy
  },
  preview: {
    host: true,
    // Disable host checking when behind Cloudflare proxy
  },
})
