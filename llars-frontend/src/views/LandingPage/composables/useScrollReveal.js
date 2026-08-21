/**
 * IntersectionObserver-based scroll reveal composable.
 * Adds a fade-up animation when elements enter the viewport.
 * Respects prefers-reduced-motion by making elements immediately visible.
 */
import { onMounted, onUnmounted } from 'vue'

export function useScrollReveal(options = {}) {
  const {
    threshold = 0.15,
    rootMargin = '0px 0px -40px 0px'
  } = options

  let observer = null

  /** Check if user prefers reduced motion */
  const prefersReducedMotion = () =>
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  onMounted(() => {
    if (prefersReducedMotion()) {
      // Immediately reveal all elements
      document.querySelectorAll('[data-reveal]').forEach(el => {
        el.classList.add('revealed')
      })
      return
    }

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.dataset.revealDelay || '0', 10)
            if (delay > 0) {
              setTimeout(() => entry.target.classList.add('revealed'), delay)
            } else {
              entry.target.classList.add('revealed')
            }
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold, rootMargin }
    )

    document.querySelectorAll('[data-reveal]').forEach(el => {
      observer.observe(el)
    })
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  })

  return { prefersReducedMotion }
}
