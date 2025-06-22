/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}", // General src catch-all
    "./src/modules/customer/**/*.{vue,js,ts,jsx,tsx}",
    "./src/modules/admin/**/*.{vue,js,ts,jsx,tsx}",
    "./src/shared/**/*.{vue,js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#42b983', // Vue green as primary (from customer)
        'secondary': '#34495e', // Darker blue/gray (from customer)
        'accent': '#1abc9c', // Teal (from customer)
        'danger': '#e74c3c', // Red (from customer)
        'light-gray': '#f0f2f5', // (from customer, admin-light-gray is similar)

        // Merged from admin-frontend
        'admin-primary': '#3b82f6',
        'admin-secondary': '#1f2937',
        'admin-accent': '#10b981',
        // 'admin-light-gray': '#f3f4f6', // customer's light-gray is very similar, keeping one for simplicity
      },
      fontFamily: {
        // Using customer-frontend's default sans-serif stack.
        // If 'Inter' or other admin-specific fonts are needed, they should be added to the project.
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```
