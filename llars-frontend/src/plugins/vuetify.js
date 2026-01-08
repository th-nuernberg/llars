/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com
 */

// Styles
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'
import { h } from 'vue'

// Theme configuration
import { lightTheme, darkTheme } from '@/config/theme'
import { llarsAliases, resolveIconComponent } from '@/icons/itshover'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  icons: {
    defaultSet: 'llars',
    aliases: llarsAliases,
    sets: {
      llars: {
        component: (props) => {
          const { icon, tag, ...rest } = props
          const IconComponent = resolveIconComponent(icon)
          return IconComponent ? h(IconComponent, rest) : h(tag || 'span', rest)
        }
      }
    }
  },
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
