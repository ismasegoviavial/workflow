/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fusion: {
          blue: '#1a73e8',
          darkBlue: '#1557b0',
          header: '#1a73e8',
          border: '#dadce0',
          bg: '#f8f9fa',
          nodeBorder: '#4285f4',
          nodeSource: '#34a853',
          nodeSink: '#7e57c2',
        }
      }
    },
  },
  plugins: [],
}
