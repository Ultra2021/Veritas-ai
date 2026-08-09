import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paper / structural
        bone: "#F2EEE3",
        paper: "#FBF9F4",
        sand: "#E7E1D2",
        ink: "#0A0A0A",
        smoke: "#5C574C",

        // Loud accents
        acid: "#CCFF00",      // acid lime
        hot: "#FF2E88",       // hot pink
        cobalt: "#2D4EFF",    // electric blue
        tangerine: "#FF6B1A", // orange
        violetPop: "#8B3DFF", // purple
        mint: "#00E5A0",      // mint green
        sun: "#FFD600",       // yellow
        blood: "#E8202A",     // red
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
        display: ["var(--font-display)", "Impact", "sans-serif"],
      },
      fontSize: {
        "10xl": ["10rem", { lineHeight: "0.85", letterSpacing: "-0.04em" }],
        "11xl": ["13rem", { lineHeight: "0.82", letterSpacing: "-0.045em" }],
      },
      borderWidth: {
        3: "3px",
        5: "5px",
        6: "6px",
      },
      boxShadow: {
        // Hard offset shadows — no blur, ever.
        brutal: "4px 4px 0 0 #0A0A0A",
        "brutal-sm": "2px 2px 0 0 #0A0A0A",
        "brutal-md": "6px 6px 0 0 #0A0A0A",
        "brutal-lg": "10px 10px 0 0 #0A0A0A",
        "brutal-xl": "16px 16px 0 0 #0A0A0A",
        "brutal-acid": "6px 6px 0 0 #CCFF00, 6px 6px 0 3px #0A0A0A",
        "brutal-hot": "6px 6px 0 0 #FF2E88, 6px 6px 0 3px #0A0A0A",
        "brutal-cobalt": "6px 6px 0 0 #2D4EFF, 6px 6px 0 3px #0A0A0A",
        "brutal-inset": "inset 4px 4px 0 0 #0A0A0A",
      },
      animation: {
        marquee: "marquee 26s linear infinite",
        "marquee-rev": "marquee-rev 26s linear infinite",
        "spin-slow": "spin 14s linear infinite",
        blink: "blink 1s step-end infinite",
        wobble: "wobble 0.6s ease-in-out infinite",
        "shake-tiny": "shake-tiny 3.5s ease-in-out infinite",
        "pop-in": "pop-in 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        "slide-stamp": "slide-stamp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        ticker: "ticker 1.2s steps(4) infinite",
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "marquee-rev": {
          "0%": { transform: "translateX(-50%)" },
          "100%": { transform: "translateX(0)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        wobble: {
          "0%, 100%": { transform: "rotate(-2deg)" },
          "50%": { transform: "rotate(2deg)" },
        },
        "shake-tiny": {
          "0%, 92%, 100%": { transform: "translate(0,0) rotate(0deg)" },
          "94%": { transform: "translate(-2px,1px) rotate(-1deg)" },
          "96%": { transform: "translate(2px,-1px) rotate(1deg)" },
          "98%": { transform: "translate(-1px,2px) rotate(0deg)" },
        },
        "pop-in": {
          from: { opacity: "0", transform: "scale(0.9) translateY(10px)" },
          to: { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        "slide-stamp": {
          from: { opacity: "0", transform: "scale(1.6) rotate(-18deg)" },
          to: { opacity: "1", transform: "scale(1) rotate(-8deg)" },
        },
        ticker: {
          "0%": { content: '"."' },
          "100%": { content: '"...."' },
        },
      },
      backgroundImage: {
        "stripe-acid":
          "repeating-linear-gradient(45deg, #CCFF00 0 12px, #0A0A0A 12px 24px)",
        "stripe-ink":
          "repeating-linear-gradient(45deg, #0A0A0A 0 8px, transparent 8px 16px)",
        dots: "radial-gradient(#0A0A0A 1.5px, transparent 1.5px)",
        grid: "linear-gradient(#0A0A0A 1px, transparent 1px), linear-gradient(90deg, #0A0A0A 1px, transparent 1px)",
      },
      backgroundSize: {
        dots: "18px 18px",
        grid: "56px 56px",
      },
      rotate: {
        "1.5": "1.5deg",
        "2.5": "2.5deg",
      },
    },
  },
  plugins: [],
};
export default config;
