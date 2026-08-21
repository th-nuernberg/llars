import { createRouter, createWebHistory } from "vue-router";
import { i18n } from "@/i18n";
import { docsBasePathForLocale } from "@/utils/docsUrl";
import Login from "@/components/Login.vue";
import Register from "@/views/Register.vue";
import AutoLogin from "@/views/AutoLogin.vue";
import Home from "@/components/Home.vue";
import NotFound from "@/components/NotFound.vue";
import Ranker from "@/components/Ranker/Ranker.vue";
import RankerDetail from "@/components/Ranker/RankerDetail.vue";
import Rater from "@/components/Rater/Rater.vue";
import RaterDetail from "@/components/Rater/RaterDetail.vue";
import RaterDetailFeature from "@/components/Rater/RaterDetailFeature.vue";
import AdminDashboard from "@/components/Admin/AdminDashboard.vue"; // New unified Admin Dashboard
import AdminHome from "@/components/Admin/AdminHome.vue"; // Legacy Admin Dashboard
import AdminRanker from "@/components/Admin/AdminRanker.vue";
import AdminPermissions from "@/components/AdminPermissions.vue"; // Permission Management
import HistoryGeneration from "@/components/HistoryGenerator/HistoryGeneration.vue";
import HistoryGenerationDetail from "@/components/HistoryGenerator/HistoryGenerationDetail.vue";
import Impressum from "@/components/Orga/Impressum.vue";
import Datenschutz from "@/components/Orga/Datenschutz.vue";
import Nutzungsbedingungen from "@/components/Orga/Nutzungsbedingungen.vue";
// Eager (not lazy): /study-consent is a critical public study-entry page like
// Impressum/Datenschutz. A lazy chunk that fails to load left it rendering blank
// (header shows, content empty, no console error). Shipping it in the main
// bundle guarantees it always renders.
import StudyConsentInfo from "@/views/StudyConsentInfo.vue";
import Kontakt from "@/components/Orga/Kontakt.vue";
import axios from "axios";
import { useAuth } from "@/composables/useAuth";
import { usePermissions } from "@/composables/usePermissions";
import { logI18n } from "@/utils/logI18n";

// Session-scoped cache for the evaluator-only single-scenario shortcut.
// Populated lazily on the first navigation that needs it, invalidated on
// auth changes (see useAuth.logout below — we listen via a token-mismatch
// check). Values:
//   null                → not fetched yet
//   { count, scenarioId } → cached lookup; scenarioId is null when count !== 1
let _evaluatorScenarioShortcutCache = null;
let _evaluatorScenarioShortcutToken = null;

async function _resolveEvaluatorSingleScenario(currentToken) {
    // Invalidate cache on token change (logout/login switch).
    if (_evaluatorScenarioShortcutToken !== currentToken) {
        _evaluatorScenarioShortcutCache = null;
        _evaluatorScenarioShortcutToken = currentToken;
    }
    if (_evaluatorScenarioShortcutCache) return _evaluatorScenarioShortcutCache;
    try {
        // Hard 3s timeout — the router guard is on the critical-path of
        // every navigation; if /api/scenarios stalls (e.g. ephemeral
        // staging hiccup, transient 502 from gunicorn worker recycle),
        // the entire app hangs at /Home without ever reaching the
        // EvaluationHub. Better to silently fall back to /evaluation.
        const resp = await axios.get('/api/scenarios', {
            params: { filter: 'all', include_stats: 'false' },
            timeout: 3000,
        });
        const scenarios = Array.isArray(resp.data?.scenarios)
            ? resp.data.scenarios
            : Array.isArray(resp.data) ? resp.data : [];
        const count = scenarios.length;
        // Tolerate both numeric id and string id; the items-overview route
        // accepts either. Pick the first scenario when count === 1.
        const scenarioId = count === 1
            ? (scenarios[0]?.id ?? scenarios[0]?.scenario_id ?? null)
            : null;
        _evaluatorScenarioShortcutCache = { count, scenarioId };
        return _evaluatorScenarioShortcutCache;
    } catch (err) {
        // On failure, don't redirect — let the user see the EvaluationHub
        // and re-try manually. Cache a no-op result so we don't hammer the
        // API on every nav.
        console.warn('[router] evaluator shortcut: scenario lookup failed', err);
        _evaluatorScenarioShortcutCache = { count: -1, scenarioId: null };
        return _evaluatorScenarioShortcutCache;
    }
}

import AdminTester from "@/components/Admin/AdminTester.vue";

import Chat from "@/components/Chat.vue";
import ChatWithBots from "@/components/ChatWithBots.vue";

import TempTestPage from "@/components/TempTest.vue";

import PromptEngineering from "@/components/PromptEngineering/PromptEngineering.vue";
import PromptEngineeringDetail from "@/components/PromptEngineering/PromptEngineeringDetail.vue";

import Comparison from "@/components/comparison/Comparison.vue";
import ComparisonDetail from "@/components/comparison/ComparisonDetail.vue";
import AdminUserProgressStats from "@/components/Admin/AdminUserProgressStats.vue";
import AdminRAG from "@/components/Admin/AdminRAG.vue"; // RAG Document Management

// Anonymize Tool
import AnonymizeTool from "@/components/Anonymize/AnonymizeTool.vue";

// Anonymization Pipeline
import AnonymizationManager from "@/components/AnonymizationPipeline/AnonymizationManager.vue";
import AnonymizationDetail from "@/components/AnonymizationPipeline/AnonymizationDetail.vue";

// Judge Components
import JudgeOverview from "@/components/Judge/JudgeOverview.vue";
import JudgeConfig from "@/components/Judge/JudgeConfig.vue";
import JudgeSession from "@/components/Judge/JudgeSession.vue";
import JudgeResults from "@/components/Judge/JudgeResults.vue";

// OnCoCo Analysis Components
import OnCoCoOverview from "@/components/OnCoCo/OnCoCoOverview.vue";
import OnCoCoConfig from "@/components/OnCoCo/OnCoCoConfig.vue";
import OnCoCoResults from "@/components/OnCoCo/OnCoCoResults.vue";
import OnCoCoInfo from "@/components/OnCoCo/OnCoCoInfo.vue";
import KaimoHub from "@/components/Kaimo/KaimoHub.vue";
import KaimoPanel from "@/components/Kaimo/KaimoPanel.vue";
import KaimoNewCase from "@/components/Kaimo/KaimoNewCase.vue";
import KaimoCase from "@/components/Kaimo/KaimoCase.vue";
import KaimoCaseEditor from "@/components/Kaimo/KaimoCaseEditor.vue";

// Markdown Collab
import MarkdownCollabHome from "@/views/MarkdownCollab/MarkdownCollabHome.vue";
import MarkdownCollabWorkspace from "@/views/MarkdownCollab/MarkdownCollabWorkspace.vue";


// Evaluation Hub
import EvaluationHub from "@/components/Evaluation/EvaluationHub.vue";

// Evaluation Assistant (LLM Transparency)
import EvaluationAssistant from "@/components/EvaluationAssistant/EvaluationAssistant.vue";

// Data Importer
import DataImporterView from "@/views/DataImporter/DataImporterView.vue";

// Scenario Manager
import ScenarioManagerHome from "@/views/ScenarioManager/ScenarioManagerHome.vue";
import ScenarioWorkspace from "@/views/ScenarioManager/ScenarioWorkspace.vue";

// Fake/Echt (Authenticity)
import AuthenticityOverview from "@/components/Authenticity/AuthenticityOverview.vue";
import AuthenticityDetail from "@/components/Authenticity/AuthenticityDetail.vue";

// User Settings
import UserSettingsPage from "@/views/UserSettings/UserSettingsPage.vue";

// Evaluation Session (new unified evaluation interface)
import EvaluationSession from "@/views/Evaluation/EvaluationSession.vue";
import EvaluationItemsOverview from "@/views/Evaluation/EvaluationItemsOverview.vue";

// Batch Generation
import GenerationHub from "@/components/Generation/GenerationHub.vue";
import GenerationJobDetail from "@/components/Generation/GenerationJobDetail.vue";
import GenerationWizard from "@/components/Generation/GenerationWizard.vue";
import DemoVideoPage from "@/views/Video/DemoVideoPage.vue";

// Pipeline
import PipelineHub from "@/views/Pipeline/PipelineHub.vue";
import PipelineSession from "@/views/Pipeline/PipelineSession.vue";
import PipelineWizard from "@/views/Pipeline/PipelineWizard.vue";

// Conference Manager
import ConferenceEntry from "@/views/ConferenceManager/ConferenceEntry.vue";
import ResearchGroupSelection from "@/views/ConferenceManager/ResearchGroupSelection.vue";
import ConferenceManagerHome from "@/views/ConferenceManager/ConferenceManagerHome.vue";
import ResearchGroupMembers from "@/views/ConferenceManager/ResearchGroupMembers.vue";
import ResearchGroupAccessRequestPage from "@/views/ConferenceManager/ResearchGroupAccessRequestPage.vue";

// Messaging
import MessagingHome from "@/views/Messaging/MessagingHome.vue";
import { useCommunicationAdmin } from "@/composables/useCommunicationAdmin";

// Chatbot Manager (dedicated page, separated from Admin)
import ChatbotManagerPage from "@/views/ChatbotManager/ChatbotManagerPage.vue";

const EVALUATION_ROUTE_PERMISSIONS = [
    'feature:ranking:view',
    'feature:rating:view',
    'feature:mail_rating:view',
    'feature:comparison:view',
    'feature:authenticity:view'
];

const SCENARIO_ROUTE_PERMISSIONS = [
    'data:manage_scenarios',
    'feature:ranking:view',
    'feature:rating:view'
];

const routes = [
    { path: '/Impressum', component: Impressum, meta: { requiresAuth: false, seoTitle: 'imprintPage.title' } },
    { path: '/Datenschutz', component: Datenschutz, meta: { requiresAuth: false, seoTitle: 'privacyPolicy.title' } },
    { path: '/Nutzungsbedingungen', component: Nutzungsbedingungen, meta: { requiresAuth: false, seoTitle: 'termsPage.title' } },
    { path: '/Kontakt', component: Kontakt, meta: { requiresAuth: false, seoTitle: 'contactPage.title' } },
    // Redirect legacy docs hub to MkDocs (force full reload).
    // Zielsprache = aktuelle UI-Sprache (DE -> /mkdocs/, EN -> /mkdocs/en/).
    {
      path: '/docs',
      beforeEnter: () => {
        if (typeof window !== 'undefined') {
          const base = docsBasePathForLocale(i18n.global.locale.value);
          window.location.href = `${window.location.origin}${base}`;
        }
        return false;
      },
      meta: { requiresAuth: false }
    },
    {
      path: '/docs/:lang(en|de)?/:pathMatch(.*)*',
      beforeEnter: (to) => {
        if (typeof window !== 'undefined') {
          const rest = Array.isArray(to.params.pathMatch)
            ? to.params.pathMatch.join('/')
            : (to.params.pathMatch || '');
          // Explizit angeforderte Sprache respektieren, sonst UI-Sprache.
          const lang = to.params.lang || i18n.global.locale.value;
          const base = docsBasePathForLocale(lang);
          window.location.href = `${window.location.origin}${base}${rest}`;
        }
        return false;
      },
      meta: { requiresAuth: false }
    },

    { path: '/Home', component: Home, meta: { requiresAuth: true } },
    // Public: the landing page's "Demo Video" button links here, so logged-out
    // visitors must be able to watch the LLARS demo (YouTube is only a backup
    // link on this page). The video asset itself is already served publicly.
    { path: '/video', name: 'DemoVideoPage', component: DemoVideoPage, meta: { requiresAuth: false } },
    { path: '/settings', name: 'UserSettings', component: UserSettingsPage, meta: { requiresAuth: true } },
    {
      path: '/evaluation',
      name: 'EvaluationHub',
      component: EvaluationHub,
      meta: { requiresAuth: true, requiresAnyPermission: EVALUATION_ROUTE_PERMISSIONS }
    },
    {
      path: '/evaluation/assistant/:id',
      name: 'EvaluationAssistant',
      component: EvaluationAssistant,
      props: true,
      meta: { requiresAuth: true, requiresAnyPermission: EVALUATION_ROUTE_PERMISSIONS }
    },
    { path: '/data-import', alias: '/import', name: 'DataImporter', component: DataImporterView, meta: { requiresAuth: true } },

    // Scenario Manager
    {
      path: '/scenarios',
      name: 'ScenarioManager',
      component: ScenarioManagerHome,
      meta: { requiresAuth: true, requiresAnyPermission: SCENARIO_ROUTE_PERMISSIONS }
    },
    {
      path: '/scenarios/:id',
      name: 'ScenarioWorkspace',
      component: ScenarioWorkspace,
      props: true,
      meta: { requiresAuth: true, requiresAnyPermission: SCENARIO_ROUTE_PERMISSIONS }
    },
    // Legacy evaluation route - redirects to new evaluation interface
    {
      path: '/evaluate/:id',
      name: 'ScenarioEvaluation',
      redirect: to => ({ name: 'EvaluationItemsOverview', params: { scenarioId: to.params.id } })
    },

    // New unified Evaluation Session routes
    // Items Overview - shows all items as cards
    {
      path: '/scenarios/:scenarioId/evaluate',
      name: 'EvaluationItemsOverview',
      component: EvaluationItemsOverview,
      props: true,
      meta: { requiresAuth: true, requiresAnyPermission: EVALUATION_ROUTE_PERMISSIONS }
    },
    // Evaluation Session - for evaluating a specific item or first item
    {
      path: '/scenarios/:scenarioId/evaluate/item/:itemId',
      name: 'EvaluationSessionItem',
      component: EvaluationSession,
      props: true,
      meta: { requiresAuth: true, requiresAnyPermission: EVALUATION_ROUTE_PERMISSIONS }
    },
    {
      path: '/scenarios/:scenarioId/evaluate/start',
      name: 'EvaluationSession',
      component: EvaluationSession,
      props: true,
      meta: { requiresAuth: true, requiresAnyPermission: EVALUATION_ROUTE_PERMISSIONS }
    },

    { path: '/Ranker', name: 'Ranker', component: Ranker, meta: { requiresAuth: true } },
    { path: '/Ranker/:id', name: 'RankerDetail', component: RankerDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater', name: 'Rater', component: Rater, meta: { requiresAuth: true } },
    { path: '/Rater/:id', name: 'RaterDetail', component: RaterDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater/:id/:feature', name:'RaterDetailFeature', component: RaterDetailFeature, props: true, meta: { requiresAuth: true } },
    { path: '/authenticity', name: 'AuthenticityOverview', component: AuthenticityOverview, meta: { requiresAuth: true } },
    { path: '/authenticity/:id', name: 'AuthenticityDetail', component: AuthenticityDetail, props: true, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration', name: 'HistoryGenerator', component: HistoryGeneration, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration/:id', name:'HistoryGenerationDetail', component: HistoryGenerationDetail, props: true, meta: { requiresAuth: true } },
    { path: '/PromptEngineering', name: 'PromptEngineering', component: PromptEngineering, meta: { requiresAuth: true } },
    // PromptEngineeringDetail liest die ID intern aus der Route, props: true entfernt, um Vue-Warnung zu vermeiden
    { path : '/PromptEngineering/:id', name:'PromptEngineeringDetail', component: PromptEngineeringDetail, meta: { requiresAuth: true } },

    // Batch Generation
    { path: '/generation', name: 'GenerationHub', component: GenerationHub, meta: { requiresAuth: true } },
    { path: '/generation/new', name: 'GenerationWizard', component: GenerationWizard, meta: { requiresAuth: true } },
    { path: '/generation/:jobId', name: 'GenerationJobDetail', component: GenerationJobDetail, props: true, meta: { requiresAuth: true } },

    // Messaging (gated by communication toggle + permission)
    {
      path: '/messaging',
      name: 'Messaging',
      component: MessagingHome,
      meta: { requiresAuth: true },
      beforeEnter: async () => {
        const { communicationEnabled, loaded, fetchCommunicationStatus } = useCommunicationAdmin()
        if (!loaded.value) await fetchCommunicationStatus()
        if (!communicationEnabled.value) return '/home'
      },
    },
    {
      path: '/messaging/:conversationId',
      name: 'MessagingConversation',
      component: MessagingHome,
      props: true,
      meta: { requiresAuth: true },
      beforeEnter: async () => {
        const { communicationEnabled, loaded, fetchCommunicationStatus } = useCommunicationAdmin()
        if (!loaded.value) await fetchCommunicationStatus()
        if (!communicationEnabled.value) return '/home'
      },
    },

    // Conference Manager
    { path: '/conferences', name: 'ConferenceEntry', component: ConferenceEntry, meta: { requiresAuth: true } },
    { path: '/conferences/groups', name: 'ResearchGroupSelection', component: ResearchGroupSelection, meta: { requiresAuth: true } },
    { path: '/conferences/groups/:groupId', name: 'ConferenceManager', component: ConferenceManagerHome, props: true, meta: { requiresAuth: true } },
    { path: '/conferences/groups/:groupId/members', name: 'ResearchGroupMembers', component: ResearchGroupMembers, props: true, meta: { requiresAuth: true } },
    { path: '/conferences/groups/:groupId/request-access', name: 'ResearchGroupAccessRequest', component: ResearchGroupAccessRequestPage, props: true, meta: { requiresAuth: true } },

    // Pipeline (admin-only, see home_tiles.contract.json)
    { path: '/pipeline', name: 'PipelineHub', component: PipelineHub, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/pipeline/new', name: 'PipelineWizard', component: PipelineWizard, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/pipeline/:runId', name: 'PipelineSession', component: PipelineSession, props: true, meta: { requiresAuth: true, requiresAdmin: true } },

    { path : '/comparison', name:'Comparison', component: Comparison, meta: { requiresAuth: true } },
    {
      path: '/comparison/session/:session_id',
      name: 'ComparisonDetail',
      component: ComparisonDetail,
      props: true,
      meta: { requiresAuth: true }
    },

    // Anonymize Tool
    { path: '/Anonymize', alias: '/anonymize', name: 'AnonymizeTool', component: AnonymizeTool, meta: { requiresAuth: true } },

    // Anonymization Pipeline
    { path: '/anonymization', name: 'AnonymizationManager', component: AnonymizationManager, meta: { requiresAuth: true, requiresPermission: 'feature:anonymization-pipeline:view' } },
    { path: '/anonymization/:id', name: 'AnonymizationDetail', component: AnonymizationDetail, props: true, meta: { requiresAuth: true, requiresPermission: 'feature:anonymization-pipeline:view' } },

    // Judge Routes
    // Chatbot Arena (Judge): admin-only, in sync with home_tiles.contract.json.
    // The nightly tile-regression suite asserts that evaluator/researcher
    // get redirected away from `/judge`; without `requiresAdmin: true` they
    // hit the page and the e2e suite blocks prod-deploy on the Negative-
    // Routes assertion.
    { path: '/judge', name: 'JudgeOverview', component: JudgeOverview, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/judge/config', name: 'JudgeConfig', component: JudgeConfig, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/judge/session/:id', name: 'JudgeSession', component: JudgeSession, props: true, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/judge/results/:id', name: 'JudgeResults', component: JudgeResults, props: true, meta: { requiresAuth: true, requiresAdmin: true } },

    // OnCoCo Analysis Routes
    { path: '/oncoco', name: 'OnCoCoOverview', component: OnCoCoOverview, meta: { requiresAuth: true } },
    { path: '/oncoco/config', name: 'OnCoCoConfig', component: OnCoCoConfig, meta: { requiresAuth: true } },
    { path: '/oncoco/results/:id', name: 'OnCoCoResults', component: OnCoCoResults, props: true, meta: { requiresAuth: true } },
    { path: '/oncoco/info', name: 'OnCoCoInfo', component: OnCoCoInfo, meta: { requiresAuth: true } },
    // KAIMO Routes
    { path: '/kaimo', name: 'KaimoHub', component: KaimoHub, meta: { requiresAuth: true } },
    { path: '/kaimo/panel', name: 'KaimoPanel', component: KaimoPanel, meta: { requiresAuth: true } },
    { path: '/kaimo/new', name: 'KaimoNewCase', component: KaimoNewCase, meta: { requiresAuth: true } },
    { path: '/kaimo/edit/:id', name: 'KaimoCaseEditor', component: KaimoCaseEditor, props: true, meta: { requiresAuth: true } },
    { path: '/kaimo/:id', name: 'KaimoCase', component: KaimoCase, props: true, meta: { requiresAuth: true } },

    // Chatbot Manager (dedicated page for chatbot_manager role)
    { path: '/chatbot-manager', name: 'ChatbotManagerPage', component: ChatbotManagerPage, meta: { requiresAuth: true } },

    // New unified Admin Dashboard (admin only)
    { path: '/admin', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },

    // Legacy Admin Routes (redirect to new dashboard with appropriate tab)
    { path: '/AdminDashboard', redirect: '/admin' },
    { path: '/AdminRanker', redirect: '/admin?tab=scenarios' },
    { path: '/AdminPermissions', redirect: '/admin?tab=permissions' },
    { path: '/AdminRAG', redirect: '/admin?tab=rag' },
    { path: '/AdminUserProgressStats/:id', name:'AdminUserProgressStats', component: AdminUserProgressStats, props: true, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/AdminTester', component: AdminTester, meta: { requiresAuth: true, requiresAdmin: true } },

    { path: '/login', component: Login, meta: { requiresAuth: false } },
    { path: '/register', name: 'Register', component: Register, meta: { requiresAuth: false } },
    { path: '/join/:code', name: 'RegisterWithCode', component: Register, props: true, meta: { requiresAuth: false } },
    // Passwordless magic auto-login link from the IJCAI welcome mail.
    // AutoLogin.vue POSTs the token to /api/auth/magic-login, installs the
    // returned Authentik token bundle and routes the user straight in.
    { path: '/auto-login/:token', name: 'AutoLogin', component: AutoLogin, props: true, meta: { requiresAuth: false } },
    // Self-service password reset (gated by the admin toggle; the login
    // link is hidden when disabled). hiddenWhenAuth reuses the existing
    // guard that bounces already-authenticated users to /Home.
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('@/views/ForgotPassword.vue'),
      meta: { requiresAuth: false, hiddenWhenAuth: true },
    },
    {
      path: '/reset/:token',
      name: 'ResetPassword',
      component: () => import('@/views/ResetPassword.vue'),
      props: true,
      meta: { requiresAuth: false, hiddenWhenAuth: true },
    },
    // Friendly fallback when /join/:code points at an unknown / expired
    // referral link. Register.vue redirects here on validation failure
    // (preserving the attempted code as a query for context).
    {
      path: '/join-invalid',
      name: 'JoinInvalid',
      component: () => import('@/views/JoinInvalid.vue'),
      meta: { requiresAuth: false },
    },
    // Standalone consent-information page — linked from the Register
    // form's single mandatory consent checkbox. Public so the link in
    // the outreach email works for people who aren't registered yet.
    {
      path: '/study-consent',
      name: 'StudyConsentInfo',
      component: StudyConsentInfo,
      meta: { requiresAuth: false },
    },
    // Public landing page — rendered natively on "/" (kein Login-Redirect mehr).
    // hideAppChrome versteckt AppBar + globalen Footer (App.vue), da die
    // Landing Page eigene Nav/Footer mitbringt. hiddenWhenAuth schickt
    // bereits eingeloggte User weiter auf /Home bzw. in den
    // Single-Scenario-Shortcut (siehe Guard unten).
    {
      path: '/',
      name: 'LandingPage',
      component: () => import('@/views/LandingPage/LandingPage.vue'),
      meta: { requiresAuth: false, hiddenWhenAuth: true, hideAppChrome: true }
    },
    // Alter Direktlink bleibt als Alias erhalten (externe Verweise/Bookmarks).
    { path: '/landing', redirect: '/', meta: { requiresAuth: false } },
    // Admin-only preview: lets admins inspect the public landing page
    // without the hiddenWhenAuth redirect kicking them back to /Home.
    {
      path: '/landing-preview',
      name: 'LandingPagePreview',
      component: () => import('@/views/LandingPage/LandingPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, hideAppChrome: true }
    },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound }, // 404 Route

    { path: '/chat', component: ChatWithBots, name: 'ChatWithBots', meta: { requiresAuth: true } },
    { path: '/chat-legacy', component: Chat, meta: { requiresAuth: true } },

    // Markdown Collab
    { path: '/MarkdownCollab', name: 'MarkdownCollabHome', component: MarkdownCollabHome, meta: { requiresAuth: true } },
    { path: '/MarkdownCollab/workspace/:workspaceId', name: 'MarkdownCollabWorkspace', component: MarkdownCollabWorkspace, meta: { requiresAuth: true } },
    { path: '/MarkdownCollab/workspace/:workspaceId/document/:documentId', name: 'MarkdownCollabWorkspaceDocument', component: MarkdownCollabWorkspace, meta: { requiresAuth: true } },


    { path: '/TempTestPage', component: TempTestPage, meta: { requiresAuth: true } }

];

const router = createRouter({
    history: createWebHistory(),
    routes,
    // Scroll to top on every navigation
    scrollBehavior(to, from, savedPosition) {
        // If browser back/forward button was used, restore saved position
        if (savedPosition) {
            return savedPosition;
        }
        // If navigating to a hash anchor, scroll to it
        if (to.hash) {
            return {
                el: to.hash,
                behavior: 'smooth'
            };
        }
        // Otherwise, always scroll to top
        return { top: 0, behavior: 'smooth' };
    }
});

// Navigationswächter mit Custom Auth
router.beforeEach(async (to, from, next) => {
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);

    const auth = useAuth();
    const rawToken = auth.getToken();
    const isAuthenticated = auth.isAuthenticated.value;
    const isAdmin = auth.isAdmin.value;
    const isChatbotManager = auth.userRoles.value?.includes('chatbot_manager');

    if (rawToken && !isAuthenticated) {
        auth.logout();
    }

    logI18n("log", "logs.router.navigateTo", to.path);
    logI18n("log", "logs.router.authenticated", isAuthenticated);
    logI18n("log", "logs.router.isAdmin", isAdmin);

    // Evaluator-style landing: users with NO power role (admin / researcher
    // / chatbot_manager) get the simplified landing flow — straight into
    // /evaluation (or into their single assigned scenario, see below).
    //
    // We deliberately include `viewer` (the alias `permission_service.py`
    // normalises to `evaluator` server-side, but old JWTs in flight may
    // still carry it raw) and any unknown/empty role set so an invited
    // rater whose JWT hasn't fully propagated still gets the redirect.
    // The check is "absence of power roles" rather than "exactly equals
    // evaluator" — that way a user can have evaluator + any non-power
    // role and still land on the rater flow (Sozialwissenschaften feedback 2026-05-17).
    const roles = auth.userRoles.value || [];
    const POWER_ROLES = new Set(['admin', 'researcher', 'chatbot_manager']);
    const hasPowerRole = roles.some(r => POWER_ROLES.has(r));
    // Require at least one role to avoid redirecting users whose auth-bundle
    // hasn't been fully populated yet (e.g. CI fixtures created via the
    // temporary-user endpoint, fresh referral registrations where the JWT
    // groups claim arrives a tick later). For those we keep the default
    // /Home landing — once their role propagates, the next navigation
    // (or page reload) triggers the redirect normally.
    const isEvaluatorOnly =
        isAuthenticated && roles.length > 0 && !hasPowerRole;

    // Single-scenario shortcut (Sozialwissenschaften 2026-05-17, refined 2026-05-18).
    //
    // Two redirect-paths, tried in order:
    //
    //   1. **Referral-bound landing.** If the user originally registered
    //      via a referral link tied to a specific scenario, the login
    //      response carries `referral_target_scenario_id` and we mirror
    //      it into localStorage. We prefer this hint over the API count
    //      so a rater who later gets added to a second scenario (e.g.
    //      admin testing) STILL lands directly in the study they were
    //      actually invited to.
    //
    //   2. **Count===1 fallback.** No referral binding? Fall back to the
    //      original heuristic: if the user has exactly one assigned
    //      scenario, drop them into its item-overview. count===0 stays
    //      on /Home (empty-state for fresh accounts) and count>1 also
    //      stays put (arbitrary pick would be confusing).
    function _readReferralTargetScenario() {
        try {
            const raw = localStorage.getItem('llars-referral-target-scenario');
            if (!raw) return null;
            const n = Number(raw);
            return Number.isFinite(n) && n > 0 ? n : null;
        } catch (_) {
            return null;
        }
    }

    async function _maybeRedirectToSingleScenario() {
        if (!isEvaluatorOnly) return null;

        const referralId = _readReferralTargetScenario();
        if (referralId) {
            const targetPath = `/scenarios/${referralId}/evaluate`;
            if (to.path === targetPath || to.path.startsWith(targetPath + '/')) {
                return null; // already there
            }
            return targetPath;
        }

        const { count, scenarioId } = await _resolveEvaluatorSingleScenario(rawToken);
        if (count !== 1 || scenarioId == null) return null;
        const targetPath = `/scenarios/${scenarioId}/evaluate`;
        if (to.path === targetPath || to.path.startsWith(targetPath + '/')) {
            return null; // already there
        }
        return targetPath;
    }

    // Apply the single-scenario shortcut on landing-style routes:
    //  - /Home, / (main landing)
    //  - /login, /register (hiddenWhenAuth gate)
    //  - /evaluation (tool list — user explicitly asked for "ohne über
    //    home usw gehen zu müssen")
    if (
        isAuthenticated && (
            to.path === '/Home' ||
            to.path === '/' ||
            to.path === '/evaluation' ||
            to.meta.hiddenWhenAuth
        )
    ) {
        const target = await _maybeRedirectToSingleScenario();
        if (target) { next(target); return; }
    }

    // Authenticated users hitting login/register without the shortcut
    // (count !== 1) get pushed back to /Home as before.
    if (to.meta.hiddenWhenAuth && isAuthenticated) {
        next('/Home');
        return;
    }

    // If route requires authentication and user is not authenticated
    if (requiresAuth && !isAuthenticated) {
        logI18n("log", "logs.router.requireAuthRedirect");
        next({ path: '/login', query: { redirect: to.fullPath } });
        return;
    }

    // If route requires admin role
    if (requiresAdmin && !isAdmin) {
        // Redirect chatbot managers trying to access /admin to their dedicated page
        if (isChatbotManager && to.path === '/admin') {
            const tabMap = { chatbots: 'chatbots', rag: 'rag', crawler: 'crawler' };
            const tab = tabMap[to.query.tab] || 'chatbots';
            next({ path: '/chatbot-manager', query: { tab } });
            return;
        }
        logI18n("log", "logs.router.requireAdminRedirect");
        next('/Home');
        return;
    }

    // If route requires specific permission
    const requiredPermission = to.matched.find(record => record.meta.requiresPermission)?.meta.requiresPermission;
    const requiredAnyPermissionMeta = to.matched.find(record => Array.isArray(record.meta.requiresAnyPermission))
        ?.meta.requiresAnyPermission;

    // Permission gates race the async permission fetch on hard reload:
    // `usePermissions` starts with an empty list and is only populated by a
    // backend call first triggered in App.vue's onMounted — which runs AFTER
    // this guard. Without awaiting it here, deep permission-gated routes (e.g.
    // /scenarios/:id/evaluate/item/:itemId) would evaluate against an empty
    // permission set and bounce the authenticated user to /Home. Ensure the
    // permissions are loaded once before evaluating the gates below.
    if (isAuthenticated && (requiredPermission || requiredAnyPermissionMeta?.length)) {
        const { hasLoaded, fetchPermissions } = usePermissions();
        if (!hasLoaded.value) {
            await fetchPermissions();
        }
    }

    // Permission gates are a UX affordance, not the security boundary — every
    // gated route is enforced server-side by @require_permission. So when we
    // could not determine the permissions (429 rate limit, 5xx, offline), let
    // the navigation through instead of bouncing: a wrongly-allowed navigation
    // just renders a view whose API calls fail, while a wrongly-denied one
    // ejects a rater from the study they are in the middle of.
    //
    // INCIDENT 2026-07-29: polling exhausted the per-IP rate limit on
    // /api/permissions/my-permissions, the permission set stayed empty, and
    // these two gates bounced raters to '/' → /login on every attempt. It read
    // as "I can't log in anymore" even though every login returned HTTP 200.
    const { loadFailedTransiently } = usePermissions();
    const permissionsUnknown = loadFailedTransiently.value;

    if (requiredPermission && !permissionsUnknown) {
        const { hasPermission } = usePermissions();
        if (!hasPermission(requiredPermission)) {
            next({ path: '/' });
            return;
        }
    }

    if (requiredAnyPermissionMeta?.length && !permissionsUnknown) {
        const { hasAnyPermission } = usePermissions();
        if (!hasAnyPermission(...requiredAnyPermissionMeta)) {
            next('/Home');
            return;
        }
    }

    // All checks passed, proceed with navigation
    next();
});

// Per-Route-Dokumenttitel für Tab-Anzeige und JS-rendernde Crawler. Die
// statische SEO-Basis (Description/OG/JSON-LD) steht in index.html; hier wird
// nur der Titel pro Route gesetzt. `meta.seoTitle` (i18n-Key oder Klartext)
// überschreibt den Default, sonst wird der Routenname angehängt.
const DEFAULT_TITLE = 'LLARS – Quelloffene Plattform für LLM-Evaluation & Labeling';
router.afterEach((to) => {
    if (typeof document === 'undefined') return;
    const raw = to.meta?.seoTitle;
    let title = DEFAULT_TITLE;
    if (raw) {
        // i18n-Key auflösen, falls vorhanden; sonst Klartext verwenden.
        const translated = i18n.global.te?.(raw) ? i18n.global.t(raw) : raw;
        title = `${translated} · LLARS`;
    } else if (to.name && to.path !== '/') {
        title = `${String(to.name)} · LLARS`;
    }
    document.title = title;
});

export default router;
