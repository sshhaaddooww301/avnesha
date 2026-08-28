import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#09090b", // Deep luxury obsidian black
        surface: "#0e0e11",
        card: "#121216",      // Carbon dark gray
        "card-hover": "#191920",
        sidebar: "#09090b",
        border: "#23232a",    // Subtle metallic gray border
        "border-light": "#32323d",
        zinc: {
          850: "#1f1f23",
          900: "#18181b",
          950: "#09090b",
        },
        silver: {
          400: "#d4d4d8",
          300: "#e4e4e7",
          200: "#f4f4f5",
          100: "#fafafa",
        },
        accent: {
          DEFAULT: "#e4e4e7",
          muted: "#71717a",
          highlight: "#ffffff",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 12s linear infinite",
      },
      boxShadow: {
        premium: "0 8px 32px 0 rgba(0, 0, 0, 0.4)",
        card: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
        glow: "0 0 20px -5px rgba(255, 255, 255, 0.08)",
      },
    },
  },
  plugins: [],
};
export default config;
