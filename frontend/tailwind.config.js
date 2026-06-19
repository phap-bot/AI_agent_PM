import forms from '@tailwindcss/forms';
import containerQueries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      "colors": {
          "on-tertiary-container": "#ffede6",
          "inverse-surface": "#2e3039",
          "error-container": "#ffdad6",
          "background": "#faf8ff",
          "inverse-primary": "#b4c5ff",
          "primary-fixed-dim": "#b4c5ff",
          "surface-container-high": "#e7e7f3",
          "on-surface": "#191b23",
          "tertiary": "#943700",
          "tertiary-container": "#bc4800",
          "surface-bright": "#faf8ff",
          "tertiary-fixed": "#ffdbcd",
          "on-primary-fixed": "#00174b",
          "on-secondary": "#ffffff",
          "on-secondary-container": "#fffbff",
          "on-tertiary-fixed-variant": "#7d2d00",
          "primary": "#004ac6",
          "on-primary-fixed-variant": "#003ea8",
          "surface-dim": "#d9d9e5",
          "surface-container-highest": "#e1e2ed",
          "secondary-fixed": "#e2dfff",
          "inverse-on-surface": "#f0f0fb",
          "on-error": "#ffffff",
          "tertiary-fixed-dim": "#ffb596",
          "on-tertiary": "#ffffff",
          "secondary-fixed-dim": "#c3c0ff",
          "on-primary-container": "#eeefff",
          "on-surface-variant": "#434655",
          "on-secondary-fixed-variant": "#3323cc",
          "surface-container-lowest": "#ffffff",
          "surface-container": "#ededf9",
          "on-secondary-fixed": "#0f0069",
          "primary-container": "#2563eb",
          "surface-tint": "#0053db",
          "secondary": "#4b41e1",
          "error": "#ba1a1a",
          "surface-container-low": "#f3f3fe",
          "outline": "#737686",
          "on-background": "#191b23",
          "on-primary": "#ffffff",
          "primary-fixed": "#dbe1ff",
          "on-tertiary-fixed": "#360f00",
          "surface-variant": "#e1e2ed",
          "secondary-container": "#645efb",
          "on-error-container": "#93000a",
          "outline-variant": "#c3c6d7",
          "surface": "#faf8ff"
      },
      "borderRadius": {
          "DEFAULT": "0.25rem",
          "lg": "0.5rem",
          "xl": "0.75rem",
          "full": "9999px"
      },
      "spacing": {
          "margin-page": "32px",
          "stack-lg": "24px",
          "gutter": "16px",
          "unit": "4px",
          "container-padding": "24px",
          "stack-md": "16px",
          "stack-sm": "8px"
      },
      "fontFamily": {
          "display-lg": ["Inter", "sans-serif"],
          "body-md": ["Inter", "sans-serif"],
          "headline-sm": ["Inter", "sans-serif"],
          "mono-sm": ["JetBrains Mono", "monospace"],
          "headline-md": ["Inter", "sans-serif"],
          "label-md": ["Inter", "sans-serif"],
          "body-lg": ["Inter", "sans-serif"]
      },
      "fontSize": {
          "display-lg": ["32px", {"lineHeight": "40px", "letterSpacing": "-0.02em", "fontWeight": "700"}],
          "body-md": ["14px", {"lineHeight": "20px", "fontWeight": "400"}],
          "headline-sm": ["18px", {"lineHeight": "24px", "fontWeight": "600"}],
          "mono-sm": ["12px", {"lineHeight": "18px", "fontWeight": "450"}],
          "headline-md": ["24px", {"lineHeight": "32px", "letterSpacing": "-0.01em", "fontWeight": "600"}],
          "label-md": ["12px", {"lineHeight": "16px", "letterSpacing": "0.01em", "fontWeight": "600"}],
          "body-lg": ["16px", {"lineHeight": "24px", "fontWeight": "400"}]
      }
    },
  },
  plugins: [
    forms,
    containerQueries
  ],
}
