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
        background: '#0d120e',
        surface: {
          DEFAULT: 'rgba(21, 28, 22, 0.72)',
          secondary: 'rgba(29, 39, 31, 0.75)',
          tertiary: 'rgba(38, 51, 41, 0.8)',
          glass: 'rgba(25, 34, 27, 0.65)',
        },
        olive: {
          50: '#f4f7f4',
          100: '#e5ede5',
          200: '#cbdccb',
          300: '#a6c2a8',
          400: '#7fa988',
          500: '#5e8967',
          600: '#486e51',
          700: '#3a5841',
          800: '#2f4635',
          900: '#273a2d',
          950: '#141f17',
        },
        earth: {
          50: '#faf7f4',
          100: '#f4eee7',
          200: '#e7d9cc',
          300: '#d5beaa',
          400: '#c09c82',
          500: '#ad7e61',
          600: '#9b6b50',
          700: '#7e5340',
          800: '#674436',
          900: '#54392f',
          950: '#2d1c16',
        },
        clay: {
          DEFAULT: '#c98055',
          light: '#d89467',
          dark: '#9c5f3b',
        },
        sand: {
          DEFAULT: '#d4bc97',
          light: '#e8d8be',
          dark: '#a88e68',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Poppins', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glass-hover': '0 12px 40px 0 rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.18)',
        'glow-olive': '0 0 30px -5px rgba(127, 169, 136, 0.25)',
        'glow-earth': '0 0 30px -5px rgba(201, 128, 85, 0.2)',
      },
      spacing: {
        '4.5': '1.125rem',
      }
    },
  },
  plugins: [],
}
