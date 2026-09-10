/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./bank/**/*.py",
    "./static/bank/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        morgi: {
          primary: '#0077B6',
          secondary: '#0A2B4E',
          accent: '#0096C7',
        },
        border: 'var(--morgi-border)',
        card: 'var(--morgi-card)',
      },
      borderRadius: {
        lg: '0.625rem',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      }
    },
  },
  plugins: [],
}
