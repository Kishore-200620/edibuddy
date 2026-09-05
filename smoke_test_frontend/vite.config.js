import { defineConfig } from 'vite';

export default defineConfig({
  base: '/static/',
  server: {
    proxy: {
      '/avatar': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/voice': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
});
