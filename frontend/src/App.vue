<template>
  <v-app>
    <v-app-bar density="comfortable" class="appbar-gradient">
      <v-app-bar-title class="d-flex align-center">
        <img :src="urnaSrc" @error="onUrnaError" alt="Urna" class="brand-logo" loading="eager" decoding="async" />
        Prode 2025
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn to="/" variant="text">🏠 Inicio</v-btn>
      <v-btn :to="afterDeadline ? undefined : '/play'" variant="text" :disabled="afterDeadline" :title="afterDeadline ? 'Cerraron los comicios' : 'Jugar'">
        <span v-if="!afterDeadline">🗳️ Jugar</span>
        <span v-else>🔒 Cerrado</span>
      </v-btn>
      <v-btn to="/results" variant="text">📊 Resultados</v-btn>
      <v-btn to="/ranking" variant="text">🏆 Ranking</v-btn>

      <v-menu location="bottom end">
        <template #activator="{ props }">
          <v-btn v-bind="props" variant="text" aria-label="Aportes">
            💵 APORTES
          </v-btn>
        </template>
        <v-card min-width="280">
          <v-list density="comfortable">
            <v-list-item class="text-left" :href="cafecitoUrl" target="_blank" rel="noopener" :disabled="!cafecitoHandle">
              <div class="d-flex align-center w-100">
                <img :src="CAFECITO_IMG" alt="Cafecito" class="list-icon me-2" @error="hideImg" />
                <div class="flex-grow-1">
                  <div class="text-body-2">Invitame un Cafecito</div>
                  <div v-if="cafecitoHandle" class="text-caption text-medium-emphasis">@{{ cafecitoHandle }}</div>
                </div>
                <v-icon icon="mdi-open-in-new" size="14" class="ms-2" />
              </div>
            </v-list-item>
            <v-divider class="my-1" />
            <v-list-item class="text-left">
              <div class="d-flex align-center w-100">
                <img :src="MP_IMG" alt="Mercado Pago" class="list-icon me-2" @error="hideImg" />
                <div class="flex-grow-1">
                  <div class="text-body-2">Alias Mercado Pago</div>
                  <div class="text-caption text-medium-emphasis">{{ mpAlias || 'alias.no.configurado' }}</div>
                </div>
                <v-btn size="small" variant="text" icon="mdi-content-copy" :title="'Copiar alias'" @click="copyAlias" />
              </div>
            </v-list-item>
          </v-list>
        </v-card>
      </v-menu>
    </v-app-bar>
    <v-main class="bg-pattern">
      <router-view />
    </v-main>
    <v-footer class="footer" height="36" elevation="0" app>
      <div class="footer-inner">
        <div class="footer-left">
          <strong>Hecho por </strong>
          <a href="https://github.com/f3d3to" target="_blank" rel="noopener" class="link">@f3d3to</a>
          <span class="sep">•</span>
          <a href="https://github.com/f3d3to/prode-elecciones" target="_blank" rel="noopener" class="link">Repositorio</a>
          <span class="sep">•</span>
          <a href="https://www.linkedin.com/in/federico-j-neuman/" target="_blank" rel="noopener" class="link">LinkedIn</a>
        </div>
        <div class="footer-right">
          <span>MVP 2025</span>
        </div>
      </div>
    </v-footer>
  </v-app>
  <v-snackbar v-model="snack.show" timeout="1800" location="bottom" color="secondary">
    {{ snack.text }}
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const urnaSrc = ref('/urna_voto.png')
function onUrnaError() {
  // Si la PNG es muy grande o no existe, utilizamos el SVG del favicon como fallback
  if (urnaSrc.value !== '/favicon.svg') {
    urnaSrc.value = '/favicon.svg'
  }
}

// Contribuciones: variables configurables por entorno
const cafecitoHandle = (import.meta.env.VITE_CAFECITO || '').toString().trim()
const cafecitoUrl = cafecitoHandle ? `https://cafecito.app/${cafecitoHandle}` : undefined
const mpAlias = (import.meta.env.VITE_MP_ALIAS || '').toString().trim()

// Imagenes de aporte (en public/). Si no existen, se reemplazan por un fallback inline para evitar huecos
const CAFECITO_IMG = '/cafecito.png'
const MP_IMG = '/mercado-pago.png'
const ICON_FALLBACK_SVG = 'data:image/svg+xml;utf8,' +
  encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
    <rect x="1" y="1" width="18" height="18" rx="4" fill="#E5E7EB" stroke="#CBD5E1" />
    <path d="M6 10h8" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`)

const snack = ref({ show: false, text: '' })
async function copyAlias() {
  const text = mpAlias || 'alias.no.configurado'
  try {
    await navigator.clipboard.writeText(text)
    snack.value = { show: true, text: 'Alias copiado al portapapeles' }
  } catch (e: any) {
    snack.value = { show: true, text: e?.message || 'No se pudo copiar el alias' }
  }
}

// Estado de deadline (para deshabilitar navegación a Jugar desde la barra)
const afterDeadline = ref(false)
const q = new URLSearchParams(globalThis.location?.search || '')
let deadlineDt = new Date(String(import.meta.env.VITE_DEADLINE || ''))
const sim = q.get('simulate_deadline')
const override = q.get('deadline')
if (sim === '1') deadlineDt = new Date(Date.now() - 1000)
else if (override) {
  const dt = new Date(override)
  if (!Number.isNaN(dt.getTime())) deadlineDt = dt
}
let deadlineTimer: number | undefined
function updateDeadline() {
  afterDeadline.value = Date.now() >= deadlineDt.getTime()
}
onMounted(() => {
  updateDeadline()
  deadlineTimer = globalThis.setInterval(updateDeadline, 1000)
})
onBeforeUnmount(() => {
  if (deadlineTimer) globalThis.clearInterval(deadlineTimer)
})

function hideImg(e: Event) {
  const t = e.target as HTMLImageElement
  if (!t) return
  // Reemplazar por un placeholder visible en vez de ocultar
  if (!t.dataset.fallbackApplied) {
    t.src = ICON_FALLBACK_SVG
    t.dataset.fallbackApplied = '1'
    t.style.display = ''
  }
}
</script>

<style>
html, body, #app { height: 100%; }
.appbar-gradient {
  background: linear-gradient(90deg, rgba(0,174,239,1) 0%, rgba(0,119,200,1) 60%, rgba(249,192,0,1) 100%) !important;
  color: white !important;
}
.bg-pattern {
  background: radial-gradient(ellipse at top, rgba(0,174,239,0.09), transparent 60%),
              radial-gradient(ellipse at bottom, rgba(249,192,0,0.08), transparent 60%),
              #F5FBFF;
  min-height: calc(100vh - 64px - 36px); /* app bar (64) + footer (36) */
}
.brand-logo {
  height: 22px;
  width: auto;
  margin-right: 8px;
  vertical-align: middle;
  object-fit: contain;
  border-radius: 3px;
}

.list-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.footer { background-color: #F9C000 !important; color: #fff !important; padding: 0 !important; }
.footer-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}
.footer .link {
  color: #ffffff;
  text-decoration: underline;
}
.footer .sep {
  opacity: 0.7;
  margin: 0 8px;
}
.footer-right span {
  opacity: 0.9;
}
</style>
