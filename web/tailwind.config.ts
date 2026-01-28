import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm Cream / Paper Palette
        background: "#FFFBF0", // Warm cream
        foreground: "#2D2420", // Dark coffee brown
        
        // Brand Colors
        accent: "#FFD233",     // Sunny yellow
        "accent-hover": "#FFC000",
        
        // UI Colors
        surface: "#FFFFFF",
        "surface-alt": "#F7F2E8",
        border: "#4A3B32",     // Dark brown border
        muted: "#8C7E75",      // Muted earth tone
        
        // Semantic
        success: "#A3E635",    // Lime green
        error: "#F87171",      // Soft red
      },
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        serif: ['DM Serif Display', 'serif'],
      },
      boxShadow: {
        'sketch': '4px 4px 0px 0px #4A3B32',
        'sketch-hover': '6px 6px 0px 0px #4A3B32',
        'sketch-sm': '2px 2px 0px 0px #4A3B32',
      },
      backgroundImage: {
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E\")",
      }
    },
  },
  plugins: [],
};
export default config;
