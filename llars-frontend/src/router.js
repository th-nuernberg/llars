import { createRouter, createWebHistory } from "vue-router";
import Login from "@/components/Login.vue";
import Register from "@/views/Register.vue";
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
import Kontakt from "@/components/Orga/Kontakt.vue";
import { useAuth } from "@/composables/useAuth";
import { logI18n } from "@/utils/logI18n";

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

// LaTeX Collab (mit KI-Features)
import LatexCollabHome from "@/views/LatexCollabAI/LatexCollabAIHome.vue";
import LatexCollabWorkspace from "@/views/LatexCollabAI/LatexCollabAIWorkspace.vue";

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

const routes = [
    { path: '/Impressum', component: Impressum, meta: { requiresAuth: false } },
    { path: '/Datenschutz', component: Datenschutz, meta: { requiresAuth: false } },
    { path: '/Kontakt', component: Kontakt, meta: { requiresAuth: false } },
    // Redirect legacy docs hub to MkDocs (force full reload)
    {
      path: '/docs',
      beforeEnter: () => {
        if (typeof window !== 'undefined') {
          window.location.href = `${window.location.origin}/mkdocs/en/`;
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
          const suffix = rest ? `/mkdocs/en/${rest}` : '/mkdocs/en/';
          window.location.href = `${window.location.origin}${suffix}`;
        }
        return false;
      },
      meta: { requiresAuth: false }
    },

    { path: '/Home', component: Home, meta: { requiresAuth: true } },
    { path: '/settings', name: 'UserSettings', component: UserSettingsPage, meta: { requiresAuth: true } },
    { path: '/evaluation', name: 'EvaluationHub', component: EvaluationHub, meta: { requiresAuth: true } },
    { path: '/evaluation/assistant/:id', name: 'EvaluationAssistant', component: EvaluationAssistant, props: true, meta: { requiresAuth: true } },
    { path: '/data-import', alias: '/import', name: 'DataImporter', component: DataImporterView, meta: { requiresAuth: true } },

    // Scenario Manager
    { path: '/scenarios', name: 'ScenarioManager', component: ScenarioManagerHome, meta: { requiresAuth: true } },
    { path: '/scenarios/:id', name: 'ScenarioWorkspace', component: ScenarioWorkspace, props: true, meta: { requiresAuth: true } },
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
      meta: { requiresAuth: true }
    },
    // Evaluation Session - for evaluating a specific item or first item
    {
      path: '/scenarios/:scenarioId/evaluate/item/:itemId',
      name: 'EvaluationSessionItem',
      component: EvaluationSession,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/scenarios/:scenarioId/evaluate/start',
      name: 'EvaluationSession',
      component: EvaluationSession,
      props: true,
      meta: { requiresAuth: true }
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

    // Judge Routes
    { path: '/judge', name: 'JudgeOverview', component: JudgeOverview, meta: { requiresAuth: true } },
    { path: '/judge/config', name: 'JudgeConfig', component: JudgeConfig, meta: { requiresAuth: true } },
    { path: '/judge/session/:id', name: 'JudgeSession', component: JudgeSession, props: true, meta: { requiresAuth: true } },
    { path: '/judge/results/:id', name: 'JudgeResults', component: JudgeResults, props: true, meta: { requiresAuth: true } },

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

    // New unified Admin Dashboard
    { path: '/admin', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, requiresAdminOrChatbotManager: true } },

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
    { path: '/', redirect: '/login' },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound }, // 404 Route

    { path: '/chat', component: ChatWithBots, name: 'ChatWithBots', meta: { requiresAuth: true } },
    { path: '/chat-legacy', component: Chat, meta: { requiresAuth: true } },

    // Markdown Collab
    { path: '/MarkdownCollab', name: 'MarkdownCollabHome', component: MarkdownCollabHome, meta: { requiresAuth: true } },
    { path: '/MarkdownCollab/workspace/:workspaceId', name: 'MarkdownCollabWorkspace', component: MarkdownCollabWorkspace, meta: { requiresAuth: true } },
    { path: '/MarkdownCollab/workspace/:workspaceId/document/:documentId', name: 'MarkdownCollabWorkspaceDocument', component: MarkdownCollabWorkspace, meta: { requiresAuth: true } },

    // LaTeX Collab (mit optionalen KI-Features)
    { path: '/LatexCollab', name: 'LatexCollabHome', component: LatexCollabHome, meta: { requiresAuth: true } },
    { path: '/LatexCollab/workspace/:workspaceId', name: 'LatexCollabWorkspace', component: LatexCollabWorkspace, meta: { requiresAuth: true } },
    { path: '/LatexCollab/workspace/:workspaceId/document/:documentId', name: 'LatexCollabWorkspaceDocument', component: LatexCollabWorkspace, meta: { requiresAuth: true } },

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
router.beforeEach((to, from, next) => {
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
    const requiresAdminOrChatbotManager = to.matched.some(record => record.meta.requiresAdminOrChatbotManager);

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

    // If route requires authentication and user is not authenticated
    if (requiresAuth && !isAuthenticated) {
        logI18n("log", "logs.router.requireAuthRedirect");
        next({ path: '/login', query: { redirect: to.fullPath } });
        return;
    }

    // If route requires admin role
    if (requiresAdmin && !isAdmin) {
        logI18n("log", "logs.router.requireAdminRedirect");
        next('/Home');
        return;
    }

    if (requiresAdminOrChatbotManager && !(isAdmin || isChatbotManager)) {
        logI18n("log", "logs.router.requireAdminOrManagerRedirect");
        next('/Home');
        return;
    }

    // All checks passed, proceed with navigation
    next();
});


export default router;
