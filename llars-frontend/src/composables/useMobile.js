/**
 * useMobile Composable
 *
 * Provides reactive mobile device detection and responsive breakpoint utilities.
 * Uses Vuetify's display composable and additional user agent detection.
 *
 * @example
 * const { isMobile, isTablet, isDesktop, isTouchDevice, platform } = useMobile()
 *
 * <template>
 *   <div v-if="isMobile">Mobile View</div>
 *   <div v-else>Desktop View</div>
 * </template>
 */

import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useDisplay } from 'vuetify'

export function useMobile() {
  const display = useDisplay()

  // Reactive window width for SSR compatibility
  const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
  const windowHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 768)

  // Breakpoints (aligned with Vuetify 3)
  const BREAKPOINTS = {
    xs: 0,      // Extra small devices (phones, < 600px)
    sm: 600,    // Small devices (tablets portrait, >= 600px)
    md: 960,    // Medium devices (tablets landscape, >= 960px)
    lg: 1264,   // Large devices (desktops, >= 1264px)
    xl: 1904    // Extra large devices (large desktops, >= 1904px)
  }

  // Update window dimensions on resize
  let resizeHandler = null

  onMounted(() => {
    if (typeof window !== 'undefined') {
      resizeHandler = () => {
        windowWidth.value = window.innerWidth
        windowHeight.value = window.innerHeight
      }
      window.addEventListener('resize', resizeHandler, { passive: true })
    }
  })

  onUnmounted(() => {
    if (resizeHandler && typeof window !== 'undefined') {
      window.removeEventListener('resize', resizeHandler)
    }
  })

  /**
   * Detect if the device is a touch device
   */
  const isTouchDevice = computed(() => {
    if (typeof window === 'undefined') return false
    return 'ontouchstart' in window ||
           navigator.maxTouchPoints > 0 ||
           // @ts-ignore
           navigator.msMaxTouchPoints > 0
  })

  /**
   * Detect platform from user agent
   */
  const platform = computed(() => {
    if (typeof navigator === 'undefined') return 'unknown'

    const ua = navigator.userAgent.toLowerCase()

    if (/iphone|ipod/.test(ua)) return 'iphone'
    if (/ipad/.test(ua)) return 'ipad'
    if (/android/.test(ua) && /mobile/.test(ua)) return 'android-phone'
    if (/android/.test(ua)) return 'android-tablet'
    if (/macintosh|mac os x/.test(ua)) return 'mac'
    if (/windows/.test(ua)) return 'windows'
    if (/linux/.test(ua)) return 'linux'

    return 'unknown'
  })

  /**
   * Check if the device is an iOS device (iPhone, iPad, iPod)
   */
  const isIOS = computed(() => {
    return ['iphone', 'ipad'].includes(platform.value) ||
           // iOS 13+ on iPad reports as Mac, check for touch
           (platform.value === 'mac' && isTouchDevice.value)
  })

  /**
   * Check if the device is an Android device
   */
  const isAndroid = computed(() => {
    return platform.value.startsWith('android')
  })

  /**
   * Mobile device detection (phones)
   * xs breakpoint or mobile user agent
   */
  const isMobile = computed(() => {
    // Vuetify xs breakpoint (< 600px)
    if (display.xs?.value) return true

    // User agent based detection for phones
    const mobileAgents = ['iphone', 'android-phone']
    if (mobileAgents.includes(platform.value)) return true

    // Fallback: very small width
    return windowWidth.value < BREAKPOINTS.sm
  })

  /**
   * Tablet device detection
   * sm/md breakpoint or tablet user agent
   */
  const isTablet = computed(() => {
    // Already classified as mobile phone
    if (isMobile.value) return false

    // Vuetify sm or md breakpoint with touch
    if ((display.sm?.value || display.md?.value) && isTouchDevice.value) return true

    // User agent based detection for tablets
    const tabletAgents = ['ipad', 'android-tablet']
    if (tabletAgents.includes(platform.value)) return true

    // Fallback: medium width with touch
    return windowWidth.value >= BREAKPOINTS.sm &&
           windowWidth.value < BREAKPOINTS.lg &&
           isTouchDevice.value
  })

  /**
   * Desktop device detection
   * lg+ breakpoint or no touch
   */
  const isDesktop = computed(() => {
    return !isMobile.value && !isTablet.value
  })

  /**
   * Small screen (mobile or tablet)
   * Useful for responsive layouts
   */
  const isSmallScreen = computed(() => {
    return isMobile.value || isTablet.value
  })

  /**
   * Current breakpoint name
   */
  const breakpoint = computed(() => {
    if (display.xs?.value) return 'xs'
    if (display.sm?.value) return 'sm'
    if (display.md?.value) return 'md'
    if (display.lg?.value) return 'lg'
    if (display.xl?.value) return 'xl'
    if (display.xxl?.value) return 'xxl'
    return 'md' // fallback
  })

  /**
   * Check if current width is at or below a breakpoint
   * @param {string} bp - Breakpoint name (xs, sm, md, lg, xl)
   */
  const isBreakpointOrSmaller = (bp) => {
    const order = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']
    const currentIndex = order.indexOf(breakpoint.value)
    const targetIndex = order.indexOf(bp)
    return currentIndex <= targetIndex
  }

  /**
   * Check if current width is at or above a breakpoint
   * @param {string} bp - Breakpoint name (xs, sm, md, lg, xl)
   */
  const isBreakpointOrLarger = (bp) => {
    const order = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']
    const currentIndex = order.indexOf(breakpoint.value)
    const targetIndex = order.indexOf(bp)
    return currentIndex >= targetIndex
  }

  /**
   * Orientation detection
   */
  const isPortrait = computed(() => windowHeight.value > windowWidth.value)
  const isLandscape = computed(() => windowWidth.value > windowHeight.value)

  /**
   * Safe area insets for notched devices (iPhone X+)
   * Returns CSS env() values or fallbacks
   */
  const safeAreaInsets = computed(() => {
    return {
      top: 'env(safe-area-inset-top, 0px)',
      right: 'env(safe-area-inset-right, 0px)',
      bottom: 'env(safe-area-inset-bottom, 0px)',
      left: 'env(safe-area-inset-left, 0px)'
    }
  })

  return {
    // Device type detection
    isMobile,
    isTablet,
    isDesktop,
    isSmallScreen,
    isTouchDevice,

    // Platform detection
    platform,
    isIOS,
    isAndroid,

    // Breakpoint utilities
    breakpoint,
    isBreakpointOrSmaller,
    isBreakpointOrLarger,

    // Dimensions
    windowWidth,
    windowHeight,
    isPortrait,
    isLandscape,

    // iOS safe areas
    safeAreaInsets,

    // Vuetify display (pass-through for advanced usage)
    display
  }
}
