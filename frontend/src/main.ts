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

const argentinaTheme = {
  dark: false,
  colors: {
    primary: '#00AEEF',       // Celeste
    secondary: '#F9C000',     // Amarillo dorado
    accent: '#0077C8',        // Azul bandera
    info: '#4FC3F7',
    success: '#2E7D32',
    warning: '#F9A825',
    error: '#C62828',
    background: '#F5FBFF',
    surface: '#FFFFFF',
  },
}

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'argentina',
    themes: {
      argentina: argentinaTheme as any,
    },
  },
  defaults: {
    VAppBar: { color: 'primary', elevation: 2 },
    VBtn: { rounded: 'lg' },
    VCard: { rounded: 'lg' },
    VChip: { variant: 'tonal' },
    VAlert: { border: 'start', elevation: 0 },
  },
})

createApp(App).use(createPinia()).use(router).use(vuetify).mount('#app')
