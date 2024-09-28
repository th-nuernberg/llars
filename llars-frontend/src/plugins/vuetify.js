/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#b0ca97',   // Primäre Farbe (Grünlich)
          secondary: '#81b68b', // Sekundäre Farbe (Dunkleres Grün)
          accent: '#8c9eff',    // Optional: Akzentfarbe (z.B. Blau)
          error: '#b71c1c',     // Optional: Fehlerfarbe (Rot)
          admin: '#8c00ff',     // Optional: Adminfarbe (Rot)
        },
      },
      dark: {
        colors: {
          primary: '#b0ca97',   // Gleiche Primärfarbe für Dark Mode
          secondary: '#81b68b', // Sekundäre Farbe für Dark Mode
        },
      },
    },
  },
})
