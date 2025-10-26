<template>
  <div class="pa-6 d-flex flex-column align-center text-center">
    <v-avatar size="84" class="mb-3" color="secondary">
      <img src="/flag-ar.svg" alt="Bandera Argentina" width="64" height="42" />
    </v-avatar>
    <h1 class="mb-1 text-primary">Prode Electoral 2025</h1>
    <div class="mb-6" style="width: 100%; max-width: 560px;">
      <v-alert :type="deadlineType" variant="tonal" border="start" :icon="deadlineIcon" class="deadline-alert">
        <div class="d-flex align-center justify-center">
          <strong class="me-2">{{ deadlineLabel }}</strong>
          <span class="deadline-time">{{ countdown }}</span>
        </div>
        <div v-if="afterDeadline" class="text-caption mt-1 text-error">Cerraron los comicios.</div>
        <div v-if="simulatedNote" class="text-caption mt-1">{{ simulatedNote }}</div>
      </v-alert>
    </div>
    <div class="mb-4">
      <v-chip :color="apiOk ? 'success' : 'error'" size="small" variant="tonal">
        {{ apiOk ? '💙 API OK' : '⛔ API FAIL' }}
      </v-chip>
    </div>
    <v-btn color="primary" to="/play" :disabled="afterDeadline" :title="afterDeadline ? 'Cerraron los comicios' : 'Jugar'">
      <span v-if="!afterDeadline">🗳️ Jugar</span>
      <span v-else>🔒 Edición cerrada</span>
    </v-btn>

    <div class="mt-8" style="max-width: 720px;">
  <h3 class="mb-2">Participantes</h3>
      <div v-if="playersError" class="mb-2">
        <v-alert type="warning" variant="tonal">No pudimos cargar la lista de participantes.</v-alert>
      </div>
      <div v-else>
        <div class="text-medium-emphasis mb-2">{{ players.length }} completaron el prode • Total: {{ totalPlayers }}</div>
        <div class="d-flex flex-wrap justify-center gap-2">
          <v-chip v-for="u in players" :key="u" class="ma-1" size="small" color="primary" variant="tonal">
            {{ u }}
          </v-chip>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

// Deadline base y simulación (solo en dev):
// - ?simulate_deadline=1 -> fuerza deadline pasado
// - ?deadline=ISO-UTC -> sobreescribe fecha
const params = new URLSearchParams(globalThis.location?.search || '')
const baseDeadlineStr = String(import.meta.env.VITE_DEADLINE || '')
let initialDeadline = new Date(baseDeadlineStr)
let simulatedNote = ref('')
const afterDeadline = ref(false)
const closedByGuard = params.get('closed') === '1'
// Simulación habilitada siempre por URL para facilitar pruebas
const sim = params.get('simulate_deadline')
const override = params.get('deadline')
if (sim === '1') {
  initialDeadline = new Date(Date.now() - 1000)
  simulatedNote.value = 'Modo simulación: deadline ya vencido (simulate_deadline=1)'
} else if (override) {
  const dt = new Date(override)
  if (!Number.isNaN(dt.getTime())) {
    initialDeadline = dt
    simulatedNote.value = 'Modo simulación: deadline sobreescrito por URL'
  }
}

const deadline = initialDeadline
const countdown = ref('')
let timer: number | undefined
const apiOk = ref(false)
const players = ref<string[]>([])
const totalPlayers = ref(0)
const playersError = ref('')

const deadlineType = ref<'info' | 'warning' | 'error'>('info')
const deadlineIcon = ref('mdi-timer-outline')
const deadlineLabel = ref('Cierre en')

function update() {
  const now = Date.now()
  const dist = deadline.getTime() - now
  if (dist <= 0) {
    countdown.value = 'Elecciones finalizadas'
    deadlineLabel.value = '⏰ Elecciones finalizadas'
    deadlineType.value = 'error'
    deadlineIcon.value = 'mdi-lock'
    afterDeadline.value = true
    if (timer) {
      globalThis.clearInterval(timer)
    }
    return
  }
  const days = Math.floor(dist / 1000 / 60 / 60 / 24)
  const hours = Math.floor((dist / 1000 / 60 / 60) % 24)
  const minutes = Math.floor((dist / 1000 / 60) % 60)
  const seconds = Math.floor((dist / 1000) % 60)
  const parts = [] as string[]
  if (days > 0) parts.push(`${days}d`)
  parts.push(`${hours}h`, `${minutes}m`, `${seconds}s`)
  countdown.value = parts.join(' ')

  // Estética según cercanía
  const hoursLeft = dist / 1000 / 60 / 60
  if (hoursLeft <= 1) {
    deadlineType.value = 'error'
    deadlineIcon.value = 'mdi-timer-off'
    afterDeadline.value = false
  } else if (hoursLeft <= 24) {
    deadlineType.value = 'warning'
    deadlineIcon.value = 'mdi-timer-alert'
    afterDeadline.value = false
  } else {
    deadlineType.value = 'info'
    deadlineIcon.value = 'mdi-timer-outline'
    afterDeadline.value = false
  }
}

onMounted(() => {
  update()
  timer = globalThis.setInterval(update, 1000)
  if (closedByGuard) simulatedNote.value = 'Redirigido: cerraron los comicios.'
  // ping API health once
  const base = String(import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '')
  axios.get(`${base}/api/health`).then(() => apiOk.value = true).catch(() => apiOk.value = false)
  // fetch players
  axios.get(`${base}/api/players`).then((res) => {
    players.value = res.data?.usernames || []
    totalPlayers.value = res.data?.count_total || players.value.length
  }).catch(() => {
    playersError.value = 'error'
  })
})

onBeforeUnmount(() => {
  if (timer) globalThis.clearInterval(timer)
})
</script>

<style scoped>
.deadline-alert {
  font-size: 1.05rem;
}
.deadline-time {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
</style>
