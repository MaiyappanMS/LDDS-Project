/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#F3F5F8',
        surface: '#FFFFFF',
        ink: '#152238',
        muted: '#5B6779',
        line: '#DDE2EA',
        brand: { DEFAULT: '#2F4B8F', dark: '#233A72', tint: '#E8EDF8' },
        sev: {
          high: '#C43D2F', 'high-tint': '#FBE9E6',
          mid: '#B9740F', 'mid-tint': '#FBF0DC',
          low: '#2E7D6B', 'low-tint': '#E3F3EE',
        },
      },
      fontFamily: { sans: ['"Schibsted Grotesk"', 'system-ui', 'Segoe UI', 'sans-serif'] },
      borderRadius: { card: '12px' },
      boxShadow: { card: '0 1px 2px rgba(21,34,56,0.06), 0 0 0 1px rgba(21,34,56,0.03)' },
    },
  },
  plugins: [],
};
