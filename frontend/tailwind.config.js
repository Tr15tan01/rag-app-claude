/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#12141c",
        paper: "#faf9f6",
        accent: {
          DEFAULT: "#6c5ce7",
          soft: "#a29bfe",
          deep: "#4834d4",
        },
        surface: {
          DEFAULT: "#ffffff",
          muted: "#f3f2ef",
          border: "#e7e5e0",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 2px 16px rgba(18, 20, 28, 0.06)",
        lift: "0 8px 30px rgba(18, 20, 28, 0.10)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};
