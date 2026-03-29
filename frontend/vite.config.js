import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/users':     'http://localhost:8000',
      '/rooms':     'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/files':     'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
