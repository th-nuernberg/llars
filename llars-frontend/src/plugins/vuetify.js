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
import { aliases as mdiAliases, mdi } from 'vuetify/iconsets/mdi'

// Theme configuration
import { lightTheme, darkTheme } from '@/config/theme'
import { llarsAliases, resolveIconComponent } from '@/icons/itshover'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  icons: {
    defaultSet: 'llars',
    aliases: { ...mdiAliases, ...llarsAliases },
    sets: {
      // MDI icon set for direct MDI icon usage (e.g., icon="mdi:mdi-format-bold")
      mdi,
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
