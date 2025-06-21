/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}", // Scan all relevant files in src
  ],
  theme: {
    extend: {
      // Example: Custom colors or fonts can be added here
      colors: {
        'primary': '#42b983', // Vue green as primary
        'secondary': '#34495e', // Darker blue/gray
        'accent': '#1abc9c', // Teal
        'danger': '#e74c3c', // Red
        'light-gray': '#f0f2f5',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```
