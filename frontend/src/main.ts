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
import Admin from './pages/Admin.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/play', component: Play },
  { path: '/results', component: Results },
  { path: '/ranking', component: Ranking },
  // Ruta de administración (no enlazada en navegación pública)
  { path: '/admin', component: Admin },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guard de deadline: bloquea /play cuando pasó el cierre
router.beforeEach((to) => {
  try {
    const params = new URLSearchParams(globalThis.location?.search || '')
    const override = params.get('deadline')
    const simulate = params.get('simulate_deadline')
    const envDeadline = String(import.meta.env.VITE_DEADLINE || '')
    let deadline = new Date(envDeadline)
    if (simulate === '1') deadline = new Date(Date.now() - 1000)
    else if (override) {
      const dt = new Date(override)
      if (!Number.isNaN(dt.getTime())) deadline = dt
    }
    const afterDeadline = Date.now() >= deadline.getTime()
    if (to.path === '/play' && afterDeadline) {
      return { path: '/', query: { closed: '1' } }
    }
  } catch {
    // noop
  }
  return true
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
