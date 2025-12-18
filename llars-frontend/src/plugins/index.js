/**
 * plugins/index.js
 *
 * Automatically included in `./src/main.js`
 */

// Plugins
import vuetify from './vuetify'

export function registerPlugins (app) {
  app.use(vuetify)
}

// Export vuetify instance for direct access (e.g., theme initialization)
export { vuetify }
