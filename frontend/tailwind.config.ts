import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: "#18181b",
        "surface-raised": "#27272a",
        primary: "#6366f1",
        "primary-hover": "#4f46e5",
        accent: "#ec4899",
      },
    },
  },
  plugins: [],
} satisfies Config;
