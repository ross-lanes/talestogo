import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: ['tales.robotrachel.com', 'localhost'],
  },
  preview: {
    host: true,
    allowedHosts: ['tales.robotrachel.com', 'localhost'],
  },
})
