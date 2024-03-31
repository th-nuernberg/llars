import {createRouter, createWebHistory} from "vue-router";
import AnimalCollection from "@/components/AnimalCollection.vue";
import FoodItems from "@/components/FoodItems.vue";
import Login from "@/components/Login.vue";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/animals', component: AnimalCollection },
        { path: '/food', component: FoodItems },
        { path: '/login', component: Login},
        { path: '/', redirect: '/login'}
        //{ path: '/', redirect: '/animals',component: Login },
    ]
});

export default router;