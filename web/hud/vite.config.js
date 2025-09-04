import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  build: {
    outDir: '../../apps/hud-macos/Resources/www',
    emptyOutDir: true
  },
  server: {
    port: 5173,
    open: true
  }
})