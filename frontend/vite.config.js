import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/onboarding': 'http://localhost:8000',
      '/vocabulary': 'http://localhost:8000',
      '/flashcard': 'http://localhost:8000',
      '/grammar': 'http://localhost:8000',
      '/answerlog': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
    },
  },
})
