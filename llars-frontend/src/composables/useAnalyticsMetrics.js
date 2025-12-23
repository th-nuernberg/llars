import { onMounted, onUnmounted, watch } from 'vue'
import { matomoTrackEvent } from '@/plugins/llars-metrics'

const nowMs = () => (typeof performance !== 'undefined' ? performance.now() : Date.now())

const clampNumber = (value, min = 0) => Math.max(min, Number(value) || 0)

const resolveDimensions = (dimensions) => {
  if (typeof dimensions === 'function') return dimensions() || {}
  if (dimensions && typeof dimensions === 'object' && 'value' in dimensions) {
    return dimensions.value || {}
  }
  return dimensions || {}
}

const resolveValue = (value) => {
  if (typeof value === 'function') return value()
  if (value && typeof value === 'object' && 'value' in value) {
    return value.value
  }
  return value
}

export const useActiveDuration = ({
  category,
  action = 'active_time',
  name,
  dimensions,
  idleMs = 60_000,
  minMs = 1_000
} = {}) => {
  let activeMs = 0
  let activeSince = null
  let lastActivity = nowMs()
  let idleTimer = null
  let isVisible = true
  let isFocused = true

  const pause = () => {
    if (activeSince === null) return
    activeMs += nowMs() - activeSince
    activeSince = null
  }

  const resume = () => {
    if (activeSince !== null) return
    activeSince = nowMs()
  }

  const flush = (reason = 'unmount') => {
    pause()
    if (activeMs >= minMs) {
      matomoTrackEvent(category, action, resolveValue(name), Math.round(activeMs), {
        dimensions: { ...resolveDimensions(dimensions), reason }
      })
    }
    activeMs = 0
  }

  const onVisibilityChange = () => {
    isVisible = typeof document !== 'undefined' ? document.visibilityState === 'visible' : true
    if (!isVisible) {
      pause()
      return
    }
    if (isFocused) {
      resume()
    }
  }

  const onFocus = () => {
    isFocused = true
    if (isVisible) {
      resume()
    }
  }

  const onBlur = () => {
    isFocused = false
    pause()
  }

  const onActivity = () => {
    lastActivity = nowMs()
    if (activeSince === null && isVisible && isFocused) {
      resume()
    }
  }

  const checkIdle = () => {
    if (!activeSince) return
    if (nowMs() - lastActivity >= idleMs) {
      pause()
    }
  }

  onMounted(() => {
    lastActivity = nowMs()
    if (typeof document !== 'undefined') {
      isVisible = document.visibilityState === 'visible'
      document.addEventListener('visibilitychange', onVisibilityChange)
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('focus', onFocus)
      window.addEventListener('blur', onBlur)
      window.addEventListener('keydown', onActivity, true)
      window.addEventListener('pointerdown', onActivity, true)
      window.addEventListener('scroll', onActivity, true)
    }
    if (isVisible && isFocused) {
      resume()
    }
    if (typeof window !== 'undefined') {
      idleTimer = window.setInterval(checkIdle, Math.max(5_000, clampNumber(idleMs / 2)))
    }
  })

  onUnmounted(() => {
    flush('unmount')
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('focus', onFocus)
      window.removeEventListener('blur', onBlur)
      window.removeEventListener('keydown', onActivity, true)
      window.removeEventListener('pointerdown', onActivity, true)
      window.removeEventListener('scroll', onActivity, true)
      if (idleTimer) {
        window.clearInterval(idleTimer)
      }
    }
  })

  return {
    flush,
    getActiveMs: () => activeMs + (activeSince ? nowMs() - activeSince : 0)
  }
}

export const useTypingMetrics = ({
  category,
  name,
  dimensions,
  burstIdleMs = 1_200,
  minBurstMs = 200,
  minChars = 3
} = {}) => {
  let burstStart = null
  let burstChars = 0
  let burstEvents = 0
  let totalChars = 0
  let totalBursts = 0
  let totalDuration = 0
  let burstTimer = null

  const endBurst = (reason = 'idle') => {
    if (burstStart === null) return
    const duration = Math.max(1, nowMs() - burstStart)
    const shouldEmit = duration >= minBurstMs && burstChars >= minChars
    if (shouldEmit) {
      totalBursts += 1
      totalDuration += duration
      const wpm = Math.round((burstChars / 5) / (duration / 60_000))
      const label = `${resolveValue(name) || 'typing'}|chars:${burstChars}|wpm:${wpm}|events:${burstEvents}|${reason}`
      matomoTrackEvent(category, 'typing_burst', label, Math.round(duration), {
        dimensions: resolveDimensions(dimensions)
      })
    }
    burstStart = null
    burstChars = 0
    burstEvents = 0
    if (burstTimer) {
      window.clearTimeout(burstTimer)
      burstTimer = null
    }
  }

  const recordInput = (charsDelta) => {
    const delta = clampNumber(charsDelta, 0)
    if (delta <= 0) return
    totalChars += delta
    burstChars += delta
    burstEvents += 1
    if (burstStart === null) {
      burstStart = nowMs()
    }
    if (burstTimer) {
      window.clearTimeout(burstTimer)
    }
    burstTimer = window.setTimeout(() => endBurst('idle'), burstIdleMs)
  }

  const flush = () => {
    endBurst('flush')
    if (totalChars <= 0 || totalDuration <= 0) return
    const avgWpm = Math.round((totalChars / 5) / (totalDuration / 60_000))
    const label = `${resolveValue(name) || 'typing'}|chars:${totalChars}|bursts:${totalBursts}|wpm:${avgWpm}`
    matomoTrackEvent(category, 'typing_total', label, Math.round(totalDuration), {
      dimensions: resolveDimensions(dimensions)
    })
    totalChars = 0
    totalBursts = 0
    totalDuration = 0
  }

  onUnmounted(() => {
    flush()
  })

  return { recordInput, flush }
}

export const useVisibilityTracker = ({
  category,
  action = 'visible_time',
  nameBuilder = (id) => String(id),
  minMs = 2_000,
  threshold = 0.4,
  dimensions
} = {}) => {
  const items = new Map()
  let observer = null
  let isVisible = true

  const ensureObserver = () => {
    if (observer || typeof window === 'undefined') return
    observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const id = entry.target?.dataset?.metricsId
        if (!id || !items.has(id)) return
        const item = items.get(id)
        const nowVisible = entry.isIntersecting && entry.intersectionRatio >= threshold
        item.visible = nowVisible
        if (!isVisible) return
        if (nowVisible) {
          if (item.startedAt === null) {
            item.startedAt = nowMs()
          }
        } else if (item.startedAt !== null) {
          item.totalMs += nowMs() - item.startedAt
          item.startedAt = null
        }
      })
    }, { threshold })
  }

  const stopItem = (item) => {
    if (item.startedAt !== null) {
      item.totalMs += nowMs() - item.startedAt
      item.startedAt = null
    }
  }

  const pauseAll = () => {
    isVisible = false
    items.forEach((item) => stopItem(item))
  }

  const resumeAll = () => {
    isVisible = true
    items.forEach((item) => {
      if (item.visible && item.startedAt === null) {
        item.startedAt = nowMs()
      }
    })
  }

  const onVisibilityChange = () => {
    if (typeof document === 'undefined') return
    if (document.visibilityState === 'visible') {
      resumeAll()
    } else {
      pauseAll()
    }
  }

  const register = (id, el, extraDimensions = {}) => {
    if (!id) return
    if (!el) {
      unregister(id)
      return
    }
    ensureObserver()
    el.dataset.metricsId = String(id)
    const existing = items.get(String(id))
    if (!existing) {
      items.set(String(id), {
        id: String(id),
        totalMs: 0,
        startedAt: null,
        visible: false,
        dimensions: extraDimensions,
        el
      })
    } else {
      existing.dimensions = extraDimensions
      if (existing.el && existing.el !== el) {
        observer?.unobserve(existing.el)
      }
      existing.el = el
    }
    observer?.observe(el)
  }

  const unregister = (id) => {
    const key = String(id)
    const item = items.get(key)
    if (!item) return
    stopItem(item)
    if (item.el) {
      observer?.unobserve(item.el)
    }
    items.delete(key)
  }

  const flush = () => {
    items.forEach((item) => {
      stopItem(item)
      if (item.totalMs >= minMs) {
        const label = nameBuilder(item.id)
        matomoTrackEvent(category, action, label, Math.round(item.totalMs), {
          dimensions: { ...resolveDimensions(dimensions), ...item.dimensions }
        })
      }
    })
    items.clear()
  }

  onMounted(() => {
    if (typeof document !== 'undefined') {
      isVisible = document.visibilityState === 'visible'
      document.addEventListener('visibilitychange', onVisibilityChange)
    }
  })

  onUnmounted(() => {
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
    observer?.disconnect?.()
    flush()
  })

  return { register, unregister, flush }
}

export const useScrollDepth = (containerRef, {
  category,
  action = 'scroll_depth',
  name,
  thresholds = [0.25, 0.5, 0.75, 1],
  dimensions
} = {}) => {
  const seen = new Set()
  let ticking = false
  let currentEl = null

  const handleScroll = () => {
    if (ticking || !currentEl) return
    ticking = true
    window.requestAnimationFrame(() => {
      ticking = false
      const { scrollTop, clientHeight, scrollHeight } = currentEl
      if (!scrollHeight || scrollHeight <= clientHeight) return
      const depth = (scrollTop + clientHeight) / scrollHeight
      thresholds.forEach((threshold) => {
        if (depth >= threshold && !seen.has(threshold)) {
          seen.add(threshold)
          matomoTrackEvent(category, action, resolveValue(name), Math.round(threshold * 100), {
            dimensions: resolveDimensions(dimensions)
          })
        }
      })
    })
  }

  const attach = (el) => {
    if (!el) return
    currentEl = el
    el.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
  }

  const detach = (el) => {
    if (!el) return
    el.removeEventListener('scroll', handleScroll)
    if (currentEl === el) {
      currentEl = null
    }
  }

  watch(containerRef, (next, prev) => {
    if (prev) detach(prev)
    if (next) attach(next)
  })

  onMounted(() => {
    if (containerRef?.value) {
      attach(containerRef.value)
    }
  })

  onUnmounted(() => {
    if (currentEl) {
      detach(currentEl)
    }
  })

  const reset = () => {
    seen.clear()
  }

  return { reset }
}
