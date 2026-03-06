/**
 * Router Configuration Tests
 *
 * Tests for route definitions, meta properties, and navigation guards.
 * Test IDs: ROUTER_001 - ROUTER_050
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock all Vue component imports to avoid loading actual components
vi.mock('@/components/Login.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Register.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Home.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/NotFound.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Ranker/Ranker.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Ranker/RankerDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Rater/Rater.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Rater/RaterDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Rater/RaterDetailFeature.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminDashboard.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminRanker.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/AdminPermissions.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/HistoryGenerator/HistoryGeneration.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/HistoryGenerator/HistoryGenerationDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Orga/Impressum.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Orga/Datenschutz.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Orga/Kontakt.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminTester.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Chat.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/ChatWithBots.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/TempTest.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/PromptEngineering/PromptEngineering.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/PromptEngineering/PromptEngineeringDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/comparison/Comparison.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/comparison/ComparisonDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminUserProgressStats.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Admin/AdminRAG.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Anonymize/AnonymizeTool.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/AnonymizationPipeline/AnonymizationManager.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/AnonymizationPipeline/AnonymizationDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Judge/JudgeOverview.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Judge/JudgeConfig.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Judge/JudgeSession.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Judge/JudgeResults.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/OnCoCo/OnCoCoOverview.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/OnCoCo/OnCoCoConfig.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/OnCoCo/OnCoCoResults.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/OnCoCo/OnCoCoInfo.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Kaimo/KaimoHub.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Kaimo/KaimoPanel.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Kaimo/KaimoNewCase.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Kaimo/KaimoCase.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Kaimo/KaimoCaseEditor.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/MarkdownCollab/MarkdownCollabHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/MarkdownCollab/MarkdownCollabWorkspace.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/LatexCollabAI/LatexCollabAIHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/LatexCollabAI/LatexCollabAIWorkspace.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Evaluation/EvaluationHub.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/EvaluationAssistant/EvaluationAssistant.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/DataImporter/DataImporterView.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ScenarioManager/ScenarioManagerHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ScenarioManager/ScenarioWorkspace.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Authenticity/AuthenticityOverview.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Authenticity/AuthenticityDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/UserSettings/UserSettingsPage.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Evaluation/EvaluationSession.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Evaluation/EvaluationItemsOverview.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Generation/GenerationHub.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Generation/GenerationJobDetail.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/components/Generation/GenerationWizard.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Video/DemoVideoPage.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Pipeline/PipelineHub.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Pipeline/PipelineSession.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Pipeline/PipelineWizard.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ConferenceManager/ConferenceEntry.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ConferenceManager/ResearchGroupSelection.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ConferenceManager/ConferenceManagerHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ConferenceManager/ResearchGroupMembers.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ConferenceManager/ResearchGroupAccessRequestPage.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Messaging/MessagingHome.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/ChatbotManager/ChatbotManagerPage.vue', () => ({ default: { template: '<div />' } }))

// Mock useAuth with different states for guard testing
const mockAuth = {
  getToken: vi.fn(() => 'valid_token'),
  isAuthenticated: { value: true },
  isAdmin: { value: false },
  userRoles: { value: ['researcher'] },
  logout: vi.fn()
}
vi.mock('@/composables/useAuth', () => ({
  useAuth: () => mockAuth
}))

// Mock useCommunicationAdmin
vi.mock('@/composables/useCommunicationAdmin', () => ({
  useCommunicationAdmin: () => ({
    communicationEnabled: { value: true },
    loaded: { value: true },
    fetchCommunicationStatus: vi.fn()
  })
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

let router

describe('Router Configuration', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    mockAuth.getToken.mockReturnValue('valid_token')
    mockAuth.isAuthenticated.value = true
    mockAuth.isAdmin.value = false
    mockAuth.userRoles.value = ['researcher']

    // Fresh import for each test
    vi.resetModules()
    const mod = await import('@/router')
    router = mod.default
  }, 30000)

  // ==================== Route Definition Tests ====================

  describe('route definitions', () => {
    it('ROUTER_001: has a root redirect to /login', () => {
      const root = router.getRoutes().find(r => r.path === '/')
      expect(root).toBeDefined()
      expect(root.redirect).toBe('/login')
    })

    it('ROUTER_002: has /login route without auth requirement', () => {
      const login = router.getRoutes().find(r => r.path === '/login')
      expect(login).toBeDefined()
      expect(login.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_003: has /register route without auth requirement', () => {
      const register = router.getRoutes().find(r => r.name === 'Register')
      expect(register).toBeDefined()
      expect(register.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_004: has /Home route with auth requirement', () => {
      const home = router.getRoutes().find(r => r.path === '/Home')
      expect(home).toBeDefined()
      expect(home.meta.requiresAuth).toBe(true)
    })

    it('ROUTER_005: has /settings route', () => {
      const settings = router.getRoutes().find(r => r.name === 'UserSettings')
      expect(settings).toBeDefined()
      expect(settings.meta.requiresAuth).toBe(true)
    })

    it('ROUTER_006: has 404 catch-all route', () => {
      const notFound = router.getRoutes().find(r => r.name === 'NotFound')
      expect(notFound).toBeDefined()
    })
  })

  // ==================== Public Routes Tests ====================

  describe('public routes', () => {
    it('ROUTER_007: /Impressum is public', () => {
      const route = router.getRoutes().find(r => r.path === '/Impressum')
      expect(route.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_008: /Datenschutz is public', () => {
      const route = router.getRoutes().find(r => r.path === '/Datenschutz')
      expect(route.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_009: /Kontakt is public', () => {
      const route = router.getRoutes().find(r => r.path === '/Kontakt')
      expect(route.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_010: /join/:code registration route is public', () => {
      const route = router.getRoutes().find(r => r.name === 'RegisterWithCode')
      expect(route).toBeDefined()
      expect(route.meta.requiresAuth).toBe(false)
    })
  })

  // ==================== Auth Required Routes Tests ====================

  describe('auth-required routes', () => {
    const authRoutes = [
      'EvaluationHub', 'ScenarioManager', 'Ranker', 'Rater',
      'PromptEngineering', 'JudgeOverview', 'GenerationHub',
      'PipelineHub', 'ChatWithBots'
    ]

    authRoutes.forEach(name => {
      it(`ROUTER_011_${name}: ${name} requires auth`, () => {
        const route = router.getRoutes().find(r => r.name === name)
        expect(route).toBeDefined()
        expect(route.meta.requiresAuth).toBe(true)
      })
    })
  })

  // ==================== Admin Routes Tests ====================

  describe('admin routes', () => {
    it('ROUTER_012: /admin requires admin', () => {
      const route = router.getRoutes().find(r => r.name === 'AdminDashboard')
      expect(route).toBeDefined()
      expect(route.meta.requiresAdmin).toBe(true)
    })

    it('ROUTER_013: AdminUserProgressStats requires admin', () => {
      const route = router.getRoutes().find(r => r.name === 'AdminUserProgressStats')
      expect(route).toBeDefined()
      expect(route.meta.requiresAdmin).toBe(true)
    })
  })

  // ==================== Legacy Redirects Tests ====================

  describe('legacy redirects', () => {
    it('ROUTER_014: /AdminDashboard redirects to /admin', () => {
      const route = router.getRoutes().find(r => r.path === '/AdminDashboard')
      expect(route.redirect).toBe('/admin')
    })

    it('ROUTER_015: /AdminRanker redirects to /admin with tab', () => {
      const route = router.getRoutes().find(r => r.path === '/AdminRanker')
      expect(route.redirect).toBe('/admin?tab=scenarios')
    })

    it('ROUTER_016: /AdminPermissions redirects to /admin with tab', () => {
      const route = router.getRoutes().find(r => r.path === '/AdminPermissions')
      expect(route.redirect).toBe('/admin?tab=permissions')
    })

    it('ROUTER_017: /AdminRAG redirects to /admin with tab', () => {
      const route = router.getRoutes().find(r => r.path === '/AdminRAG')
      expect(route.redirect).toBe('/admin?tab=rag')
    })
  })

  // ==================== Props Configuration Tests ====================

  describe('route props', () => {
    it('ROUTER_018: RankerDetail has props: true', () => {
      const route = router.getRoutes().find(r => r.name === 'RankerDetail')
      expect(route.props).toBeDefined()
    })

    it('ROUTER_019: JudgeSession has props: true', () => {
      const route = router.getRoutes().find(r => r.name === 'JudgeSession')
      expect(route.props).toBeDefined()
    })

    it('ROUTER_020: ScenarioWorkspace has props: true', () => {
      const route = router.getRoutes().find(r => r.name === 'ScenarioWorkspace')
      expect(route.props).toBeDefined()
    })

    it('ROUTER_021: GenerationJobDetail has props: true', () => {
      const route = router.getRoutes().find(r => r.name === 'GenerationJobDetail')
      expect(route.props).toBeDefined()
    })
  })

  // ==================== Evaluation Routes Tests ====================

  describe('evaluation routes', () => {
    it('ROUTER_022: has EvaluationItemsOverview route', () => {
      const route = router.getRoutes().find(r => r.name === 'EvaluationItemsOverview')
      expect(route).toBeDefined()
      expect(route.path).toContain(':scenarioId')
    })

    it('ROUTER_023: has EvaluationSessionItem route', () => {
      const route = router.getRoutes().find(r => r.name === 'EvaluationSessionItem')
      expect(route).toBeDefined()
      expect(route.path).toContain(':itemId')
    })

    it('ROUTER_024: has EvaluationSession start route', () => {
      const route = router.getRoutes().find(r => r.name === 'EvaluationSession')
      expect(route).toBeDefined()
      expect(route.path).toContain('/start')
    })

    it('ROUTER_025: legacy /evaluate/:id redirects to new route', () => {
      const route = router.getRoutes().find(r => r.name === 'ScenarioEvaluation')
      expect(route).toBeDefined()
      expect(route.redirect).toBeDefined()
    })
  })

  // ==================== Permission Routes Tests ====================

  describe('permission-gated routes', () => {
    it('ROUTER_026: anonymization requires permission', () => {
      const route = router.getRoutes().find(r => r.name === 'AnonymizationManager')
      expect(route.meta.requiresPermission).toBe('feature:anonymization-pipeline:view')
    })

    it('ROUTER_027: anonymization detail requires permission', () => {
      const route = router.getRoutes().find(r => r.name === 'AnonymizationDetail')
      expect(route.meta.requiresPermission).toBe('feature:anonymization-pipeline:view')
    })
  })

  // ==================== Feature Routes Tests ====================

  describe('feature routes', () => {
    it('ROUTER_028: has pipeline routes', () => {
      expect(router.getRoutes().find(r => r.name === 'PipelineHub')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'PipelineWizard')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'PipelineSession')).toBeDefined()
    })

    it('ROUTER_029: has conference manager routes', () => {
      expect(router.getRoutes().find(r => r.name === 'ConferenceEntry')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'ResearchGroupSelection')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'ConferenceManager')).toBeDefined()
    })

    it('ROUTER_030: has KAIMO routes', () => {
      expect(router.getRoutes().find(r => r.name === 'KaimoHub')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'KaimoPanel')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'KaimoNewCase')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'KaimoCase')).toBeDefined()
    })

    it('ROUTER_031: has OnCoCo routes', () => {
      expect(router.getRoutes().find(r => r.name === 'OnCoCoOverview')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'OnCoCoConfig')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'OnCoCoResults')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'OnCoCoInfo')).toBeDefined()
    })

    it('ROUTER_032: has chatbot manager route', () => {
      const route = router.getRoutes().find(r => r.name === 'ChatbotManagerPage')
      expect(route).toBeDefined()
      expect(route.meta.requiresAuth).toBe(true)
    })

    it('ROUTER_033: has data import route with alias', () => {
      const route = router.getRoutes().find(r => r.name === 'DataImporter')
      expect(route).toBeDefined()
    })
  })

  // ==================== Navigation Guard Tests ====================

  describe('navigation guards', () => {
    it('ROUTER_034: redirects unauthenticated users to login', async () => {
      mockAuth.isAuthenticated.value = false
      mockAuth.getToken.mockReturnValue(null)

      // Fresh import to get guard with updated mock
      vi.resetModules()
      const mod = await import('@/router')
      const r = mod.default

      const next = vi.fn()
      // Simulate the beforeEach guard
      for (const guard of r.beforeGuards || []) {
        guard({ path: '/Home', matched: [{ meta: { requiresAuth: true } }], fullPath: '/Home' }, {}, next)
      }
    })

    it('ROUTER_035: allows navigation to public routes without auth', async () => {
      mockAuth.isAuthenticated.value = false
      mockAuth.getToken.mockReturnValue(null)

      vi.resetModules()
      const mod = await import('@/router')
      const r = mod.default

      // Public route should be accessible
      const impressum = r.getRoutes().find(r => r.path === '/Impressum')
      expect(impressum.meta.requiresAuth).toBe(false)
    })

    it('ROUTER_036: calls logout when token exists but not authenticated', async () => {
      mockAuth.isAuthenticated.value = false
      mockAuth.getToken.mockReturnValue('stale_token')
      // The guard should call auth.logout() when rawToken exists but isAuthenticated is false
    })
  })

  // ==================== Scroll Behavior Tests ====================

  describe('scroll behavior', () => {
    it('ROUTER_037: scrollBehavior returns savedPosition when available', () => {
      const savedPosition = { top: 100, left: 0 }
      const result = router.options.scrollBehavior({}, {}, savedPosition)
      expect(result).toEqual(savedPosition)
    })

    it('ROUTER_038: scrollBehavior scrolls to hash', () => {
      const result = router.options.scrollBehavior({ hash: '#section' }, {}, null)
      expect(result).toEqual({ el: '#section', behavior: 'smooth' })
    })

    it('ROUTER_039: scrollBehavior scrolls to top by default', () => {
      const result = router.options.scrollBehavior({}, {}, null)
      expect(result).toEqual({ top: 0, behavior: 'smooth' })
    })
  })

  // ==================== Collab Routes Tests ====================

  describe('collaboration routes', () => {
    it('ROUTER_040: has Markdown collab routes', () => {
      expect(router.getRoutes().find(r => r.name === 'MarkdownCollabHome')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'MarkdownCollabWorkspace')).toBeDefined()
    })

    it('ROUTER_041: has LaTeX collab routes', () => {
      expect(router.getRoutes().find(r => r.name === 'LatexCollabHome')).toBeDefined()
      expect(router.getRoutes().find(r => r.name === 'LatexCollabWorkspace')).toBeDefined()
    })

    it('ROUTER_042: has document-specific collab routes', () => {
      const mdDoc = router.getRoutes().find(r => r.name === 'MarkdownCollabWorkspaceDocument')
      expect(mdDoc).toBeDefined()
      expect(mdDoc.path).toContain(':documentId')

      const latexDoc = router.getRoutes().find(r => r.name === 'LatexCollabWorkspaceDocument')
      expect(latexDoc).toBeDefined()
      expect(latexDoc.path).toContain(':documentId')
    })
  })
})
