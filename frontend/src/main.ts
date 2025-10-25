import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import App from './App.vue'
import Home from './pages/Home.vue'
import Play from './pages/Play.vue'
import Results from './pages/Results.vue'
import Ranking from './pages/Ranking.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/play', component: Play },
  { path: '/results', component: Results },
  { path: '/ranking', component: Ranking },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
})

createApp(App).use(createPinia()).use(router).use(vuetify).mount('#app')
