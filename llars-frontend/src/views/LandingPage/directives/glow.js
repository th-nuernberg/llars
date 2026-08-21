/**
 * v-glow — cursor-following specular highlight ("liquid glass").
 *
 * Schreibt nur drei CSS-Custom-Properties (--mx, --my, --glow-on) auf das
 * Element; das eigentliche Rendering macht die `.glow-surface`-CSS-Klasse
 * (radialer Gradient am Cursor, definiert unscoped in LandingPage.vue).
 * Muster von der Akteon-Landing-Page übernommen.
 *
 * Kein-Op bei prefers-reduced-motion. Handler werden in einer WeakMap
 * registriert, damit unmounted() exakt die gebundenen Listener entfernt.
 */
const registry = new WeakMap()

const prefersReducedMotion = () =>
  typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches

export const glow = {
  mounted(el) {
    if (prefersReducedMotion()) return
    const move = (e) => {
      const r = el.getBoundingClientRect()
      if (!r.width || !r.height) return
      el.style.setProperty('--mx', `${((e.clientX - r.left) / r.width) * 100}%`)
      el.style.setProperty('--my', `${((e.clientY - r.top) / r.height) * 100}%`)
    }
    const enter = () => el.style.setProperty('--glow-on', '1')
    const leave = () => el.style.setProperty('--glow-on', '0')
    el.addEventListener('pointermove', move, { passive: true })
    el.addEventListener('pointerenter', enter)
    el.addEventListener('pointerleave', leave)
    registry.set(el, { move, enter, leave })
  },
  unmounted(el) {
    const h = registry.get(el)
    if (!h) return
    el.removeEventListener('pointermove', h.move)
    el.removeEventListener('pointerenter', h.enter)
    el.removeEventListener('pointerleave', h.leave)
    registry.delete(el)
  },
}
