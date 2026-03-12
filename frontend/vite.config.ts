import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // <-- Importă asta

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // <-- Adaugă asta aici
  ],
})