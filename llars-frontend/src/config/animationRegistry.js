/**
 * LLARS Icon & Animation Registry
 *
 * Zentrale Registry für alle LLARS Design-System Icons und Animationen.
 * Neue Icons/Animationen MÜSSEN hier registriert werden, damit sie im Admin Showcase erscheinen.
 *
 * === ICON-TYPEN ===
 *
 * 1. ANIMIERTE ICONS (iconAnimations)
 *    - Haben Hover-Animationen oder kontinuierliche Animationen
 *    - Datei: src/icons/itshover/{Name}Icon.vue
 *    - Beispiel: HomeIcon.vue, ChatbotIcon.vue
 *
 * 2. STATISCHE ICONS (staticIcons)
 *    - Einfache Icons ohne Animation (oder nur minimale Hover-Effekte)
 *    - Datei: src/icons/itshover/{Name}Icon.vue
 *    - Beispiel: ZoteroIcon.vue, ClaudeIcon.vue
 *
 * === WIE MAN EIN NEUES ICON HINZUFÜGT ===
 *
 * 1. Erstelle {Name}Icon.vue in src/icons/itshover/
 * 2. Registriere in src/icons/itshover/index.js (import + iconComponents)
 * 3. Registriere hier in staticIcons oder iconAnimations
 * 4. Icon erscheint automatisch im Admin Showcase
 *
 * === ANIMATIONS-KATEGORIEN ===
 *
 * - loading: Lade-Animationen (LLoading Komponente)
 * - icon: Icon Hover-Animationen (LIcon Komponente)
 * - indicator: Status-Indikatoren (Pulse, Typing, etc.)
 * - progress: Progress-Bar Animationen
 * - transition: Vue Transition Effekte
 */

/**
 * Loading Animationen (LLoading Komponente)
 * Diese erscheinen in der Dokumenten-Lade-Animation
 */
export const loadingAnimations = [
  {
    id: 'llars-loading-float',
    name: 'Float',
    description: 'Schwebendes Dokument (auf/ab)',
    duration: '2.2s',
    easing: 'ease-in-out',
    component: 'LLoading'
  },
  {
    id: 'llars-loading-sweep',
    name: 'Sweep',
    description: 'Glanz-Effekt über das Dokument',
    duration: '1.6s',
    easing: 'ease-in-out',
    component: 'LLoading'
  },
  {
    id: 'llars-loading-line',
    name: 'Line Pulse',
    description: 'Pulsierende Text-Zeilen',
    duration: '1.4s',
    easing: 'ease-in-out',
    component: 'LLoading'
  },
  {
    id: 'llars-loading-progress',
    name: 'Progress Pendel',
    description: 'Pendelnder Progress-Balken (vor und zurück)',
    duration: '1.4s',
    easing: 'ease-in-out',
    component: 'LLoading'
  }
]

/**
 * Icon Hover-Animationen (LIcon / itshover)
 * Diese werden bei Hover auf Icons aktiviert
 *
 * WICHTIG: Icon-Namen müssen dem itshover System entsprechen!
 * Siehe: src/icons/itshover/index.js → iconComponents
 */
export const iconAnimations = [
  {
    id: 'home',
    name: 'Home',
    description: 'Dach hebt sich, Tür öffnet sich',
    trigger: 'hover',
    file: 'HomeIcon.vue'
  },
  {
    id: 'file',
    name: 'File',
    description: 'Eselsohr faltet sich auf',
    trigger: 'hover',
    file: 'FileIcon.vue'
  },
  {
    id: 'file-plus',
    name: 'File Plus',
    description: 'Datei erstellen - Eselsohr faltet, Plus leuchtet',
    trigger: 'hover',
    file: 'FilePlusIcon.vue'
  },
  {
    id: 'folder-plus',
    name: 'Folder Plus',
    description: 'Ordner erstellen - Ordner hebt sich, Plus leuchtet',
    trigger: 'hover',
    file: 'FolderPlusIcon.vue'
  },
  {
    id: 'markdown-collab',
    name: 'Markdown',
    description: 'Eselsohr faltet sich auf',
    trigger: 'hover',
    file: 'MarkdownCollabIcon.vue'
  },
  {
    id: 'latex-collab-ai',
    name: 'LaTeX',
    description: 'Sigma pulsiert, Cursor blinkt',
    trigger: 'hover',
    file: 'LatexCollabAiIcon.vue'
  },
  {
    id: 'latex-doc',
    name: 'LaTeX Doc',
    description: 'Eselsohr faltet sich auf',
    trigger: 'hover',
    file: 'LatexDocIcon.vue'
  },
  {
    id: 'chatbot',
    name: 'Chatbot',
    description: 'Typing-Animation, Sparkle pulsiert',
    trigger: 'hover',
    file: 'ChatbotIcon.vue'
  },
  {
    id: 'wand',
    name: 'Wizard/Wand',
    description: 'Zauberstab schwingt, Sterne leuchten',
    trigger: 'hover',
    file: 'WandIcon.vue'
  },
  {
    id: 'oncoco',
    name: 'OnCoCo',
    description: 'Nadel schwingt, Balken wachsen',
    trigger: 'hover',
    file: 'OncocoIcon.vue'
  },
  {
    id: 'database',
    name: 'Database',
    description: 'Pulse-Effekt, mittlere Scheibe expandiert',
    trigger: 'hover',
    file: 'DatabaseIcon.vue'
  },
  {
    id: 'check-circle',
    name: 'Success',
    description: 'Haken bounced, Sterne funkeln',
    trigger: 'hover',
    file: 'CheckedIcon.vue'
  },
  {
    id: 'star',
    name: 'Star',
    description: 'Stern funkelt und dreht',
    trigger: 'hover',
    file: 'StarIcon.vue'
  },
  {
    id: 'flask',
    name: 'Flask',
    description: 'Blasen steigen auf, Flüssigkeit brodelt',
    trigger: 'hover',
    file: 'FlaskIcon.vue'
  },
  {
    id: 'refresh',
    name: 'Refresh',
    description: 'Rotation bei Hover',
    trigger: 'hover',
    file: 'RefreshIcon.vue'
  },
  {
    id: 'play',
    name: 'Player',
    description: 'Scale bei Hover',
    trigger: 'hover',
    file: 'PlayerIcon.vue'
  }
]

/**
 * Statische Icons (ohne Animation)
 * Diese Icons haben keine oder nur minimale Hover-Effekte
 *
 * Kategorien:
 * - brand: Externe Marken/Dienste (Zotero, Claude, OpenAI, etc.)
 * - ui: UI-Elemente ohne Animation
 */
export const staticIcons = [
  // === BRAND ICONS (Externe Dienste) ===
  {
    id: 'zotero',
    name: 'Zotero',
    description: 'Zotero Literaturverwaltung - stilisiertes Z',
    category: 'brand',
    file: 'ZoteroIcon.vue',
    color: '#CC2936'
  },
  {
    id: 'claude',
    name: 'Claude',
    description: 'Anthropic Claude AI',
    category: 'brand',
    file: 'ClaudeIcon.vue'
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'OpenAI Logo',
    category: 'brand',
    file: 'OpenAiIcon.vue'
  },
  {
    id: 'gemini',
    name: 'Gemini',
    description: 'Google Gemini AI',
    category: 'brand',
    file: 'GeminiIcon.vue'
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Ollama Local LLM',
    category: 'brand',
    file: 'OllamaIcon.vue'
  },
  {
    id: 'litellm',
    name: 'LiteLLM',
    description: 'LiteLLM Proxy',
    category: 'brand',
    file: 'LitellmIcon.vue'
  },
  {
    id: 'vllm',
    name: 'vLLM',
    description: 'vLLM Inference Server',
    category: 'brand',
    file: 'VllmIcon.vue'
  },
  // === UI ICONS (Einfache UI-Elemente) ===
  {
    id: 'arrow-left',
    name: 'Arrow Left',
    description: 'Pfeil nach links',
    category: 'ui',
    file: 'ArrowNarrowLeftIcon.vue'
  },
  {
    id: 'arrow-right',
    name: 'Arrow Right',
    description: 'Pfeil nach rechts',
    category: 'ui',
    file: 'ArrowNarrowRightIcon.vue'
  },
  {
    id: 'arrow-up',
    name: 'Arrow Up',
    description: 'Pfeil nach oben',
    category: 'ui',
    file: 'ArrowNarrowUpIcon.vue'
  },
  {
    id: 'arrow-down',
    name: 'Arrow Down',
    description: 'Pfeil nach unten',
    category: 'ui',
    file: 'ArrowNarrowDownIcon.vue'
  },
  {
    id: 'plus',
    name: 'Plus',
    description: 'Plus/Hinzufügen',
    category: 'ui',
    file: 'PlusIcon.vue'
  },
  {
    id: 'minus',
    name: 'Minus',
    description: 'Minus/Entfernen',
    category: 'ui',
    file: 'MinusIcon.vue'
  },
  {
    id: 'x',
    name: 'Close',
    description: 'Schließen/X',
    category: 'ui',
    file: 'XIcon.vue'
  },
  {
    id: 'check',
    name: 'Check',
    description: 'Häkchen/Bestätigen',
    category: 'ui',
    file: 'SimpleCheckedIcon.vue'
  },
  {
    id: 'search',
    name: 'Search',
    description: 'Suche/Lupe',
    category: 'ui',
    file: 'SearchIcon.vue'
  },
  {
    id: 'menu',
    name: 'Menu',
    description: 'Menü/Drei Punkte',
    category: 'ui',
    file: 'MenuIcon.vue'
  }
]

/**
 * Kontinuierliche Indikatoren
 * Diese laufen dauerhaft ohne User-Interaktion
 */
export const indicatorAnimations = [
  {
    id: 'llars-icon-spin',
    name: 'Spin',
    description: 'Kontinuierliche Rotation (mdi-spin Klasse)',
    duration: '0.9s',
    easing: 'linear',
    usage: '<LIcon class="mdi-spin">mdi-loading</LIcon>'
  },
  {
    id: 'compile-pulse',
    name: 'Compile Pulse',
    description: 'Pulsierender Punkt für Kompilier-Status',
    duration: '1.2s',
    easing: 'ease-in-out',
    cssClass: 'compile-dot'
  },
  {
    id: 'typing-bounce',
    name: 'Typing Indicator',
    description: 'Drei bouncing Punkte für Tipp-Animation',
    duration: '1.4s',
    easing: 'ease-in-out',
    cssClass: 'typing-dot'
  },
  {
    id: 'pulse-animation',
    name: 'Pulse',
    description: 'Einfacher Pulse-Effekt (scale + opacity)',
    duration: '1.5s',
    easing: 'ease-in-out',
    cssClass: 'pulse-dot'
  }
]

/**
 * Progress-Bar Animationen
 */
export const progressAnimations = [
  {
    id: 'pendulum-swing',
    name: 'Pendulum',
    description: 'Pendelnde Bewegung (vor und zurück)',
    duration: '1.4s',
    easing: 'ease-in-out',
    cssClass: 'pendulum-bar'
  }
]

/**
 * Vue Transition Effekte
 * Verwendung: <transition name="{id}">
 */
export const transitionAnimations = [
  {
    id: 'fade-slide',
    name: 'Fade + Slide',
    description: 'Ausblenden mit Verschiebung nach oben',
    duration: '0.3s',
    usage: '<transition name="fade-slide">'
  },
  {
    id: 'scale',
    name: 'Scale',
    description: 'Ein-/Auszoomen',
    duration: '0.3s',
    usage: '<transition name="scale">'
  },
  {
    id: 'bounce',
    name: 'Bounce',
    description: 'Bounce-Effekt beim Einblenden',
    duration: '0.5s',
    usage: '<transition name="bounce">'
  }
]

/**
 * Alle Animationen und Icons gruppiert nach Kategorie
 */
export const allAnimations = {
  loading: {
    title: 'LLoading - Dokumenten-Ladeanimation',
    icon: 'mdi-loading',
    description: 'Animationen der LLoading Komponente',
    items: loadingAnimations,
    type: 'animation'
  },
  icons: {
    title: 'Animierte Icons (Hover)',
    icon: 'mdi-star-shooting',
    description: 'Icon-Animationen die bei Hover aktiviert werden',
    items: iconAnimations,
    type: 'animated-icon'
  },
  staticIcons: {
    title: 'Statische Icons',
    icon: 'mdi-shape',
    description: 'Icons ohne Animation (Brand & UI)',
    items: staticIcons,
    type: 'static-icon'
  },
  indicators: {
    title: 'Kontinuierliche Indikatoren',
    icon: 'mdi-rotate-right',
    description: 'Dauerhaft laufende Status-Animationen',
    items: indicatorAnimations,
    type: 'animation'
  },
  progress: {
    title: 'Progress Animationen',
    icon: 'mdi-progress-check',
    description: 'Animationen für Progress-Balken',
    items: progressAnimations,
    type: 'animation'
  },
  transitions: {
    title: 'Vue Transitions',
    icon: 'mdi-transition',
    description: 'Vue Transition Effekte',
    items: transitionAnimations,
    type: 'animation'
  }
}

/**
 * Hilfsfunktion: Alle Animationen als flache Liste
 */
export function getAllAnimationsFlat() {
  return [
    ...loadingAnimations,
    ...iconAnimations,
    ...indicatorAnimations,
    ...progressAnimations,
    ...transitionAnimations
  ]
}

/**
 * Hilfsfunktion: Alle Icons (animiert + statisch) als flache Liste
 */
export function getAllIconsFlat() {
  return [
    ...iconAnimations,
    ...staticIcons
  ]
}

/**
 * Hilfsfunktion: Nur statische Icons
 */
export function getStaticIcons() {
  return staticIcons
}

/**
 * Hilfsfunktion: Nur Brand Icons
 */
export function getBrandIcons() {
  return staticIcons.filter(icon => icon.category === 'brand')
}

/**
 * Hilfsfunktion: Nur UI Icons
 */
export function getUIIcons() {
  return staticIcons.filter(icon => icon.category === 'ui')
}

/**
 * Hilfsfunktion: Animation/Icon nach ID finden
 */
export function getAnimationById(id) {
  return getAllAnimationsFlat().find(a => a.id === id)
}

/**
 * Hilfsfunktion: Icon nach ID finden (animiert oder statisch)
 */
export function getIconById(id) {
  return getAllIconsFlat().find(i => i.id === id)
}

/**
 * Hilfsfunktion: Anzahl aller Animationen
 */
export function getAnimationCount() {
  return getAllAnimationsFlat().length
}

/**
 * Hilfsfunktion: Anzahl aller Icons
 */
export function getIconCount() {
  return getAllIconsFlat().length
}

/**
 * Hilfsfunktion: Gesamtanzahl (Animationen + statische Icons)
 */
export function getTotalCount() {
  return getAllAnimationsFlat().length + staticIcons.length
}
