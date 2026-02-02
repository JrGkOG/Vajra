/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brutal-yellow': '#FFE500',
        'brutal-pink': '#FF006E',
        'brutal-blue': '#0496FF',
        'brutal-purple': '#9D4EDD',
        'brutal-orange': '#FB5607',
        'brutal-green': '#06FFA5',
        'brutal-bg': '#FAFAFA',
        'brutal-dark': '#000000',
      },
      boxShadow: {
        'hard': '8px 8px 0px 0px rgba(0,0,0,1)',
        'hard-sm': '4px 4px 0px 0px rgba(0,0,0,1)',
        'hard-lg': '12px 12px 0px 0px rgba(0,0,0,1)',
        'hard-xl': '16px 16px 0px 0px rgba(0,0,0,1)',
      },
      borderWidth: {
        '5': '5px',
        '6': '6px',
        '8': '8px',
      },
      fontFamily: {
        mono: ['Space Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'wiggle': 'wiggle 1s ease-in-out infinite',
      },
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-1deg)' },
          '50%': { transform: 'rotate(1deg)' },
        },
      },
    },
  },
  plugins: [],
}
