<template>
  <div
    ref="rootRef"
    class="paint-reveal"
    :class="{ in: isIn }"
    :style="{ '--ps-strength': strength }"
    aria-hidden="true"
  >
    <div class="ps-fly f-1" data-side="left"><div class="ps ps-1" /></div>
    <div class="ps-fly f-2" data-side="right"><div class="ps ps-2" /></div>
    <div class="ps-fly f-3" data-side="right"><div class="ps ps-3" /></div>
    <div class="ps-fly f-4" data-side="left"><div class="ps ps-4" /></div>
    <div class="ps-fly f-5" data-side="left"><div class="ps ps-5" /></div>
    <div class="ps-fly f-6" data-side="right"><div class="ps ps-6" /></div>
    <div class="ps-fly f-7" data-side="left"><div class="ps ps-7" /></div>
    <div class="ps-fly f-8" data-side="right"><div class="ps ps-8" /></div>
  </div>
</template>

<script setup>
/**
 * PaintStrokesReveal — animierter Blob-Hintergrund mit Fly-in.
 *
 * Zwei-Schichten-Struktur (Muster von der Akteon-Landing-Page), damit sich
 * zwei Transforms nicht in die Quere kommen:
 *  - äußere .ps-fly trägt den einmaligen Fly-in (translateX(±165%) → 0)
 *    mit gestaffelten transition-delays,
 *  - innere .ps trägt den endlosen Drift-Loop (identisch zu den
 *    Hero-Paint-Strokes).
 *
 * Props:
 *  - strength: multipliziert alle Blob-Opacities (dezent hinter Karten,
 *    kräftig als CTA-Finale).
 *  - trigger: 'visible' startet beim Scrollen in den Viewport (einmalig),
 *    'mount' sofort beim Mounten (für above-the-fold-Einsatz).
 *
 * Einsatz: als erstes Kind einer Section mit position:relative +
 * overflow:hidden; Inhalt dahinter auf z-index ≥ 1 legen.
 */
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  strength: { type: Number, default: 1 },
  trigger: {
    type: String,
    default: 'visible',
    validator: (v) => ['visible', 'mount'].includes(v),
  },
})

const rootRef = ref(null)
const isIn = ref(false)
let observer = null

const prefersReducedMotion = () =>
  typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches

onMounted(() => {
  // Reduced motion: kein Flug, Blobs stehen sofort an ihrer Ruheposition
  if (prefersReducedMotion() || props.trigger === 'mount') {
    // requestAnimationFrame stellt sicher, dass der Startzustand (off-screen)
    // erst gerendert wird, bevor .in die Transition auslöst.
    requestAnimationFrame(() => { isIn.value = true })
    return
  }

  observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        isIn.value = true
        observer?.disconnect()
        observer = null
        break
      }
    }
  }, { threshold: 0.25 })

  if (rootRef.value) observer.observe(rootRef.value)
})

onUnmounted(() => {
  observer?.disconnect()
  observer = null
})
</script>

<style scoped>
.paint-reveal {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

/* Äußere Hülle = einmaliger Fly-in mit langem, weichem Ease-out-Bogen */
.ps-fly {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: transform 1.25s cubic-bezier(0.16, 0.84, 0.4, 1), opacity 0.9s ease;
  will-change: transform, opacity;
}

.ps-fly[data-side='left'] { transform: translateX(-165%); }
.ps-fly[data-side='right'] { transform: translateX(165%); }

.paint-reveal.in .ps-fly {
  transform: translateX(0);
  opacity: 1;
}

/* Gestaffelte Delays → kaskadierender Einflug */
.paint-reveal.in .f-1 { transition-delay: 0s; }
.paint-reveal.in .f-2 { transition-delay: 0.08s; }
.paint-reveal.in .f-3 { transition-delay: 0.16s; }
.paint-reveal.in .f-4 { transition-delay: 0.1s; }
.paint-reveal.in .f-5 { transition-delay: 0.22s; }
.paint-reveal.in .f-6 { transition-delay: 0.14s; }
.paint-reveal.in .f-7 { transition-delay: 0.28s; }
.paint-reveal.in .f-8 { transition-delay: 0.2s; }

/* Innerer Blob = endloser Drift (LLARS-Pastellpalette) */
.ps {
  position: absolute;
  filter: blur(70px);
  border-radius: 60% 40% 55% 45% / 55% 45% 60% 40%;
  will-change: transform;
}

.ps-1 { background: rgba(176, 202, 151, 0.7);  top: -16%; left: -10%;  width: 42%; height: 42%; opacity: calc(0.34 * var(--ps-strength, 1)); animation: psDrift1 26s ease-in-out infinite; }
.ps-2 { background: rgba(209, 188, 138, 0.65); top: -22%; right: -18%; width: 55%; height: 55%; opacity: calc(0.4 * var(--ps-strength, 1)); animation: psDrift2 30s ease-in-out infinite; }
.ps-3 { background: rgba(136, 196, 200, 0.6);  top: 22%;  right: -16%; width: 44%; height: 50%; opacity: calc(0.32 * var(--ps-strength, 1)); animation: psDrift3 28s ease-in-out infinite; }
.ps-4 { background: rgba(232, 200, 122, 0.55); top: 35%;  left: -18%;  width: 48%; height: 50%; opacity: calc(0.36 * var(--ps-strength, 1)); animation: psDrift4 32s ease-in-out infinite; }
.ps-5 { background: rgba(152, 212, 187, 0.6);  top: -5%;  left: 35%;   width: 38%; height: 38%; opacity: calc(0.28 * var(--ps-strength, 1)); animation: psDrift5 27s ease-in-out infinite; }
.ps-6 { background: rgba(168, 197, 226, 0.55); top: 30%;  left: 28%;   width: 50%; height: 45%; opacity: calc(0.34 * var(--ps-strength, 1)); animation: psDrift6 34s ease-in-out infinite; }
.ps-7 { background: rgba(232, 160, 135, 0.5);  bottom: -22%; left: -8%; width: 50%; height: 48%; opacity: calc(0.28 * var(--ps-strength, 1)); animation: psDrift7 36s ease-in-out infinite; }
.ps-8 { background: rgba(201, 168, 226, 0.45); bottom: -18%; right: 10%; width: 35%; height: 35%; opacity: calc(0.3 * var(--ps-strength, 1)); animation: psDrift8 31s ease-in-out infinite; }

/* Dark mode: stärkerer Blur, reduzierte Opacity — Blobs glühen aus dem
 * Dunkel statt zu decken. .dark-mode kommt vom .landing-page-Root. */
.dark-mode .ps {
  filter: blur(85px);
}

.dark-mode .ps-1 { background: rgba(140, 170, 120, 0.5); }
.dark-mode .ps-2 { background: rgba(180, 160, 110, 0.45); }
.dark-mode .ps-3 { background: rgba(100, 160, 165, 0.4); }
.dark-mode .ps-4 { background: rgba(200, 170, 90, 0.35); }
.dark-mode .ps-5 { background: rgba(120, 180, 155, 0.45); }
.dark-mode .ps-6 { background: rgba(135, 165, 195, 0.4); }
.dark-mode .ps-7 { background: rgba(200, 130, 105, 0.3); }
.dark-mode .ps-8 { background: rgba(170, 140, 195, 0.3); }

@keyframes psDrift1 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(3%, 5%) scale(1.05); } 66% { transform: translate(-2%, 3%) scale(0.97); } }
@keyframes psDrift2 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(-4%, 3%) scale(1.03); } 66% { transform: translate(2%, -4%) scale(1.02); } }
@keyframes psDrift3 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(5%, -3%) scale(1.04); } 66% { transform: translate(2%, 4%) scale(0.97); } }
@keyframes psDrift4 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(-3%, 4%) scale(1.02); } 66% { transform: translate(-5%, -2%) scale(1.05); } }
@keyframes psDrift5 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(4%, -4%) scale(1.03); } 66% { transform: translate(-3%, -2%) scale(0.98); } }
@keyframes psDrift6 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(-2%, -5%) scale(1.04); } 66% { transform: translate(3%, 3%) scale(1.01); } }
@keyframes psDrift7 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(6%, 4%) scale(1.06); } 66% { transform: translate(-4%, -3%) scale(0.96); } }
@keyframes psDrift8 { 0%, 100% { transform: translate(0, 0) scale(1); } 33% { transform: translate(-5%, -3%) scale(1.05); } 66% { transform: translate(4%, 2%) scale(0.98); } }

@media (prefers-reduced-motion: reduce) {
  .ps-fly {
    transform: none !important;
    opacity: 1;
    transition: none !important;
  }

  .ps {
    animation: none !important;
  }
}
</style>
