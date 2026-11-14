/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fbf7ee',
          100: '#f5edd6',
          500: '#c2850c',
          600: '#a36b07',
          700: '#825008',
        }
      }
    },
  },
  plugins: [],
}
