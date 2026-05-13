// apps/vera/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: [
      'effort-query-roundup.ngrok-free.dev'
    ],
  },
  build: { target: 'es2020' },
})