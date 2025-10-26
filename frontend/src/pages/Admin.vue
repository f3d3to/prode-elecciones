<template>
  <div class="pa-6 mx-auto" style="max-width: 900px;">
    <div class="text-center mb-4">
      <v-avatar size="64" class="mb-2" color="secondary">
        <v-icon icon="mdi-shield-account" size="36" class="text-white" />
      </v-avatar>
      <h2 class="mb-1 text-primary">Ingresos</h2>
    </div>

    <div v-if="!auth.authenticated" class="mx-auto" style="max-width: 520px;">
      <v-alert v-if="auth.error" type="error" variant="tonal" class="mb-3">{{ auth.error }}</v-alert>
      <v-card class="mb-4">
        <v-card-title>Ingreso</v-card-title>
        <v-card-text>
          <v-switch v-model="auth.useToken" color="primary" label="Usar token (sin cookies)" density="compact" class="mb-2" />
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

      <v-card class="mb-4">
        <v-card-title>Limpiar datos de prueba</v-card-title>
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-2">Ejecuta el purge en el mismo servicio (gratis). No borra datos reales salvo que marques la opción peligrosa.</v-alert>
          <v-switch v-model="purge.dry_run" label="Dry-run (simular)" color="primary" />
          <v-switch v-model="purge.include_official" label="Incluir resultados oficiales NO publicados" color="warning" />
          <v-switch v-model="purge.purge_all_official" label="[PELIGRO] Eliminar TODOS los resultados oficiales" color="error" />
          <div class="d-flex gap-2 mt-2">
            <v-btn color="error" :loading="busy.purge" @click="runPurge">Ejecutar purge</v-btn>
          </div>
          <v-textarea v-model="purge.output" class="mt-2" auto-grow rows="6" label="Salida" readonly />
        </v-card-text>
      </v-card>

      <v-card class="mb-4">
        <v-card-title>Gestionar predicciones</v-card-title>
        <v-card-text>
          <div class="d-flex gap-2 mb-2" style="max-width:600px;">
            <v-text-field v-model="predSearch" label="Buscar por nombre o email" density="comfortable" clearable @click:clear="() => { predSearch = ''; loadPredictions() }" @keyup.enter="loadPredictions" />
            <v-btn color="primary" @click="loadPredictions">Buscar</v-btn>
          </div>
          <v-table density="comfortable" v-if="predictions.length">
            <thead>
              <tr>
                <th scope="col">ID</th><th scope="col">Usuario</th><th scope="col">Email</th><th scope="col">Actualizado</th><th scope="col"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in predictions" :key="p.id">
                <td>{{ p.id }}</td>
                <td>{{ p.username }}</td>
                <td class="text-medium-emphasis">{{ p.email }}</td>
                <td class="text-medium-emphasis">{{ new Date(p.updated_at).toLocaleString('es-AR') }}</td>
                <td>
                  <v-btn size="x-small" color="error" variant="tonal" @click="deletePrediction(p.id)">Eliminar</v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
          <v-alert v-else type="info" variant="tonal">Sin resultados para mostrar</v-alert>
        </v-card-text>
      </v-card>

      <v-card class="mb-6">
        <v-card-title>Resultados oficiales</v-card-title>
        <v-card-text>
          <v-table density="comfortable" v-if="resultsList.length">
            <thead>
              <tr>
                <th scope="col">ID</th><th scope="col">Publicado</th><th scope="col">Publicado en</th><th scope="col">Creado</th><th scope="col"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in resultsList" :key="r.id">
                <td>{{ r.id }}</td>
                <td>{{ r.is_published ? 'Sí' : 'No' }}</td>
                <td class="text-medium-emphasis">{{ r.published_at ? new Date(r.published_at).toLocaleString('es-AR') : '—' }}</td>
                <td class="text-medium-emphasis">{{ new Date(r.created_at).toLocaleString('es-AR') }}</td>
                <td>
                  <v-btn v-if="!r.is_published" size="x-small" color="error" variant="tonal" @click="deleteResult(r.id)">Eliminar draft</v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
          <v-alert v-else type="info" variant="tonal">Sin resultados cargados</v-alert>
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
  useToken: false,
  token: '',
})

const overview = reactive({
  deadline: '',
  after_deadline: false,
  predictions_total: 0,
  predictions_completed: 0,
  results_published: false,
})

const busy = reactive({ reprocess: false, retrySheets: false, purge: false })
const lastAction = ref('')

const csvHref = `${base}/api/admin/export/ranking.csv`

const publish = reactive({ is_published: true, payload: '', loading: false, msg: '' })
const purge = reactive({ dry_run: true, include_official: false, purge_all_official: false, output: '' })
const predSearch = ref('')
const predictions = ref<Array<{id:number,username:string,email:string,updated_at:string}>>([])
const resultsList = ref<Array<{id:number,is_published:boolean,published_at:string|null,created_at:string}>>([])

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

function authHeaders() {
  const headers: any = {}
  if (auth.useToken && auth.token) headers['Authorization'] = `Bearer ${auth.token}`
  return headers
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
    if (auth.useToken) {
      const { data } = await axios.post(`${base}/api/admin/token`, { username: auth.username, password: auth.password })
      auth.token = data.token
      auth.authenticated = true
      auth.username = data.username
    } else {
      await fetchCsrf()
      const { data } = await axios.post(`${base}/api/admin/login`, { username: auth.username, password: auth.password }, { withCredentials: true, headers: csrfHeaders() })
      auth.authenticated = !!data.authenticated
      auth.username = data.username
    }
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
    const { data } = await axios.get(`${base}/api/admin/overview`, { withCredentials: true, headers: authHeaders() })
    Object.assign(overview, data)
  } catch (e: any) {
    lastAction.value = e?.message || 'No se pudo cargar overview'
  }
}

async function reprocess() {
  busy.reprocess = true
  lastAction.value = ''
  try {
    const headers = { ...csrfHeaders(), ...authHeaders() }
    const { data } = await axios.post(`${base}/api/admin/reprocess`, {}, { withCredentials: true, headers })
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
    const headers = { ...csrfHeaders(), ...authHeaders() }
    const { data } = await axios.post(`${base}/api/admin/retry-sheets`, {}, { withCredentials: true, headers })
    lastAction.value = data.detail || 'OK'
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'Error al reintentar Sheets'
  } finally {
    busy.retrySheets = false
  }
}

async function runPurge() {
  busy.purge = true as any
  purge.output = ''
  try {
    await fetchCsrf()
    const { data } = await axios.post(`${base}/api/admin/purge`, {
      dry_run: purge.dry_run,
      include_official: purge.include_official,
      purge_all_official: purge.purge_all_official,
    }, { withCredentials: true, headers: { ...csrfHeaders(), ...authHeaders() } })
    purge.output = data.output || JSON.stringify(data)
  } catch (e: any) {
    purge.output = e?.response?.data?.detail || e?.message || 'Error al purgar'
  } finally {
    busy.purge = false as any
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
    await axios.post(`${base}/api/results`, body, { withCredentials: true, headers: { ...csrfHeaders(), ...authHeaders() } })
    publish.msg = 'Resultados cargados correctamente'
    await loadOverview()
  } catch (e: any) {
    publish.msg = e?.response?.data?.detail || 'Error al cargar resultados (verificar JSON/validaciones)'
  } finally {
    publish.loading = false
  }
}

async function loadPredictions() {
  try {
    const { data } = await axios.get(`${base}/api/admin/predictions`, { params: { q: predSearch.value || undefined }, withCredentials: true, headers: authHeaders() })
    predictions.value = data.results || []
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'No se pudo cargar predicciones'
  }
}

async function deletePrediction(id: number) {
  try {
    await fetchCsrf()
    await axios.delete(`${base}/api/admin/predictions`, { data: { ids: [id] }, withCredentials: true, headers: { ...csrfHeaders(), ...authHeaders() } })
    predictions.value = predictions.value.filter(p => p.id !== id)
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'No se pudo eliminar la predicción'
  }
}

async function loadResultsList() {
  try {
    const { data } = await axios.get(`${base}/api/admin/results`, { withCredentials: true, headers: authHeaders() })
    resultsList.value = data.results || []
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'No se pudo cargar resultados'
  }
}

async function deleteResult(id: number) {
  try {
    await fetchCsrf()
    await axios.delete(`${base}/api/admin/results`, { data: { id }, withCredentials: true, headers: { ...csrfHeaders(), ...authHeaders() } })
    resultsList.value = resultsList.value.filter(r => r.id !== id)
  } catch (e: any) {
    lastAction.value = e?.response?.data?.detail || 'No se pudo eliminar el resultado'
  }
}

onMounted(async () => {
  await checkSession()
  if (auth.authenticated) {
    await loadOverview()
    await loadPredictions()
    await loadResultsList()
  }
})
</script>