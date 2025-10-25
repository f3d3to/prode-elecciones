<template>
  <div class="pa-6 mx-auto" style="max-width: 900px;">
    <div class="text-center mb-4">
      <v-avatar size="64" class="mb-2" color="secondary">
        <v-icon icon="mdi-shield-account" size="36" class="text-white" />
      </v-avatar>
      <h2 class="mb-1 text-primary">Administración</h2>
    </div>

    <div v-if="!auth.authenticated" class="mx-auto" style="max-width: 520px;">
      <v-alert v-if="auth.error" type="error" variant="tonal" class="mb-3">{{ auth.error }}</v-alert>
      <v-card class="mb-4">
        <v-card-title>Ingreso de staff</v-card-title>
        <v-card-text>
          <v-text-field v-model="auth.username" label="Usuario" />
          <v-text-field v-model="auth.password" label="Contraseña" type="password" />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" :loading="auth.loading" @click="login">Ingresar</v-btn>
        </v-card-actions>
      </v-card>
    </div>

    <div v-else>
      <v-alert type="success" variant="tonal" class="mb-3">Sesión iniciada como <strong>{{ auth.username }}</strong></v-alert>
      <div class="d-flex gap-2 mb-4">
        <v-btn size="small" variant="tonal" color="primary" @click="loadOverview">Refrescar</v-btn>
        <v-btn size="small" variant="tonal" color="error" @click="logout">Salir</v-btn>
      </div>

      <v-card class="mb-4">
        <v-card-title>Overview</v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-2">
            <v-chip label>Deadline: <strong class="ml-1">{{ overview.deadline || '-' }}</strong></v-chip>
            <v-chip :color="overview.after_deadline ? 'warning' : 'info'" label>Post-deadline: {{ overview.after_deadline ? 'Sí' : 'No' }}</v-chip>
            <v-chip label>Pronósticos: <strong class="ml-1">{{ overview.predictions_completed }}/{{ overview.predictions_total }}</strong></v-chip>
            <v-chip :color="overview.results_published ? 'success' : 'warning'" label>Resultados publicados: {{ overview.results_published ? 'Sí' : 'No' }}</v-chip>
          </div>
        </v-card-text>
      </v-card>

      <v-card class="mb-4">
        <v-card-title>Acciones</v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-2">
            <v-btn color="primary" @click="reprocess" :loading="busy.reprocess">Reprocesar puntajes</v-btn>
            <v-btn color="secondary" :href="csvHref" target="_blank">Exportar ranking CSV</v-btn>
            <v-btn color="warning" @click="retrySheets" :loading="busy.retrySheets">Reintentar Sheets</v-btn>
          </div>
          <div class="text-medium-emphasis mt-3" v-if="lastAction">{{ lastAction }}</div>
        </v-card-text>
      </v-card>

      <v-card>
        <v-card-title>Publicar resultados oficiales</v-card-title>
        <v-card-text>
          <div class="mb-2">
            <v-switch v-model="publish.is_published" color="success" label="Publicar (visible para el público)" />
          </div>
          <v-textarea v-model="publish.payload" auto-grow rows="8" label="JSON de resultados oficiales" hint="Incluye national_percentages, participation, margin_1_2, blanco_nulo_impugnado, total_votes y provinciales" />
          <div class="d-flex gap-2 mt-2">
            <v-btn color="primary" :loading="publish.loading" @click="sendResults">Enviar</v-btn>
            <v-btn variant="text" @click="loadExample">Ejemplo</v-btn>
          </div>
          <div class="text-medium-emphasis mt-2" v-if="publish.msg">{{ publish.msg }}</div>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import axios from 'axios'

const base = import.meta.env.VITE_API_BASE

const auth = reactive({
  authenticated: false,
  username: '',
  password: '',
  loading: false,
  error: '',
})

const overview = reactive({
  deadline: '',
  after_deadline: false,
  predictions_total: 0,
  predictions_completed: 0,
  results_published: false,
})

const busy = reactive({ reprocess: false, retrySheets: false })
const lastAction = ref('')

const csvHref = `${base}/api/admin/export/ranking.csv`

const publish = reactive({ is_published: true, payload: '', loading: false, msg: '' })

async function fetchCsrf() {
  try {
    await axios.get(`${base}/api/admin/csrf`, { withCredentials: true })
  } catch (e: any) {
    lastAction.value = e?.message || 'No se pudo obtener CSRF (puede fallar el próximo POST)'
  }
}

function getCookie(name: string) {
  const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[2]) : ''
}

function csrfHeaders() {
  const token = getCookie('csrftoken')
  return token ? { 'X-CSRFToken': token } : {}
}

async function checkSession() {
  try {
    const { data } = await axios.get(`${base}/api/admin/login`, { withCredentials: true })
    auth.authenticated = !!data.authenticated
    auth.username = data.username
  } catch {
    auth.authenticated = false
  }
}

async function login() {
  auth.loading = true
  auth.error = ''
  try {
    await fetchCsrf()
    const { data } = await axios.post(`${base}/api/admin/login`, { username: auth.username, password: auth.password }, { withCredentials: true, headers: csrfHeaders() })
    auth.authenticated = !!data.authenticated
    auth.username = data.username
    await loadOverview()
  } catch (e: any) {
    auth.error = e?.response?.data?.detail || 'No se pudo iniciar sesión'
  } finally {
    auth.loading = false
  }
}

async function logout() {
  try {
    await axios.post(`${base}/api/admin/logout`, {}, { withCredentials: true, headers: csrfHeaders() })
  } finally {
    auth.authenticated = false
    auth.username = ''
  }
}

async function loadOverview() {
  try {
    const { data } = await axios.get(`${base}/api/admin/overview`, { withCredentials: true })
    Object.assign(overview, data)
  } catch (e: any) {
    lastAction.value = e?.message || 'No se pudo cargar overview'
  }
}

async function reprocess() {
  busy.reprocess = true
  lastAction.value = ''
  try {
    const { data } = await axios.post(`${base}/api/admin/reprocess`, {}, { withCredentials: true, headers: csrfHeaders() })
    lastAction.value = `Reproceso OK (${data.predictions_count})`
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'Error de reproceso'
  } finally {
    busy.reprocess = false
  }
}

async function retrySheets() {
  busy.retrySheets = true
  lastAction.value = ''
  try {
    const { data } = await axios.post(`${base}/api/admin/retry-sheets`, {}, { withCredentials: true, headers: csrfHeaders() })
    lastAction.value = data.detail || 'OK'
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'Error al reintentar Sheets'
  } finally {
    busy.retrySheets = false
  }
}

function loadExample() {
  const example = {
    is_published: true,
    national_percentages: { "LLA": 32.1, "UxP": 31.7, "JxC": 24.3 },
    participation: 72.5,
    margin_1_2: 0.4,
    blanco_nulo_impugnado: 3.2,
    total_votes: 20000000,
    provinciales: {
      "Buenos Aires": { percentages: { "LLA": 30, "UxP": 36, "JxC": 25 }, winner: "UxP" },
      "CABA": { percentages: { "LLA": 27, "UxP": 22, "JxC": 45 }, winner: "JxC" },
    }
  }
  publish.payload = JSON.stringify(example, null, 2)
}

async function sendResults() {
  publish.loading = true
  publish.msg = ''
  try {
    await fetchCsrf()
    const body = JSON.parse(publish.payload || '{}')
    body.is_published = publish.is_published
    await axios.post(`${base}/api/results`, body, { withCredentials: true, headers: csrfHeaders() })
    publish.msg = 'Resultados cargados correctamente'
    await loadOverview()
  } catch (e: any) {
    publish.msg = e?.response?.data?.detail || 'Error al cargar resultados (verificar JSON/validaciones)'
  } finally {
    publish.loading = false
  }
}

onMounted(async () => {
  await checkSession()
  if (auth.authenticated) await loadOverview()
})
</script>