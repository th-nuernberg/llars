import { createRouter, createWebHistory } from "vue-router";
import Login from "@/components/Login.vue";
import Home from "@/components/Home.vue";
import NotFound from "@/components/NotFound.vue";
import Ranker from "@/components/Ranker/Ranker.vue";
import RankerDetail from "@/components/Ranker/RankerDetail.vue";
import Rater from "@/components/Rater/Rater.vue";
import RaterDetail from "@/components/Rater/RaterDetail.vue";
import RaterDetailFeature from "@/components/Rater/RaterDetailFeature.vue";
import AdminHome from "@/components/Admin/AdminHome.vue"; // Admin Dashboard
import AdminRanker from "@/components/Admin/AdminRanker.vue";
import HistoryGeneration from "@/components/HistoryGenerator/HistoryGeneration.vue";
import HistoryGenerationDetail from "@/components/HistoryGenerator/HistoryGenerationDetail.vue";
import Impressum from "@/components/Orga/Impressum.vue";
import Datenschutz from "@/components/Orga/Datenschutz.vue";
import Kontakt from "@/components/Orga/Kontakt.vue";
import AdminTester from "@/components/Admin/AdminTester.vue";

import ChatWidget from "@/components/ChatWidget.vue";

// Importiere die Admin-Check Funktion
import { isAdmin } from '@/services/admins';

const routes = [
    { path: '/Impressum', component: Impressum, meta: { requiresAuth: false } },
    { path: '/Datenschutz', component: Datenschutz, meta: { requiresAuth: false } },
    { path: '/Kontakt', component: Kontakt, meta: { requiresAuth: false } },

    { path: '/Home', component: Home, meta: { requiresAuth: true } },
    { path: '/Ranker', component: Ranker, meta: { requiresAuth: true } },
    { path: '/Ranker/:id', name:'RankerDetail', component: RankerDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater', component: Rater, meta: { requiresAuth: true } },
    { path: '/Rater/:id', name:'RaterDetail', component: RaterDetail, props: true, meta: { requiresAuth: true } },
    { path: '/Rater/:id/:feature', name:'RaterDetailFeature', component: RaterDetailFeature, props: true, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration', name: 'HistoryGenerator', component: HistoryGeneration, meta: { requiresAuth: true } },
    { path : '/HistoryGeneration/:id', name:'HistoryGenerationDetail', component: HistoryGenerationDetail, props: true, meta: { requiresAuth: true } },

    { path: '/AdminDashboard', component: AdminHome, meta: { requiresAuth: true, requiresAdmin: true } }, // Admin-Route
    { path: '/AdminRanker', component: AdminRanker, meta: { requiresAuth: true, requiresAdmin: true } }, // Admin-Route
    { path: '/AdminTester', component: AdminTester, meta: { requiresAuth: true, requiresAdmin: true } }, // Admin-Route

    { path: '/login', component: Login, meta: { requiresAuth: false } },
    { path: '/', redirect: '/login' },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound }, // 404 Route

    { path: '/chat', component: ChatWidget, meta: { requiresAuth: true } }

];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// Navigationswächter
router.beforeEach((to, from, next) => {
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
    const isAuthenticated = localStorage.getItem('token');
    const username = localStorage.getItem('username');

    console.log("Navigating to:", to.path);
    console.log("isAuthenticated:", isAuthenticated);
    console.log("username:", username);
    console.log("isAdmin:", isAdmin(username));

    if (requiresAuth && !isAuthenticated) {
        next('/login');
    } else if (requiresAdmin && !isAdmin(username)) {
        next('/Home');
    } else {
        next();
    }
});


export default router;
