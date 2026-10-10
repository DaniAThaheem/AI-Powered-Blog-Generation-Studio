/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: {
          DEFAULT: '#111827',
          elevated: '#1E293B',
          muted: '#182234',
        },
        primary: {
          DEFAULT: '#4F46E5',
          hover: '#4338CA',
          light: '#6366F1',
        },
        accent: {
          DEFAULT: '#06B6D4',
          hover: '#0891B2',
          glow: 'rgba(6, 182, 212, 0.15)',
        },
        border: {
          subtle: '#1F2937',
          DEFAULT: '#374151',
          highlight: '#4B5563',
        },
        text: {
          primary: '#E5E7EB',
          secondary: '#9CA3AF',
          muted: '#6B7280',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
