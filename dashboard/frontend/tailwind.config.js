/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        surface: {
          900: '#0f1117',
          800: '#161822',
          700: '#1e2030',
          600: '#282a3a',
        },
        accent: {
          red: '#ef4444',
          yellow: '#f59e0b',
          green: '#22c55e',
          blue: '#3b82f6',
        },
      },
    },
  },
  plugins: [],
}
