module.exports = {
  darkMode: 'class',
  content: ["../**/*.html"],  // Ensures purge scans all HTML templates
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
          400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
          800: '#1e40af', 900: '#1e3a8a'
        },
        dark: {
          50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1',
          400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155',
          800: '#1e293b', 900: '#0f172a', 950: '#020617'
        }
      },
      animation: {
        'laser-pulse': 'laser-pulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'laser-sweep': 'laser-sweep 8s ease-in-out infinite'
      },
      keyframes: {
        'laser-pulse': { '0%,100%': { opacity: '0.3' }, '50%': { opacity: '1' }},
        'float': { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' }},
        'laser-sweep': { '0%,100%': { transform: 'translateX(-100%)' }, '50%': { transform: 'translateX(100%)' }}
      }
    }
  },
  plugins: [],
}
