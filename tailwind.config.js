/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './pdf_tools/**/*.html',
    './smallpdf/**/*.html',
    './templates/**/*.{html,js}',
    './**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f5ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#4361ee',
          600: '#3a0ca3',
          700: '#2d3a8c',
          800: '#283274',
          900: '#1e255f',
        },
        secondary: {
          500: '#f72585',
          600: '#b5179e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 10px 30px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 20px 40px rgba(0, 0, 0, 0.1)',
      },
      animation: {
        float: 'float 15s infinite ease-in-out',
      },
      keyframes: {
        float: {
          '0%': { 
            transform: 'translateY(0) rotate(0deg)',
            opacity: '0.2',
          },
          '50%': { 
            transform: 'translateY(-20px) rotate(180deg)',
            opacity: '0.5',
          },
          '100%': { 
            transform: 'translateY(0) rotate(360deg)',
            opacity: '0.2',
          },
        }
      }
    },
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
        lg: '4rem',
        xl: '5rem',
      },
    },
  },
  plugins: [],
}