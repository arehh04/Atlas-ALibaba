/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Friendly warm palette inspired by the SynapseAir logo gradient
        brand: {
          purple: '#8A4FFF',
          'purple-light': '#A66FFF',
          blue: '#5B7FFF',
          cyan: '#4FA8FF',
          lavender: '#F3F1FA',
          'lavender-light': '#F8F7FC',
        },
        // Warm neutrals instead of cold slate
        warm: {
          50: '#FDFCFE',
          100: '#F8F7FC',
          200: '#EEEAF5',
          300: '#DDD8EB',
          400: '#B8B2CC',
          500: '#8E87A5',
          600: '#6B6882',
          700: '#4A4660',
          800: '#2D2A42',
          900: '#1E1B2E',
        },
        // Friendly status colors
        success: {
          light: '#ECFDF5',
          DEFAULT: '#34D399',
          dark: '#065F46',
        },
        warning: {
          light: '#FFFBEB',
          DEFAULT: '#FBBF24',
          dark: '#92400E',
        },
        danger: {
          light: '#FEF2F2',
          DEFAULT: '#F87171',
          dark: '#991B1B',
        },
        info: {
          light: '#EFF6FF',
          DEFAULT: '#60A5FA',
          dark: '#1E40AF',
        },
      },
      fontFamily: {
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
        '4xl': '1.5rem',
      },
      boxShadow: {
        'soft': '0 1px 3px rgba(30, 27, 46, 0.04), 0 4px 12px rgba(138, 79, 255, 0.04)',
        'soft-md': '0 2px 8px rgba(30, 27, 46, 0.06), 0 8px 24px rgba(138, 79, 255, 0.06)',
        'soft-lg': '0 4px 16px rgba(30, 27, 46, 0.08), 0 16px 48px rgba(138, 79, 255, 0.08)',
        'glow-purple': '0 0 20px rgba(138, 79, 255, 0.15)',
        'glow-blue': '0 0 20px rgba(91, 127, 255, 0.15)',
        'inner-soft': 'inset 0 1px 0 rgba(255,255,255,0.6)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #8A4FFF 0%, #5B7FFF 50%, #4FA8FF 100%)',
        'brand-gradient-soft': 'linear-gradient(135deg, rgba(138,79,255,0.1) 0%, rgba(79,168,255,0.1) 100%)',
        'warm-gradient': 'linear-gradient(180deg, #F8F7FC 0%, #F3F1FA 100%)',
      },
      animation: {
        'ping-slow': 'ping-slow 2s ease-in-out infinite',
        'pulse-soft': 'pulse-soft 3s ease-in-out infinite',
        'slide-up': 'slide-up 0.4s ease-out both',
        'slide-in-right': 'slide-in-right 0.35s ease-out both',
        'fade-in': 'fade-in 0.5s ease-out both',
        'shimmer': 'shimmer 3s ease-in-out infinite',
        'float': 'float 4s ease-in-out infinite',
        'bounce-gentle': 'bounce-gentle 2s ease-in-out infinite',
        'gradient-x': 'gradient-x 6s ease infinite',
      },
      keyframes: {
        'ping-slow': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%': { transform: 'scale(1.15)', opacity: '0.3' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          from: { opacity: '0', transform: 'translateX(16px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'bounce-gentle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
    },
  },
  plugins: [],
}
