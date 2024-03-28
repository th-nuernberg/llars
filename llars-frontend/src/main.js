import { createApp } from 'vue'
import router from './router/router.js';
import App from './App.vue'

const app = createApp(App)

app.use(router);
//app.component('food-items', FoodItems);
//app.component('animal-collection', AnimalCollection);

app.mount('#app')