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

// Theme configuration
import { lightTheme, darkTheme } from '@/config/theme'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
  },
  defaults: {
    global: {
      // Ensure text is readable in both themes
    },
  },
  // Vuetify 3 uses CSS variables for opacity
  // text-medium-emphasis uses --v-medium-emphasis-opacity
  // We override this in the theme colors or via CSS
})
