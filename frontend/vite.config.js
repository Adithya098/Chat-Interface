import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Match uvicorn --host 127.0.0.1; "localhost" on Windows can resolve to ::1 and break the proxy.
const API_ORIGIN = 'http://127.0.0.1:8000'

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
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
