/**
 * Ambient cursor-glow effect for the Hero section.
 * Renders a soft radial gradient that follows the mouse with lerp smoothing.
 * Disabled on touch devices and when prefers-reduced-motion is active.
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useCursorGlow(containerRef) {
  const glowX = ref(50)
  const glowY = ref(50)

  let targetX = 50
  let targetY = 50
  let animationId = null
  let active = false

  const LERP_FACTOR = 0.08

  function lerp(current, target, factor) {
    return current + (target - current) * factor
  }

  function onMouseMove(e) {
    const el = containerRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    targetX = ((e.clientX - rect.left) / rect.width) * 100
    targetY = ((e.clientY - rect.top) / rect.height) * 100
  }

  function animate() {
    glowX.value = lerp(glowX.value, targetX, LERP_FACTOR)
    glowY.value = lerp(glowY.value, targetY, LERP_FACTOR)
    animationId = requestAnimationFrame(animate)
  }

  onMounted(() => {
    // Skip on touch-only devices or reduced motion
    const isTouch = typeof window !== 'undefined' &&
      window.matchMedia('(hover: none)').matches
    const reducedMotion = typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (isTouch || reducedMotion) return

    active = true
    const el = containerRef.value
    if (el) {
      el.addEventListener('mousemove', onMouseMove, { passive: true })
    }
    animationId = requestAnimationFrame(animate)
  })

  onUnmounted(() => {
    if (animationId) cancelAnimationFrame(animationId)
    if (active && containerRef.value) {
      containerRef.value.removeEventListener('mousemove', onMouseMove)
    }
  })

  return { glowX, glowY }
}
