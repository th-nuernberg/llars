<template>
  <div class="not-found-container">
    <!-- Background Particles -->
    <div class="background-particles">
      <div v-for="n in 6" :key="n" class="particle" :class="`particle-${n}`"></div>
    </div>

    <!-- Main Content -->
    <div class="content-wrapper">
      <!-- Animated Document with Magnifying Glass -->
      <div class="animation-area">
        <div class="document-wrapper">
          <!-- Floating Document -->
          <div class="lost-document" @click="showEasterEgg = !showEasterEgg">
            <div class="document-header">
              <div class="document-dots">
                <span class="dot dot-1"></span>
                <span class="dot dot-2"></span>
                <span class="dot dot-3"></span>
              </div>
            </div>
            <div class="document-body">
              <span class="error-code">404</span>
              <div class="document-lines">
                <div class="line line-1"></div>
                <div class="line line-2"></div>
                <div class="line line-3"></div>
              </div>
            </div>
            <div class="document-shimmer"></div>
          </div>

          <!-- Searching Magnifying Glass -->
          <div class="magnifier">
            <div class="magnifier-glass">
              <v-icon size="24" color="white">mdi-magnify</v-icon>
            </div>
            <div class="magnifier-handle"></div>
          </div>
        </div>

        <!-- Easter Egg Message -->
        <transition name="fade">
          <div v-if="showEasterEgg" class="easter-egg">
            <v-icon size="16" class="mr-1">mdi-lightbulb</v-icon>
            {{ easterEggMessages[currentEasterEgg] }}
          </div>
        </transition>
      </div>

      <!-- Text Content -->
      <div class="text-content">
        <h1 class="title">Dokument nicht gefunden</h1>
        <p class="subtitle">
          Diese Seite scheint sich in den Tiefen des Archivs versteckt zu haben...
        </p>
      </div>

      <!-- Search Box -->
      <div class="search-section">
        <div class="search-box">
          <v-icon class="search-icon">mdi-magnify</v-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Wonach suchen Sie?"
            class="search-input"
            @keyup.enter="handleSearch"
          />
          <LBtn
            v-if="searchQuery"
            variant="primary"
            size="small"
            @click="handleSearch"
          >
            Suchen
          </LBtn>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <LBtn variant="primary" prepend-icon="mdi-home" @click="goHome">
          Zur Startseite
        </LBtn>
        <LBtn variant="accent" prepend-icon="mdi-chat" @click="goToChat">
          Chat öffnen
        </LBtn>
      </div>

      <!-- Quick Links -->
      <div class="quick-links">
        <span class="quick-links-label">Schnellzugriff:</span>
        <div class="quick-links-tags">
          <LTag
            v-for="link in quickLinks"
            :key="link.path"
            :variant="link.variant"
            :prepend-icon="link.icon"
            class="quick-link-tag"
            @click="navigateTo(link.path)"
          >
            {{ link.label }}
          </LTag>
        </div>
      </div>
    </div>

    <!-- Attempted Path Info -->
    <div class="path-info">
      <v-icon size="14" class="mr-1">mdi-link-variant</v-icon>
      <span class="path-text">{{ currentPath }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'

const router = useRouter()
const route = useRoute()
const { hasPermission } = usePermissions()

const searchQuery = ref('')
const showEasterEgg = ref(false)
const currentEasterEgg = ref(0)

const currentPath = computed(() => route.fullPath)

const easterEggMessages = [
  'Vielleicht hat ein LLM diese Seite halluziniert?',
  'Error 404: Kaffee nicht gefunden. Moment, falsche Fehlermeldung...',
  'Diese Seite wurde vom Datenschutzbeauftragten anonymisiert.',
  'Die KI sucht noch... bitte haben Sie Geduld.',
  'Haben Sie versucht, die Seite aus- und wieder einzuschalten?'
]

// Rotate easter egg messages
let easterEggInterval = null
onMounted(() => {
  easterEggInterval = setInterval(() => {
    if (showEasterEgg.value) {
      currentEasterEgg.value = (currentEasterEgg.value + 1) % easterEggMessages.length
    }
  }, 4000)
})

onUnmounted(() => {
  if (easterEggInterval) clearInterval(easterEggInterval)
})

// Dynamic quick links based on permissions
const quickLinks = computed(() => {
  const links = [
    { path: '/Home', label: 'Home', icon: 'mdi-home', variant: 'primary' }
  ]

  if (hasPermission('feature:chat:view')) {
    links.push({ path: '/chat', label: 'Chat', icon: 'mdi-chat', variant: 'accent' })
  }

  if (hasPermission('feature:judge:view')) {
    links.push({ path: '/judge', label: 'Judge', icon: 'mdi-scale-balance', variant: 'info' })
  }

  if (hasPermission('feature:ranking:view')) {
    links.push({ path: '/Ranker', label: 'Ranking', icon: 'mdi-format-list-numbered', variant: 'secondary' })
  }

  if (hasPermission('admin:dashboard:view')) {
    links.push({ path: '/admin', label: 'Admin', icon: 'mdi-cog', variant: 'warning' })
  }

  return links
})

function goHome() {
  router.push('/Home')
}

function goToChat() {
  router.push('/chat')
}

function navigateTo(path) {
  router.push(path)
}

function handleSearch() {
  if (!searchQuery.value.trim()) return

  // Simple search logic - navigate to most likely page based on keywords
  const query = searchQuery.value.toLowerCase()

  const searchMap = {
    chat: '/chat',
    bot: '/chat',
    chatbot: '/chat',
    admin: '/admin',
    einstellungen: '/admin',
    settings: '/admin',
    judge: '/judge',
    bewertung: '/judge',
    ranking: '/Ranker',
    ranker: '/Ranker',
    rating: '/Rater',
    rater: '/Rater',
    rag: '/admin?tab=rag',
    dokument: '/admin?tab=rag',
    document: '/admin?tab=rag',
    prompt: '/PromptEngineering',
    anonymize: '/Anonymize',
    anonymisieren: '/Anonymize',
    markdown: '/MarkdownCollab',
    latex: '/LatexCollab',
    kaimo: '/kaimo',
    oncoco: '/oncoco',
    home: '/Home',
    start: '/Home'
  }

  for (const [keyword, path] of Object.entries(searchMap)) {
    if (query.includes(keyword)) {
      router.push(path)
      return
    }
  }

  // Default: go home
  router.push('/Home')
}
</script>

<style scoped>
.not-found-container {
  min-height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(
    180deg,
    rgba(var(--v-theme-background), 1) 0%,
    rgba(var(--v-theme-surface), 0.5) 100%
  );
}

/* Background Particles */
.background-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--llars-primary);
  opacity: 0.15;
  border-radius: 2px;
  animation: float-particle 20s ease-in-out infinite;
}

.particle-1 { top: 10%; left: 15%; animation-delay: 0s; }
.particle-2 { top: 20%; right: 20%; animation-delay: -3s; width: 12px; height: 12px; background: var(--llars-accent); }
.particle-3 { top: 60%; left: 10%; animation-delay: -6s; }
.particle-4 { top: 70%; right: 15%; animation-delay: -9s; width: 6px; height: 6px; background: var(--llars-secondary); }
.particle-5 { top: 40%; left: 5%; animation-delay: -12s; width: 10px; height: 10px; }
.particle-6 { top: 80%; right: 25%; animation-delay: -15s; background: var(--llars-info); }

@keyframes float-particle {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-30px) rotate(90deg); }
  50% { transform: translateY(-10px) rotate(180deg); }
  75% { transform: translateY(-40px) rotate(270deg); }
}

/* Content Wrapper */
.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  z-index: 1;
  max-width: 500px;
  width: 100%;
}

/* Animation Area */
.animation-area {
  position: relative;
  width: 200px;
  height: 180px;
  margin-bottom: 8px;
}

.document-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

/* Floating Document */
.lost-document {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 150px;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  box-shadow: var(--llars-shadow-lg);
  overflow: hidden;
  cursor: pointer;
  animation: float-document 4s ease-in-out infinite;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.lost-document:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

@keyframes float-document {
  0%, 100% {
    transform: translate(-50%, -50%) rotate(-2deg);
  }
  50% {
    transform: translate(-50%, calc(-50% - 12px)) rotate(2deg);
  }
}

.document-header {
  height: 24px;
  background: var(--llars-gradient-primary);
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.document-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-1 { background: var(--llars-danger); }
.dot-2 { background: var(--llars-warning); }
.dot-3 { background: var(--llars-success); }

.document-body {
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.error-code {
  font-size: 2.5rem;
  font-weight: 700;
  background: var(--llars-gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.document-lines {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.line {
  height: 6px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
}

.line-1 { width: 90%; }
.line-2 { width: 70%; }
.line-3 { width: 80%; }

.document-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.15) 50%,
    transparent 100%
  );
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { left: -100%; }
  50% { left: 100%; }
}

/* Magnifying Glass */
.magnifier {
  position: absolute;
  animation: search-around 6s ease-in-out infinite;
}

@keyframes search-around {
  0%, 100% {
    top: 20%;
    left: 10%;
    transform: rotate(-15deg);
  }
  25% {
    top: 60%;
    left: 5%;
    transform: rotate(10deg);
  }
  50% {
    top: 70%;
    left: 70%;
    transform: rotate(-5deg);
  }
  75% {
    top: 15%;
    left: 75%;
    transform: rotate(15deg);
  }
}

.magnifier-glass {
  width: 36px;
  height: 36px;
  background: var(--llars-gradient-accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--llars-shadow-md);
}

.magnifier-handle {
  width: 6px;
  height: 16px;
  background: var(--llars-secondary);
  border-radius: 3px;
  position: absolute;
  bottom: -12px;
  right: 2px;
  transform: rotate(45deg);
}

/* Easter Egg */
.easter-egg {
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(var(--v-theme-surface), 0.95);
  padding: 8px 16px;
  border-radius: 8px 2px 8px 2px;
  font-size: 0.8rem;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  box-shadow: var(--llars-shadow-sm);
  display: flex;
  align-items: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* Text Content */
.text-content {
  text-align: center;
}

.title {
  font-size: 1.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-background));
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-background), 0.7);
  margin: 0;
  max-width: 400px;
}

/* Search Section */
.search-section {
  width: 100%;
  max-width: 400px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 16px 4px 16px 4px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-box:focus-within {
  border-color: var(--llars-primary);
  box-shadow: 0 0 0 3px rgba(176, 202, 151, 0.15);
}

.search-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
  outline: none;
}

.search-input::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

/* Quick Links */
.quick-links {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.quick-links-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-background), 0.5);
}

.quick-links-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-link-tag {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quick-link-tag:hover {
  transform: translateY(-2px);
  box-shadow: var(--llars-shadow-sm);
}

/* Path Info */
.path-info {
  position: absolute;
  bottom: 16px;
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-background), 0.4);
  background: rgba(var(--v-theme-surface), 0.8);
  padding: 4px 12px;
  border-radius: 12px;
}

.path-text {
  font-family: monospace;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Dark Mode Adjustments */
.v-theme--dark .lost-document {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.v-theme--dark .document-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 50%,
    transparent 100%
  );
}

.v-theme--dark .particle {
  opacity: 0.1;
}

/* Mobile Responsive */
@media (max-width: 600px) {
  .not-found-container {
    padding: 16px;
    min-height: calc(100vh - 94px);
  }

  .animation-area {
    width: 160px;
    height: 150px;
  }

  .lost-document {
    width: 100px;
    height: 125px;
  }

  .error-code {
    font-size: 2rem;
  }

  .document-header {
    height: 20px;
  }

  .title {
    font-size: 1.4rem;
  }

  .subtitle {
    font-size: 0.9rem;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-buttons > * {
    width: 100%;
  }

  .easter-egg {
    font-size: 0.7rem;
    max-width: 280px;
    white-space: normal;
    text-align: center;
  }

  .path-info {
    position: relative;
    margin-top: 24px;
  }

  .path-text {
    max-width: 200px;
  }

  .magnifier-glass {
    width: 28px;
    height: 28px;
  }

  .magnifier-glass .v-icon {
    font-size: 18px !important;
  }
}
</style>
