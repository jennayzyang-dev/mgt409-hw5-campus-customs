import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The page runs on http://localhost:5173 and calls the FastAPI backend on :8000
// (that origin is allowed in backend/main.py).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 }, // falls back to 5174+ if 5173 is busy
})
