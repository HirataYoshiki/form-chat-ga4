import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // You can change this port if needed
    proxy: {
      // Proxying API requests to the backend server
      '/api': {
        target: 'http://localhost:8000', // Assuming your backend runs on port 8000
        changeOrigin: true, // Needed for virtual hosted sites
        // secure: false, // Uncomment if your backend is on HTTPS and has self-signed cert
        // rewrite: (path) => path.replace(/^\/api/, '/api') // Default rewrite is fine
      },
    },
  },
});
