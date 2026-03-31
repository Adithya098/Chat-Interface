import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend port — must match uvicorn's --port flag.
const API_PORT = process.env.API_PORT || 8000
const API_ORIGIN = `http://127.0.0.1:${API_PORT}`

const proxyToApi = {
  target: API_ORIGIN,
  changeOrigin: true,
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/users': proxyToApi,
      '/rooms': proxyToApi,
      '/documents': proxyToApi,
      '/files': proxyToApi,
      '/health': proxyToApi,
      '/db_health': proxyToApi,
    },
  },
})
