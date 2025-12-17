import { createRouter, createWebHistory } from "vue-router";
import Login from "@/components/Login.vue";
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
import Documentation from "@/components/Orga/Documentation.vue";

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

const routes = [
    { path: '/Impressum', component: Impressum, meta: { requiresAuth: false } },
    { path: '/Datenschutz', component: Datenschutz, meta: { requiresAuth: false } },
    { path: '/Kontakt', component: Kontakt, meta: { requiresAuth: false } },
    { path: '/docs', component: Documentation, meta: { requiresAuth: false } },

    { path: '/Home', component: Home, meta: { requiresAuth: true } },
    { path: '/Ranker', component: Ranker, meta: { requiresAuth: true } },
    { path: '/Ranker/:id', name:'RankerDetail', component: RankerDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater', component: Rater, meta: { requiresAuth: true } },
    { path: '/Rater/:id', name:'RaterDetail', component: RaterDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater/:id/:feature', name:'RaterDetailFeature', component: RaterDetailFeature, props: true, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration', name: 'HistoryGenerator', component: HistoryGeneration, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration/:id', name:'HistoryGenerationDetail', component: HistoryGenerationDetail, props: true, meta: { requiresAuth: true } },
    { path: '/PromptEngineering', name: 'PromptEngineering', component: PromptEngineering, meta: { requiresAuth: true } },
    // PromptEngineeringDetail liest die ID intern aus der Route, props: true entfernt, um Vue-Warnung zu vermeiden
    { path : '/PromptEngineering/:id', name:'PromptEngineeringDetail', component: PromptEngineeringDetail, meta: { requiresAuth: true } },
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
    { path: '/admin', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },

    // Legacy Admin Routes (redirect to new dashboard with appropriate tab)
    { path: '/AdminDashboard', redirect: '/admin' },
    { path: '/AdminRanker', redirect: '/admin?tab=scenarios' },
    { path: '/AdminPermissions', redirect: '/admin?tab=permissions' },
    { path: '/AdminRAG', redirect: '/admin?tab=rag' },
    { path: '/AdminUserProgressStats/:id', name:'AdminUserProgressStats', component: AdminUserProgressStats, props: true, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/AdminTester', component: AdminTester, meta: { requiresAuth: true, requiresAdmin: true } },

    { path: '/login', component: Login, meta: { requiresAuth: false } },
    { path: '/', redirect: '/login' },
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
router.beforeEach((to, from, next) => {
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);

    const clearAuthStorage = () => {
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_refreshToken');
        sessionStorage.removeItem('auth_idToken');
        sessionStorage.removeItem('auth_llars_roles');
        localStorage.removeItem('username');
    };

    const isJwtExpired = (jwtToken, skewSeconds = 30) => {
        try {
            const parts = String(jwtToken || '').split('.');
            if (parts.length < 2) return false;
            const payload = JSON.parse(atob(parts[1]));
            const exp = payload?.exp;
            if (!exp) return false;
            const now = Math.floor(Date.now() / 1000);
            return now >= (exp - skewSeconds);
        } catch (e) {
            return false;
        }
    };

    // Get auth instance from useAuth composable
    // We need to import it here instead of using useAuth() directly
    // because router guards run before components are mounted
    const rawToken = sessionStorage.getItem('auth_token');
    const isAuthenticated = !!rawToken && !isJwtExpired(rawToken);

    let userRoles = [];
    let isAdmin = false;

    if (isAuthenticated) {
        try {
            // Use stored LLARS roles from backend response (based on Authentik groups)
            const storedRoles = sessionStorage.getItem('auth_llars_roles');
            if (storedRoles) {
                userRoles = JSON.parse(storedRoles);
            } else {
                // Fallback: Try to get groups from token (Authentik uses 'groups' not 'realm_access.roles')
                const token = sessionStorage.getItem('auth_token');
                const parsed = JSON.parse(atob(token.split('.')[1]));
                userRoles = parsed?.groups || [];
            }
            // Check for 'admin' role or 'authentik Admins' group
            isAdmin = userRoles.includes('admin') || userRoles.includes('authentik Admins');
        } catch (e) {
            console.error('Failed to parse token/roles in router guard:', e);
        }
    } else if (rawToken) {
        // Token exists but is expired → clear to avoid UI getting stuck
        clearAuthStorage();
    }

    console.log("Navigating to:", to.path);
    console.log("Authenticated:", isAuthenticated);
    console.log("User roles:", userRoles);

    // If route requires authentication and user is not authenticated
    if (requiresAuth && !isAuthenticated) {
        console.log("Route requires auth, redirecting to login");
        next('/login');
        return;
    }

    // If route requires admin role
    if (requiresAdmin && !isAdmin) {
        console.log("User is not admin, redirecting to Home");
        next('/Home');
        return;
    }

    // All checks passed, proceed with navigation
    next();
});


export default router;
