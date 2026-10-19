/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#d97706", // Amber 600 - linh thiêng chùa chiền
        secondary: "#0f766e", // Teal 700 - bán đảo Sơn Trà
      }
    },
  },
  plugins: [],
}
