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
          900: '#0D0D0D',
          800: '#1A1A1A',
          700: '#262626',
          600: '#333333',
        },
        accent: {
          neon: '#00FFA3',
          warning: '#FF8A00',
          info: '#00D1FF',
          muted: '#808080',
        },
      },
    },
  },
  plugins: [],
}
