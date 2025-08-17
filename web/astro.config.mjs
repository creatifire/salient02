// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

import preact from '@astrojs/preact';

const BACKEND = process.env.BACKEND_ORIGIN || 'http://localhost:8000';

// https://astro.build/config
export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        '/chat': { target: BACKEND, changeOrigin: true },
        '/events': { target: BACKEND, changeOrigin: true },
        '/health': { target: BACKEND, changeOrigin: true },
      }
    }
  },

  integrations: [preact()]
});