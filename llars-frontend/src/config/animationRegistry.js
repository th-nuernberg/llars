/**
 * LLARS Icon & Animation Registry
 *
 * Zentrale Registry fuer alle LLARS Design-System Icons und Animationen.
 * Neue Icons/Animationen MUESSEN hier registriert werden, damit sie im Admin Showcase erscheinen.
 *
 * === HOVER-ANIMATIONS-KLASSEN ===
 *
 * Alle Icon-Hover-Animationen sind in einer zentralen CSS-Datei definiert:
 *   src/icons/itshover/hover-animations.css
 *
 * Klassen:
 *   lift    — translateY(-1.5px)         — Feature/Tool Icons
 *   wiggle  — kurzes Wackeln (0.4s)      — Interaktive Icons (Chatbot, Bell, Wand)
 *   pulse   — scale bounce (0.35s)       — Status/Feedback (Heart, Star, Evaluation)
 *   nudge   — translate Richtung (2px)   — Pfeile, Upload/Download
 *   spin    — rotate 90/180deg (0.4s)    — Gear, Refresh
 *   custom  — icon-spezifisch            — Pencil, Trash, Flask, Lock, Eye, Copy
 *   simple  — scale(1.1)                 — Plus, Minus, X, Check, etc.
 *
 * === WIE MAN EIN NEUES ICON HINZUFUEGT ===
 *
 * 1. Erstelle {Name}Icon.vue in src/icons/itshover/
 * 2. Registriere in src/icons/itshover/index.js (import + iconComponents)
 * 3. Fuege CSS-Klasse in src/icons/itshover/hover-animations.css hinzu
 * 4. Registriere hier in iconAnimations (mit hoverClass) oder staticIcons
 * 5. Icon erscheint automatisch im Admin Showcase
 */

/**
 * Loading Animationen (LLoading Komponente)
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
    description: 'Glanz-Effekt ueber das Dokument',
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
    description: 'Pendelnder Progress-Balken (vor und zurueck)',
    duration: '1.4s',
    easing: 'ease-in-out',
    component: 'LLoading'
  }
]

/**
 * Icon Hover-Animationen (LIcon / itshover)
 *
 * hoverClass: Die Animations-Kategorie aus hover-animations.css
 *   'lift' | 'wiggle' | 'pulse' | 'nudge' | 'spin' | 'custom' | 'simple'
 */
export const iconAnimations = [
  // === LIFT — Feature/Tool Icons ===
  { id: 'home', name: 'Home', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'HomeIcon.vue' },
  { id: 'admin-dashboard', name: 'Admin Dashboard', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'AdminDashboardIcon.vue' },
  { id: 'prompt-engineering', name: 'Prompt Engineering', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'PromptEngineeringIcon.vue' },
  { id: 'batch-generation', name: 'Batch Generation', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'BatchGenerationIcon.vue' },
  { id: 'rag', name: 'RAG', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'RagIcon.vue' },
  { id: 'anonymize', name: 'Anonymize', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'AnonymizeIcon.vue' },
  { id: 'markdown-collab', name: 'Markdown Collab', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'MarkdownCollabIcon.vue' },
  { id: 'latex-collab-ai', name: 'LaTeX Collab AI', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'LatexCollabAiIcon.vue' },
  { id: 'oncoco', name: 'OnCoCo', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'OncocoIcon.vue' },
  { id: 'play', name: 'Player', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'PlayerIcon.vue' },
  { id: 'evaluation-assistant', name: 'Eval Assistant', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'EvaluationAssistantIcon.vue' },
  { id: 'overleaf', name: 'Overleaf', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'OverleafIcon.vue' },
  { id: 'llars-latex', name: 'LLARS LaTeX', description: 'Dezentes Anheben', hoverClass: 'lift', file: 'LlarsLatexIcon.vue' },

  // === WIGGLE — Interaktive Icons ===
  { id: 'chatbot', name: 'Chatbot', description: 'Kurzes Wackeln', hoverClass: 'wiggle', file: 'ChatbotIcon.vue' },
  { id: 'chatbot-manage', name: 'Chatbot Manage', description: 'Kurzes Wackeln', hoverClass: 'wiggle', file: 'ChatbotManageIcon.vue' },
  { id: 'robot', name: 'Robot', description: 'Kurzes Wackeln', hoverClass: 'wiggle', file: 'RobotIcon.vue' },
  { id: 'wand', name: 'Wizard/Wand', description: 'Kurzes Wackeln', hoverClass: 'wiggle', file: 'WandIcon.vue' },
  { id: 'bell', name: 'Bell', description: 'Glocke wackelt', hoverClass: 'wiggle', file: 'BellIcon.vue' },
  { id: 'chat', name: 'Chat', description: 'Kurzes Wackeln', hoverClass: 'wiggle', file: 'ChatIcon.vue' },

  // === PULSE — Status/Feedback ===
  { id: 'heart', name: 'Heart', description: 'Herz pulsiert', hoverClass: 'pulse', file: 'HeartIcon.vue' },
  { id: 'star', name: 'Star', description: 'Stern pulsiert', hoverClass: 'pulse', file: 'StarIcon.vue' },
  { id: 'check-circle', name: 'Success', description: 'Check pulsiert', hoverClass: 'pulse', file: 'CheckedIcon.vue' },
  { id: 'evaluation', name: 'Evaluation', description: 'Skala pulsiert', hoverClass: 'pulse', file: 'EvaluationIcon.vue' },
  { id: 'arena', name: 'Arena', description: 'Arena pulsiert', hoverClass: 'pulse', file: 'ArenaIcon.vue' },
  { id: 'trophy', name: 'Trophy', description: 'Pokal pulsiert', hoverClass: 'pulse', file: 'TrophyIcon.vue' },
  { id: 'database', name: 'Database', description: 'Datenbank pulsiert', hoverClass: 'pulse', file: 'DatabaseIcon.vue' },

  // === NUDGE — Richtungs-Icons ===
  { id: 'reply', name: 'Reply', description: 'Pfeil nach links', hoverClass: 'nudge', file: 'ReplyIcon.vue' },
  { id: 'share', name: 'Share', description: 'Pfeil nach rechts-oben', hoverClass: 'nudge', file: 'ShareIcon.vue' },
  { id: 'download', name: 'Download', description: 'Pfeil nach unten', hoverClass: 'nudge', file: 'DownloadIcon.vue' },
  { id: 'upload', name: 'Upload', description: 'Pfeil nach oben', hoverClass: 'nudge', file: 'UploadIcon.vue' },
  { id: 'copy', name: 'Copy', description: 'Dokument loest sich', hoverClass: 'nudge', file: 'CopyIcon.vue' },

  // === SPIN — Drehende Icons ===
  { id: 'gear', name: 'Gear', description: 'Zahnrad dreht 90 Grad', hoverClass: 'spin', file: 'GearIcon.vue' },
  { id: 'refresh', name: 'Refresh', description: '180-Grad-Drehung', hoverClass: 'spin', file: 'RefreshIcon.vue' },

  // === CUSTOM — Icon-spezifisch ===
  { id: 'pencil', name: 'Pencil', description: 'Stift neigt sich', hoverClass: 'custom', file: 'PencilIcon.vue' },
  { id: 'trash', name: 'Trash', description: 'Muelltonnen-Wackeln', hoverClass: 'custom', file: 'TrashIcon.vue' },
  { id: 'lock', name: 'Lock', description: 'Schloss hebt sich', hoverClass: 'custom', file: 'LockIcon.vue' },
  { id: 'eye', name: 'Eye', description: 'Auge vergroessert sich', hoverClass: 'custom', file: 'EyeIcon.vue' },
  { id: 'flask', name: 'Flask', description: 'Kolben schwenkt', hoverClass: 'custom', file: 'FlaskIcon.vue' },
  { id: 'communication', name: 'Communication', description: 'Bubble + 45-Grad-Wellen', hoverClass: 'custom', file: 'CommunicationIcon.vue' },
  { id: 'voice-call', name: 'Voice Call', description: 'Hoerer klingelt, Wellen pulsieren', hoverClass: 'custom', file: 'VoiceCallIcon.vue' },
  { id: 'video-call', name: 'Video Call', description: 'Aufnahme-Punkt pulsiert', hoverClass: 'custom', file: 'VideoCallIcon.vue' },
  { id: 'ai-lookup', name: 'AI Lookup', description: 'Lupe vergroessert, Sparkles pulsieren', hoverClass: 'custom', file: 'AiLookupIcon.vue' },
  { id: 'file-plus', name: 'File Plus', description: 'Eselsohr faltet, Plus leuchtet', hoverClass: 'custom', file: 'FilePlusIcon.vue' },
  { id: 'folder-plus', name: 'Folder Plus', description: 'Ordner hebt sich, Plus leuchtet', hoverClass: 'custom', file: 'FolderPlusIcon.vue' },

  // === SIMPLE — Minimale Icons ===
  { id: 'file', name: 'File', description: 'Scale-Up', hoverClass: 'simple', file: 'FileIcon.vue' },
  { id: 'folder', name: 'Folder', description: 'Scale-Up', hoverClass: 'simple', file: 'FolderIcon.vue' },
  { id: 'plus', name: 'Plus', description: 'Scale-Up', hoverClass: 'simple', file: 'PlusIcon.vue' },
  { id: 'minus', name: 'Minus', description: 'Scale-Up', hoverClass: 'simple', file: 'MinusIcon.vue' },
  { id: 'x', name: 'Close', description: 'Scale-Up', hoverClass: 'simple', file: 'XIcon.vue' },
  { id: 'check', name: 'Check', description: 'Scale-Up', hoverClass: 'simple', file: 'SimpleCheckedIcon.vue' },
  { id: 'search', name: 'Search', description: 'Scale-Up', hoverClass: 'simple', file: 'SearchIcon.vue' },
  { id: 'menu', name: 'Menu', description: 'Scale-Up', hoverClass: 'simple', file: 'MenuIcon.vue' },
  { id: 'thumb-up', name: 'Thumb Up', description: 'Scale-Up', hoverClass: 'simple', file: 'ThumbUpIcon.vue' },
  { id: 'thumb-down', name: 'Thumb Down', description: 'Scale-Up', hoverClass: 'simple', file: 'ThumbDownIcon.vue' },
]

/**
 * Statische Icons (ohne Hover-Animation)
 * Brand-Icons und Spezial-Icons die bewusst KEINE Animation haben
 */
export const staticIcons = [
  // === BRAND ICONS ===
  { id: 'zotero', name: 'Zotero', description: 'Zotero Literaturverwaltung', category: 'brand', file: 'ZoteroIcon.vue', color: '#CC2936' },
  { id: 'claude', name: 'Claude', description: 'Anthropic Claude AI', category: 'brand', file: 'ClaudeIcon.vue' },
  { id: 'openai', name: 'OpenAI', description: 'OpenAI Logo', category: 'brand', file: 'OpenAiIcon.vue' },
  { id: 'gemini', name: 'Gemini', description: 'Google Gemini AI', category: 'brand', file: 'GeminiIcon.vue' },
  { id: 'ollama', name: 'Ollama', description: 'Ollama Local LLM', category: 'brand', file: 'OllamaIcon.vue' },
  { id: 'litellm', name: 'LiteLLM', description: 'LiteLLM Proxy', category: 'brand', file: 'LitellmIcon.vue' },
  { id: 'vllm', name: 'vLLM', description: 'vLLM Inference Server', category: 'brand', file: 'VllmIcon.vue' },
]

/**
 * Hover-Klassen Metadaten (fuer Showcase)
 */
export const hoverClasses = [
  { id: 'lift', name: 'Lift', description: 'Dezentes Anheben (translateY -1.5px)', color: '#b0ca97' },
  { id: 'wiggle', name: 'Wiggle', description: 'Kurzes Wackeln (rotate hin/her, 0.4s)', color: '#88c4c8' },
  { id: 'pulse', name: 'Pulse', description: 'Scale-Bounce (1 → 1.15 → 1, 0.35s)', color: '#D1BC8A' },
  { id: 'nudge', name: 'Nudge', description: 'Verschiebung in Pfeilrichtung (2px)', color: '#98d4bb' },
  { id: 'spin', name: 'Spin', description: 'Rotation (90/180 Grad, 0.4s)', color: '#e8a087' },
  { id: 'custom', name: 'Custom', description: 'Icon-spezifische Keyframe-Animation', color: '#c4a8d4' },
  { id: 'simple', name: 'Simple', description: 'Dezentes Scale-Up (1.1x)', color: '#a0a0a0' },
]

/**
 * Kontinuierliche Indikatoren
 */
export const indicatorAnimations = [
  { id: 'llars-icon-spin', name: 'Spin', description: 'Kontinuierliche Rotation (mdi-spin Klasse)', duration: '0.9s', easing: 'linear', usage: '<LIcon class="mdi-spin">mdi-loading</LIcon>' },
  { id: 'compile-pulse', name: 'Compile Pulse', description: 'Pulsierender Punkt fuer Kompilier-Status', duration: '1.2s', easing: 'ease-in-out', cssClass: 'compile-dot' },
  { id: 'typing-bounce', name: 'Typing Indicator', description: 'Drei bouncing Punkte fuer Tipp-Animation', duration: '1.4s', easing: 'ease-in-out', cssClass: 'typing-dot' },
  { id: 'pulse-animation', name: 'Pulse', description: 'Einfacher Pulse-Effekt (scale + opacity)', duration: '1.5s', easing: 'ease-in-out', cssClass: 'pulse-dot' }
]

/**
 * Progress-Bar Animationen
 */
export const progressAnimations = [
  { id: 'pendulum-swing', name: 'Pendulum', description: 'Pendelnde Bewegung (vor und zurueck)', duration: '1.4s', easing: 'ease-in-out', cssClass: 'pendulum-bar' }
]

/**
 * Vue Transition Effekte
 */
export const transitionAnimations = [
  { id: 'fade-slide', name: 'Fade + Slide', description: 'Ausblenden mit Verschiebung nach oben', duration: '0.3s', usage: '<transition name="fade-slide">' },
  { id: 'scale', name: 'Scale', description: 'Ein-/Auszoomen', duration: '0.3s', usage: '<transition name="scale">' },
  { id: 'bounce', name: 'Bounce', description: 'Bounce-Effekt beim Einblenden', duration: '0.5s', usage: '<transition name="bounce">' }
]

/**
 * Alle Animationen gruppiert
 */
export const allAnimations = {
  loading: { title: 'LLoading - Dokumenten-Ladeanimation', icon: 'mdi-loading', description: 'Animationen der LLoading Komponente', items: loadingAnimations, type: 'animation' },
  icons: { title: 'Animierte Icons (Hover)', icon: 'mdi-star-shooting', description: 'Icon-Animationen die bei Hover aktiviert werden', items: iconAnimations, type: 'animated-icon' },
  staticIcons: { title: 'Statische Icons (Brand)', icon: 'mdi-shape', description: 'Brand-Icons ohne Hover-Animation', items: staticIcons, type: 'static-icon' },
  indicators: { title: 'Kontinuierliche Indikatoren', icon: 'mdi-rotate-right', description: 'Dauerhaft laufende Status-Animationen', items: indicatorAnimations, type: 'animation' },
  progress: { title: 'Progress Animationen', icon: 'mdi-progress-check', description: 'Animationen fuer Progress-Balken', items: progressAnimations, type: 'animation' },
  transitions: { title: 'Vue Transitions', icon: 'mdi-transition', description: 'Vue Transition Effekte', items: transitionAnimations, type: 'animation' }
}

// === Hilfsfunktionen ===

export function getAllAnimationsFlat() {
  return [...loadingAnimations, ...iconAnimations, ...indicatorAnimations, ...progressAnimations, ...transitionAnimations]
}

export function getAllIconsFlat() {
  return [...iconAnimations, ...staticIcons]
}

export function getStaticIcons() { return staticIcons }
export function getBrandIcons() { return staticIcons.filter(i => i.category === 'brand') }
export function getUIIcons() { return staticIcons.filter(i => i.category === 'ui') }

export function getIconsByHoverClass(hoverClass) {
  return iconAnimations.filter(i => i.hoverClass === hoverClass)
}

export function getAnimationById(id) { return getAllAnimationsFlat().find(a => a.id === id) }
export function getIconById(id) { return getAllIconsFlat().find(i => i.id === id) }
export function getAnimationCount() { return getAllAnimationsFlat().length }
export function getIconCount() { return getAllIconsFlat().length }
export function getTotalCount() { return getAllAnimationsFlat().length + staticIcons.length }
