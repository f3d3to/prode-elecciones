<template>
  <div class="pa-6 d-flex flex-column align-center text-center">
    <v-avatar size="84" class="mb-3" color="secondary">
      <img src="/flag-ar.svg" alt="Bandera Argentina" width="64" height="42" />
    </v-avatar>
    <h1 class="mb-1 text-primary">Prode Electoral 2025</h1>
    <div class="text-medium-emphasis mb-6">Cierre en: <strong>{{ countdown }}</strong></div>
    <div class="mb-4">
      <v-chip :color="apiOk ? 'success' : 'error'" size="small" variant="tonal">
        {{ apiOk ? '💙 API OK' : '⛔ API FAIL' }}
      </v-chip>
    </div>
    <v-btn color="primary" to="/play">🗳️ Jugar</v-btn>

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

const deadline = new Date(import.meta.env.VITE_DEADLINE)
const countdown = ref('')
let timer: number | undefined
const apiOk = ref(false)
const players = ref<string[]>([])
const totalPlayers = ref(0)
const playersError = ref('')

function update() {
  const now = Date.now()
  const dist = deadline.getTime() - now
  if (dist <= 0) {
    countdown.value = 'Elecciones finalizadas'
    if (timer) {
      globalThis.clearInterval(timer)
    }
    return
  }
  const hours = Math.floor(dist / 1000 / 60 / 60)
  const minutes = Math.floor((dist / 1000 / 60) % 60)
  const seconds = Math.floor((dist / 1000) % 60)
  countdown.value = `${hours}h ${minutes}m ${seconds}s`
}

onMounted(() => {
  update()
  timer = globalThis.setInterval(update, 1000)
  // ping API health once
  const base = import.meta.env.VITE_API_BASE
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
