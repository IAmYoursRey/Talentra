/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        talNav: {
          dark: "#2E1065",
          DEFAULT: "#4C1D95",
          light: "#6D28D9",
        },
        talPrimary: {
          start: "#6D28D9",
          mid: "#8B5CF6",
          end: "#A855F7",
        },
        talAccent: {
          start: "#A78BFA",
          end: "#C084FC",
        },
        talText: {
          primary: "#261331",
          secondary: "#6F607D",
          muted: "#9584A7",
        },
        talSurface: {
          canvas: "#FCFBFF",
          card: "#FFFFFF",
          border: "#E9E1F4",
          pill: "#F7F2FF",
        },
        brand: {
          50: "#EEF2FD",
          100: "#DCE5FB",
          200: "#B8CAF7",
          300: "#8FAEF3",
          400: "#5D8AEC",
          500: "#3157D5", // Primary / Brand Deep Indigo
          600: "#2745AE",
          700: "#1E3586",
          800: "#16265F",
          900: "#0F1A3F",
        },
        growth: {
          50: "#E6F6F4",
          100: "#CCEFEA",
          200: "#99DFD4",
          300: "#66CFBF",
          400: "#33BFA9",
          500: "#0F8F83", // Talent / Growth Teal
          600: "#0C7269",
          700: "#09564F",
          800: "#063935",
          900: "#031D1A",
        },
        intelligence: {
          50: "#F1EEFB",
          100: "#E3DEF7",
          200: "#C7BDF0",
          300: "#AB9CE8",
          400: "#8F7BE1",
          500: "#7657D6", // Intelligence Violet
          600: "#5E46AB",
          700: "#473480",
          800: "#2F2356",
          900: "#18112B",
        },
        endorse: {
          50: "#ECFDF5",
          100: "#D1FAE5",
          200: "#A7F3D0",
          300: "#6EE7B7",
          400: "#34D399",
          500: "#16A36A", // Approved / Endorse Emerald Green
          600: "#128254",
          700: "#0E6240",
          800: "#09412A",
          900: "#052115",
        },
        revision: {
          50: "#FEF8EC",
          100: "#FDF1D9",
          200: "#FBE3B3",
          300: "#F9D58D",
          400: "#F7C767",
          500: "#D98B18", // Revision Amber
          600: "#AE6F13",
          700: "#82530E",
          800: "#57380A",
          900: "#2B1C05",
        },
        reject: {
          50: "#FDF2F2",
          100: "#FBE6E6",
          200: "#F7CDCD",
          300: "#F3B4B4",
          400: "#EF9B9B",
          500: "#D64545", // Reject Red
          600: "#AB3737",
          700: "#802929",
          800: "#561C1C",
          900: "#2B0E0E",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          muted: "#F8FAFC",
          card: "#FFFFFF",
          border: "#E9E1F4",
        },
      },
      boxShadow: {
        'tal-card': '0 4px 16px rgba(76, 29, 149, 0.06)',
        'tal-hover': '0 8px 24px rgba(76, 29, 149, 0.12)',
        'tal-glow': '0 0 20px rgba(139, 92, 246, 0.25)',
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
