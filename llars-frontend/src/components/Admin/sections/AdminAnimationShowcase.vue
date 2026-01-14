<template>
  <v-dialog v-model="dialogOpen" max-width="950" scrollable>
    <v-card class="animation-showcase">
      <v-card-title class="d-flex align-center pa-4">
        <LIcon size="24" class="mr-3" color="accent">mdi-animation-play</LIcon>
        <div>
          <div class="text-h6">LLARS Animation & Icon Showcase</div>
          <div class="text-caption text-medium-emphasis">
            {{ animationCount }} registrierte Elemente (Animationen + Icons)
          </div>
        </div>
        <v-spacer />
        <LTag variant="info" size="sm" class="mr-3">
          <LIcon size="12" class="mr-1">mdi-information</LIcon>
          Registry-basiert
        </LTag>
        <v-btn icon variant="text" size="small" @click="dialogOpen = false">
          <LIcon>mdi-close</LIcon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-0">
        <!-- Loading Animation Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.loading.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.loading.title }}</span>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.loading.items.length }}</LTag>
          </div>
          <div class="section-content loading-demos">
            <div class="demo-item">
              <LLoading size="sm" label="Klein (sm)" />
            </div>
            <div class="demo-item">
              <LLoading size="md" label="Mittel (md)" />
            </div>
            <div class="demo-item">
              <LLoading size="lg" label="Groß (lg)" />
            </div>
          </div>
          <div class="section-info">
            <div class="animation-chips">
              <LTooltip v-for="anim in allAnimations.loading.items" :key="anim.id" :text="anim.description">
                <LTag variant="info" size="sm">{{ anim.name }}</LTag>
              </LTooltip>
            </div>
          </div>
        </div>

        <!-- Icon Animations Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.icons.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.icons.title }}</span>
            <LTag variant="accent" size="sm" class="ml-2">Hover zum Aktivieren</LTag>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.icons.items.length }}</LTag>
          </div>
          <div class="section-content icon-demos">
            <div v-for="icon in allAnimations.icons.items" :key="icon.id" class="icon-demo">
              <LTooltip :text="icon.description">
                <div class="icon-wrapper">
                  <LIcon size="32">{{ icon.id }}</LIcon>
                </div>
              </LTooltip>
              <span class="icon-label">{{ icon.name }}</span>
            </div>
          </div>
        </div>

        <!-- Static Icons Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.staticIcons.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.staticIcons.title }}</span>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.staticIcons.items.length }}</LTag>
          </div>
          <div class="section-content static-icons-section">
            <!-- Brand Icons -->
            <div class="static-icons-category">
              <div class="category-header">
                <LIcon size="14" class="mr-1">mdi-domain</LIcon>
                <span class="category-title">Brand Icons</span>
                <LTag variant="info" size="sm" class="ml-2">{{ brandIcons.length }}</LTag>
              </div>
              <div class="icon-demos">
                <div v-for="icon in brandIcons" :key="icon.id" class="icon-demo">
                  <LTooltip :text="icon.description">
                    <div class="icon-wrapper icon-wrapper--brand" :style="icon.color ? `--brand-color: ${icon.color}` : ''">
                      <LIcon size="32" :style="icon.color ? `color: ${icon.color}` : ''">{{ icon.id }}</LIcon>
                    </div>
                  </LTooltip>
                  <span class="icon-label">{{ icon.name }}</span>
                </div>
              </div>
            </div>
            <!-- UI Icons -->
            <div class="static-icons-category">
              <div class="category-header">
                <LIcon size="14" class="mr-1">mdi-vector-square</LIcon>
                <span class="category-title">UI Icons</span>
                <LTag variant="info" size="sm" class="ml-2">{{ uiIcons.length }}</LTag>
              </div>
              <div class="icon-demos">
                <div v-for="icon in uiIcons" :key="icon.id" class="icon-demo">
                  <LTooltip :text="icon.description">
                    <div class="icon-wrapper">
                      <LIcon size="32">{{ icon.id }}</LIcon>
                    </div>
                  </LTooltip>
                  <span class="icon-label">{{ icon.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Indicator Animations Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.indicators.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.indicators.title }}</span>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.indicators.items.length }}</LTag>
          </div>
          <div class="section-content spinner-demos">
            <!-- Spin -->
            <div class="demo-item">
              <div class="spinner-wrapper">
                <LIcon size="32" class="mdi-spin">mdi-loading</LIcon>
              </div>
              <span class="demo-label">Spin</span>
              <code class="demo-code">mdi-spin</code>
            </div>
            <!-- Pulse -->
            <div class="demo-item">
              <div class="pulse-dot"></div>
              <span class="demo-label">Pulse</span>
              <code class="demo-code">.pulse-dot</code>
            </div>
            <!-- Compile -->
            <div class="demo-item">
              <div class="compile-indicator">
                <span class="compile-dot"></span>
                Kompilieren...
              </div>
              <span class="demo-label">Compile</span>
              <code class="demo-code">.compile-dot</code>
            </div>
            <!-- Typing -->
            <div class="demo-item">
              <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
              <span class="demo-label">Typing</span>
              <code class="demo-code">.typing-dot</code>
            </div>
          </div>
        </div>

        <!-- Progress Animations Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.progress.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.progress.title }}</span>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.progress.items.length + 2 }}</LTag>
          </div>
          <div class="section-content progress-demos">
            <div class="progress-demo">
              <div class="progress-header">
                <span class="progress-label">Pendulum (LLARS)</span>
                <code class="demo-code">.pendulum-bar</code>
              </div>
              <div class="pendulum-progress">
                <div class="pendulum-bar"></div>
              </div>
            </div>
            <div class="progress-demo">
              <div class="progress-header">
                <span class="progress-label">Indeterminate (Vuetify)</span>
                <code class="demo-code">v-progress-linear</code>
              </div>
              <v-progress-linear indeterminate color="primary" height="6" rounded />
            </div>
            <div class="progress-demo">
              <div class="progress-header">
                <span class="progress-label">Buffer (Vuetify)</span>
                <code class="demo-code">:buffer-value</code>
              </div>
              <v-progress-linear
                :model-value="bufferValue"
                :buffer-value="bufferBuffer"
                color="accent"
                height="6"
                rounded
              />
            </div>
          </div>
        </div>

        <!-- Transition Effects Section -->
        <div class="showcase-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">{{ allAnimations.transitions.icon }}</LIcon>
            <span class="section-title">{{ allAnimations.transitions.title }}</span>
            <LTag variant="gray" size="sm" class="ml-auto">{{ allAnimations.transitions.items.length }}</LTag>
          </div>
          <div class="section-content transition-demos">
            <LBtn variant="secondary" size="small" @click="toggleTransition">
              <LIcon size="16" class="mr-1">mdi-refresh</LIcon>
              Toggle
            </LBtn>
            <div class="transition-box-container">
              <transition v-for="trans in allAnimations.transitions.items" :key="trans.id" :name="trans.id">
                <LTooltip v-if="showTransition" :text="trans.usage">
                  <div class="transition-box" :class="`transition-box--${trans.id}`">
                    {{ trans.name }}
                  </div>
                </LTooltip>
              </transition>
            </div>
          </div>
        </div>

        <!-- Registry Info Section -->
        <div class="showcase-section registry-section">
          <div class="section-header">
            <LIcon size="18" class="mr-2">mdi-code-braces</LIcon>
            <span class="section-title">Animation Registry</span>
          </div>
          <div class="section-content">
            <v-alert type="info" variant="tonal" density="compact" class="mb-3">
              <template #title>Neue Animation hinzufügen</template>
              <ol class="registry-steps">
                <li>CSS @keyframes erstellen mit Präfix <code>llars-</code></li>
                <li>In <code>src/config/animationRegistry.js</code> registrieren</li>
                <li>Animation erscheint automatisch hier</li>
              </ol>
            </v-alert>
            <div class="registry-path">
              <LIcon size="14" class="mr-1">mdi-file-document</LIcon>
              <code>src/config/animationRegistry.js</code>
            </div>
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-3">
        <LTag variant="gray" size="sm">
          <LIcon size="14" class="mr-1">mdi-shield-account</LIcon>
          Nur für Admins
        </LTag>
        <v-spacer />
        <LBtn variant="secondary" @click="dialogOpen = false">Schließen</LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { allAnimations, getAnimationCount, getIconCount, getBrandIcons, getUIIcons, getTotalCount } from '@/config/animationRegistry'

const dialogOpen = defineModel({ type: Boolean, default: false })

// Total count from registry (animations + icons)
const animationCount = computed(() => getTotalCount())

// Separate brand and UI icons
const brandIcons = computed(() => getBrandIcons())
const uiIcons = computed(() => getUIIcons())

// Transition toggle
const showTransition = ref(true)
const toggleTransition = () => {
  showTransition.value = false
  setTimeout(() => {
    showTransition.value = true
  }, 50)
}

// Buffer progress animation
const bufferValue = ref(0)
const bufferBuffer = ref(0)
let bufferInterval = null

onMounted(() => {
  bufferInterval = setInterval(() => {
    bufferValue.value = (bufferValue.value + 5) % 100
    bufferBuffer.value = Math.min(100, bufferValue.value + 20)
  }, 200)
})

onUnmounted(() => {
  if (bufferInterval) {
    clearInterval(bufferInterval)
  }
})
</script>

<style scoped>
.animation-showcase {
  border-radius: 16px !important;
}

.showcase-section {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.showcase-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.section-title {
  font-weight: 600;
  font-size: 0.9rem;
}

.section-content {
  padding: 20px;
}

.section-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(var(--v-theme-primary), 0.05);
}

.animation-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Loading demos */
.loading-demos {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  gap: 24px;
  flex-wrap: wrap;
}

.demo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.demo-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.demo-code {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Icon demos */
.icon-demos {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 12px;
}

.icon-demo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.icon-wrapper {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  transition: all 0.2s ease;
  cursor: pointer;
}

.icon-wrapper:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  transform: scale(1.08);
}

.icon-wrapper--brand:hover {
  background: color-mix(in srgb, var(--brand-color, var(--llars-primary)) 15%, transparent);
}

.icon-label {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: center;
}

/* Static icons section */
.static-icons-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.static-icons-category {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-header {
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.category-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Spinner demos */
.spinner-demos {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.spinner-wrapper {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

/* Pulse dot */
.pulse-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--llars-accent);
  animation: pulse-animation 1.5s ease-in-out infinite;
}

@keyframes pulse-animation {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.7;
  }
}

/* Compile indicator */
.compile-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.14);
}

.compile-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgb(var(--v-theme-warning));
  animation: compile-pulse 1.2s ease-in-out infinite;
}

@keyframes compile-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.45);
    transform: scale(0.9);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(var(--v-theme-warning), 0);
    transform: scale(1);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0);
    transform: scale(0.9);
  }
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.4);
  animation: typing-bounce 1.4s ease-in-out infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-6px);
  }
}

/* Progress demos */
.progress-demos {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-demo {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-label {
  font-size: 0.8rem;
  font-weight: 500;
}

.pendulum-progress {
  height: 8px;
  border-radius: 999px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  overflow: hidden;
  position: relative;
}

.pendulum-bar {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 40%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--llars-primary), var(--llars-accent));
  animation: pendulum-swing 1.4s ease-in-out infinite;
}

@keyframes pendulum-swing {
  0%, 100% {
    left: -10%;
  }
  50% {
    left: 70%;
  }
}

/* Transition demos */
.transition-demos {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.transition-box-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  min-height: 50px;
}

.transition-box {
  padding: 12px 20px;
  border-radius: 8px;
  background: var(--llars-primary);
  color: white;
  font-weight: 500;
  font-size: 0.8rem;
  cursor: help;
}

.transition-box--scale {
  background: var(--llars-accent);
}

.transition-box--bounce {
  background: var(--llars-success);
}

/* Transitions */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s ease;
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.bounce-enter-active {
  animation: bounce-in 0.5s;
}

.bounce-leave-active {
  animation: bounce-in 0.3s reverse;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.15);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Registry Section */
.registry-section .section-content {
  padding: 16px;
}

.registry-steps {
  margin: 8px 0 0 16px;
  font-size: 0.85rem;
}

.registry-steps li {
  margin-bottom: 4px;
}

.registry-steps code {
  font-size: 0.8rem;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.registry-path {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.registry-path code {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.08);
}

@media (prefers-reduced-motion: reduce) {
  .pulse-dot,
  .compile-dot,
  .typing-dot,
  .pendulum-bar {
    animation: none;
  }
}
</style>
