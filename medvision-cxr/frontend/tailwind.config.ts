import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./types/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        surfaceMuted: "var(--surface-muted)",
        primary: "var(--primary)",
        primaryInk: "var(--primary-ink)",
        accent: "var(--accent)",
        accentSoft: "var(--accent-soft)",
        border: "var(--border)",
        text: "var(--text)",
        textMuted: "var(--text-muted)",
        danger: "var(--danger)",
        success: "var(--success)",
        warning: "var(--warning)",
        info: "var(--info)"
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "'Segoe UI'", "sans-serif"],
        display: ["'Space Grotesk'", "'IBM Plex Sans'", "sans-serif"]
      },
      backgroundImage: {
        "clinical-grid": "linear-gradient(to right, rgba(16, 45, 64, 0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(16, 45, 64, 0.06) 1px, transparent 1px)",
        "hero-glow": "radial-gradient(circle at top left, rgba(72, 189, 187, 0.22), transparent 35%), radial-gradient(circle at top right, rgba(242, 138, 88, 0.18), transparent 32%)"
      },
      boxShadow: {
        soft: "0 18px 40px rgba(6, 32, 44, 0.08)",
        focus: "0 0 0 4px rgba(46, 155, 149, 0.18)"
      },
      borderRadius: {
        xl: "1.25rem",
        '2xl': "1.75rem"
      }
    }
  },
  plugins: []
};

export default config;
