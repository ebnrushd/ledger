/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'admin-primary': '#3b82f6', // Example: Blue
        'admin-secondary': '#1f2937', // Example: Dark Gray
        'admin-accent': '#10b981', // Example: Green/Teal
        'admin-light-gray': '#f3f4f6',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [
    // require('@tailwindcss/forms'), // Optional: for enhanced form styling
  ],
}
```
