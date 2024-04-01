import { createRouter, createWebHistory } from "vue-router";
import Login from "@/components/Login.vue";
import Home from "@/components/Home.vue";
import NotFound from "@/components/NotFound.vue";
import Ranker from "@/components/Ranker/Ranker.vue";
import Rater from "@/components/Rater/Rater.vue";

const routes = [
    { path: '/Home', component: Home, meta: { requiresAuth: true } },
    { path: '/Ranker', component: Ranker, meta: { requiresAuth: true } },
    { path: '/Rater', component: Rater, meta: { requiresAuth: true } },
    { path: '/login', component: Login, meta: { requiresAuth: false } },

    { path: '/', redirect: '/login' },
   { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound } // 404 Route
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// Navigationswächter
router.beforeEach((to, from, next) => {
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const isAuthenticated = localStorage.getItem('token');

    if (requiresAuth && !isAuthenticated) {
        next('/login');
    } else {
        next();
    }
});

export default router;
