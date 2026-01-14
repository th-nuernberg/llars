/**
 * Server-Authoritative Wizard Session Composable
 *
 * Manages the Chatbot Builder Wizard state via server-authoritative session architecture.
 * All state is stored in Redis on the server; the client only receives and displays state.
 * Sessions persist across browser closes, reconnections, and server restarts.
 *
 * Key Features:
 * - Server is single source of truth (no sessionStorage)
 * - Time tracking is computed server-side
 * - Socket.IO for real-time updates
 * - Automatic reconnection with state recovery
 * - Heartbeat to keep session active
 *
 * Build Status Flow:
 *   draft -> crawling -> embedding -> configuring -> ready
 *                  \-> error (from any state)
 *                  \-> paused (from crawling/embedding)
 */

import { ref, computed, readonly, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'
import { logI18n } from '@/utils/logI18n'

// Valid build status values
export const BUILD_STATUS = {
  DRAFT: 'draft',
  CRAWLING: 'crawling',
  EMBEDDING: 'embedding',
  CONFIGURING: 'configuring',
  READY: 'ready',
  ERROR: 'error',
  PAUSED: 'paused'
}

// Step definitions
export const WIZARD_STEPS = {
  URL_INPUT: 1,
  CRAWLING: 2,
  EMBEDDING: 3,
  CONFIGURATION: 4,
  COMPLETE: 5
}

// Status to step mapping (matches backend)
const STATUS_TO_STEP = {
  draft: 1,
  crawling: 2,
  embedding: 3,
  configuring: 4,
  ready: 5,
  error: null,
  paused: null
}

export function useWizardSession() {
  // ===== Server State (readonly, updated via Socket.IO) =====
  const session = ref(null)
  const progress = ref({})
  const elapsedTime = ref({ crawl: 0, embed: 0, total: 0 })

  // ===== Connection State =====
  const connected = ref(false)
  const syncing = ref(false)
  const error = ref(null)

  // ===== Local State (for UI) =====
  const loading = ref(false)
  const currentStep = ref(WIZARD_STEPS.URL_INPUT)

  // ===== Field Generation State =====
  const generating = ref({
    name: false,
    display_name: false,
    system_prompt: false,
    welcome_message: false,
    icon: false,
    color: false
  })

  // ===== Socket.IO Setup =====
  let socket = null
  let heartbeatInterval = null
  let localTimerInterval = null

  // ===== Computed Properties =====
  const chatbotId = computed(() => session.value?.chatbot_id)
  const buildStatus = computed(() => session.value?.build_status || BUILD_STATUS.DRAFT)
  const serverStep = computed(() => session.value?.current_step || 1)
  const crawlerJobId = computed(() => session.value?.crawler_job_id)
  const collectionId = computed(() => session.value?.collection_id)
  const sourceUrl = computed(() => session.value?.source_url)

  const wizardData = computed(() => {
    if (!session.value?.wizard_data) return {}
    return typeof session.value.wizard_data === 'string'
      ? JSON.parse(session.value.wizard_data)
      : session.value.wizard_data
  })

  const crawlerConfig = computed(() => {
    if (!session.value?.crawler_config) return {}
    return typeof session.value.crawler_config === 'string'
      ? JSON.parse(session.value.crawler_config)
      : session.value.crawler_config
  })

  const isProcessing = computed(() => {
    return [BUILD_STATUS.CRAWLING, BUILD_STATUS.EMBEDDING].includes(buildStatus.value)
  })

  const isCrawling = computed(() => buildStatus.value === BUILD_STATUS.CRAWLING)
  const isEmbedding = computed(() => buildStatus.value === BUILD_STATUS.EMBEDDING)
  const isConfiguring = computed(() => buildStatus.value === BUILD_STATUS.CONFIGURING)
  const isReady = computed(() => buildStatus.value === BUILD_STATUS.READY)
  const hasError = computed(() => buildStatus.value === BUILD_STATUS.ERROR)
  const isPaused = computed(() => buildStatus.value === BUILD_STATUS.PAUSED)

  const crawlProgress = computed(() => ({
    stage: progress.value.crawl_stage || 'idle',
    urlsTotal: progress.value.urls_total || 0,
    urlsCompleted: progress.value.urls_completed || 0,
    documentsCreated: progress.value.documents_created || 0,
    currentUrl: progress.value.current_url || ''
  }))

  const embeddingProgress = computed(() => ({
    progress: progress.value.embedding_progress || 0,
    documentsTotal: progress.value.documents_total || 0,
    documentsProcessed: progress.value.documents_processed || 0,
    currentDocument: progress.value.current_document || ''
  }))

  const crawlProgressPercent = computed(() => {
    const total = crawlProgress.value.urlsTotal
    if (total === 0) return 0
    return Math.min(100, Math.round((crawlProgress.value.urlsCompleted / total) * 100))
  })

  const embeddingProgressPercent = computed(() => {
    return Math.min(100, Math.round(embeddingProgress.value.progress || 0))
  })

  // Local elapsed timer (interpolated between server updates)
  const localElapsed = ref(0)

  // ===== Socket.IO Event Handlers =====
  function setupSocketListeners() {
    socket = getSocket()
    if (!socket) {
      logI18n('error', 'logs.wizardSession.socketUnavailable')
      return
    }

    socket.on('wizard:state', handleStateUpdate)
    socket.on('wizard:progress', handleProgressUpdate)
    socket.on('wizard:status_changed', handleStatusChanged)
    socket.on('wizard:elapsed_time', handleElapsedTime)
    socket.on('wizard:error', handleError)
    socket.on('connect', handleReconnect)
  }

  function removeSocketListeners() {
    if (!socket) return
    socket.off('wizard:state', handleStateUpdate)
    socket.off('wizard:progress', handleProgressUpdate)
    socket.off('wizard:status_changed', handleStatusChanged)
    socket.off('wizard:elapsed_time', handleElapsedTime)
    socket.off('wizard:error', handleError)
    socket.off('connect', handleReconnect)
  }

  function handleStateUpdate(data) {
    logI18n('log', 'logs.wizardSession.stateUpdate', data)
    if (data.session) {
      session.value = data.session
      updateStepFromStatus()
    }
    if (data.progress) {
      progress.value = data.progress
    }
    if (data.elapsed_time) {
      elapsedTime.value = data.elapsed_time
      localElapsed.value = data.elapsed_time.total || 0
    }
  }

  function handleProgressUpdate(data) {
    logI18n('log', 'logs.wizardSession.progressUpdate', data)
    if (data.progress) {
      progress.value = { ...progress.value, ...data.progress }
    }
    if (data.elapsed_time) {
      elapsedTime.value = data.elapsed_time
      localElapsed.value = data.elapsed_time.total || 0
    }
  }

  function handleStatusChanged(data) {
    logI18n('log', 'logs.wizardSession.statusChanged', data)
    if (session.value) {
      session.value = { ...session.value, build_status: data.status }
      if (data.step !== null) {
        session.value.current_step = data.step
      }
    }
    if (data.elapsed_time) {
      elapsedTime.value = data.elapsed_time
      localElapsed.value = data.elapsed_time.total || 0
    }
    updateStepFromStatus()
  }

  function handleElapsedTime(data) {
    if (data.elapsed_time) {
      elapsedTime.value = data.elapsed_time
      localElapsed.value = data.elapsed_time.total || 0
    } else if (typeof data === 'object') {
      elapsedTime.value = data
      localElapsed.value = data.total || 0
    }
  }

  function handleError(data) {
    logI18n('error', 'logs.wizardSession.error', data)
    error.value = data.message || 'Unknown error'
  }

  async function handleReconnect() {
    logI18n('log', 'logs.wizardSession.socketReconnected')
    if (chatbotId.value) {
      socket.emit('wizard:join_session', { chatbot_id: chatbotId.value })
    }
  }

  function updateStepFromStatus() {
    const status = buildStatus.value
    const step = STATUS_TO_STEP[status]
    if (step !== null && step !== undefined) {
      currentStep.value = step
    }
  }

  // ===== API Actions =====

  /**
   * Create a new wizard session for a URL.
   * @param {string} url - The URL to crawl
   * @returns {Promise<number>} - The chatbot ID
   */
  async function createSession(url) {
    syncing.value = true
    error.value = null
    try {
      const response = await axios.post('/api/chatbots/wizard', { url })
      const newChatbotId = response.data.chatbot_id

      // Join the session room
      await joinSession(newChatbotId)

      return newChatbotId
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    } finally {
      syncing.value = false
    }
  }

  /**
   * Join an existing wizard session.
   * @param {number} id - The chatbot ID
   */
  async function joinSession(id) {
    syncing.value = true
    error.value = null
    try {
      const response = await axios.post(`/api/chatbots/wizard/sessions/${id}/join`)

      session.value = response.data.session
      progress.value = response.data.progress || {}
      elapsedTime.value = response.data.elapsed_time || { crawl: 0, embed: 0, total: 0 }
      localElapsed.value = elapsedTime.value.total || 0

      // Update step based on status
      updateStepFromStatus()

      // Join Socket.IO room
      if (socket) {
        socket.emit('wizard:join_session', { chatbot_id: id })
      }

      connected.value = true
      startHeartbeat()
      startLocalTimer()

    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    } finally {
      syncing.value = false
    }
  }

  /**
   * Get all active wizard sessions for the current user.
   * @returns {Promise<Array>} - List of sessions
   */
  async function getUserSessions() {
    try {
      const response = await axios.get('/api/chatbots/wizard/sessions')
      return response.data.sessions || []
    } catch (e) {
      logI18n('error', 'logs.wizardSession.userSessionsLoadFailed', e)
      return []
    }
  }

  /**
   * Start the crawl process.
   * @param {Object} config - Crawler configuration
   */
  async function startCrawl(config) {
    if (!chatbotId.value) {
      throw new Error('No active session')
    }

    loading.value = true
    error.value = null
    try {
      const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/crawl`, config)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  /**
   * Update wizard configuration data.
   * @param {Object} data - Wizard data to update
   */
  async function updateWizardData(data) {
    if (!chatbotId.value) {
      throw new Error('No active session')
    }

    try {
      await axios.patch(`/api/chatbots/wizard/sessions/${chatbotId.value}/data`, data)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    }
  }

  /**
   * Pause the current build process.
   */
  async function pauseSession() {
    if (!chatbotId.value) return

    try {
      await axios.post(`/api/chatbots/${chatbotId.value}/wizard/pause`)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    }
  }

  /**
   * Resume a paused build.
   */
  async function resumeBuild() {
    if (!chatbotId.value) return

    try {
      await axios.post(`/api/chatbots/${chatbotId.value}/resume-build`)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    }
  }

  /**
   * Finalize the chatbot and complete the wizard.
   * @param {Object} config - Final configuration
   */
  async function finalizeSession(config) {
    if (!chatbotId.value) {
      throw new Error('No active session')
    }

    loading.value = true
    try {
      await axios.post(`/api/chatbots/${chatbotId.value}/wizard/finalize`, config)
      leaveSession()
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  /**
   * Cancel the wizard and delete the chatbot.
   */
  async function cancelSession() {
    if (!chatbotId.value) return

    try {
      await axios.post(`/api/chatbots/${chatbotId.value}/cancel-build`)
      leaveSession()
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      throw e
    }
  }

  /**
   * Leave the session room (session continues on server).
   */
  function leaveSession() {
    if (socket && chatbotId.value) {
      socket.emit('wizard:leave_session', { chatbot_id: chatbotId.value })
    }
    stopHeartbeat()
    stopLocalTimer()
    session.value = null
    progress.value = {}
    elapsedTime.value = { crawl: 0, embed: 0, total: 0 }
    localElapsed.value = 0
    connected.value = false
    currentStep.value = WIZARD_STEPS.URL_INPUT
  }

  // ===== Heartbeat =====
  function startHeartbeat() {
    stopHeartbeat()
    heartbeatInterval = setInterval(() => {
      if (socket && chatbotId.value) {
        socket.emit('wizard:heartbeat', { chatbot_id: chatbotId.value })
      }
    }, 30000) // 30 seconds
  }

  function stopHeartbeat() {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
  }

  // ===== Local Timer (for smooth UX between server updates) =====
  function startLocalTimer() {
    stopLocalTimer()
    localTimerInterval = setInterval(() => {
      if (isProcessing.value) {
        localElapsed.value += 1
      }
    }, 1000)
  }

  function stopLocalTimer() {
    if (localTimerInterval) {
      clearInterval(localTimerInterval)
      localTimerInterval = null
    }
  }

  // ===== Field Generation =====
  const setGenerating = (field, isGenerating) => {
    if (field in generating.value) {
      generating.value[field] = isGenerating
    }
  }

  const isAnyFieldGenerating = computed(() => {
    return Object.values(generating.value).some(v => v)
  })

  // ===== Navigation =====
  const canNavigateToStep = (step) => {
    if (step === WIZARD_STEPS.URL_INPUT) return true
    if (!chatbotId.value) return false
    if (step >= WIZARD_STEPS.CRAWLING && step <= WIZARD_STEPS.CONFIGURATION) return true
    if (step === WIZARD_STEPS.COMPLETE) return buildStatus.value === BUILD_STATUS.READY
    return false
  }

  const navigateToStep = (step) => {
    if (!canNavigateToStep(step)) return false
    currentStep.value = step
    return true
  }

  // ===== Lifecycle =====
  onMounted(() => {
    setupSocketListeners()
  })

  onUnmounted(() => {
    removeSocketListeners()
    stopHeartbeat()
    stopLocalTimer()
    // Don't leave session on unmount - session persists on server
  })

  // Watch for status changes to update step
  watch(buildStatus, () => {
    updateStepFromStatus()
  })

  return {
    // Server State (readonly)
    session: readonly(session),
    progress: readonly(progress),
    elapsedTime: readonly(elapsedTime),
    localElapsed: readonly(localElapsed),

    // Connection State
    connected,
    syncing,
    error,
    loading,

    // Computed from session
    chatbotId,
    buildStatus,
    currentStep,
    crawlerJobId,
    collectionId,
    sourceUrl,
    wizardData,
    crawlerConfig,

    // Status checks
    isProcessing,
    isCrawling,
    isEmbedding,
    isConfiguring,
    isReady,
    hasError,
    isPaused,

    // Progress
    crawlProgress,
    embeddingProgress,
    crawlProgressPercent,
    embeddingProgressPercent,

    // Field Generation
    generating: readonly(generating),
    setGenerating,
    isAnyFieldGenerating,

    // Navigation
    canNavigateToStep,
    navigateToStep,

    // API Actions
    createSession,
    joinSession,
    getUserSessions,
    startCrawl,
    updateWizardData,
    pauseSession,
    resumeBuild,
    finalizeSession,
    cancelSession,
    leaveSession
  }
}

export default useWizardSession
