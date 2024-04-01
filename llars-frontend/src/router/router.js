import { createRouter, createWebHistory } from "vue-router";
import AnimalCollection from "@/components/AnimalCollection.vue";
import FoodItems from "@/components/FoodItems.vue";
import Login from "@/components/Login.vue";
import NotFound from "@/components/NotFound.vue";

const routes = [
    { path: '/animals', component: AnimalCollection, meta: { requiresAuth: true } },
    { path: '/food', component: FoodItems, meta: { requiresAuth: true } },
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
