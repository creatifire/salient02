// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

import preact from '@astrojs/preact';

const BACKEND = process.env.BACKEND_ORIGIN || 'http://localhost:8000';

// https://astro.build/config
export default defineConfig({
  // Static output (admin pages moved to web/public/admin/*.html in Phase 3B)
  output: 'static',
  
  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        '/chat': { target: BACKEND, changeOrigin: true },
        '/events': { target: BACKEND, changeOrigin: true },
        '/health': { target: BACKEND, changeOrigin: true },
        '/api': { target: BACKEND, changeOrigin: true },
        '/agents': { target: BACKEND, changeOrigin: true },  // Fix: Proxy agent endpoints
        '/dev/logs/tail': { target: BACKEND, changeOrigin: true },
      }
    }
  },

  integrations: [preact()]
});