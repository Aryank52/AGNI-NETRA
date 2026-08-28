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
        background: "var(--background)",
        foreground: "var(--foreground)",
        agni: {
          navy: "#070d1e",
          slate: "#0b1426",
          card: "#111c35",
          border: "#1e2e4f",
          accent: "#f59e0b",
          critical: "#ef4444",
          high: "#f97316",
          moderate: "#eab308",
          low: "#10b981",
          cyan: "#06b6d4",
          blue: "#3b82f6",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      }
    },
  },
  plugins: [],
};
export default config;
