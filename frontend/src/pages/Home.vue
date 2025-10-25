<template>
  <div class="pa-6 d-flex flex-column align-center text-center">
    <h1 class="mb-2">Prode Electoral 2025</h1>
    <p class="mb-6">Cierre en: <strong>{{ countdown }}</strong></p>
    <div class="mb-4">
      <v-chip :color="apiOk ? 'green' : 'red'" size="small" variant="flat">
        API {{ apiOk ? 'OK' : 'FAIL' }}
      </v-chip>
    </div>
    <v-btn color="primary" to="/play">Jugar</v-btn>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

const deadline = new Date(import.meta.env.VITE_DEADLINE)
const countdown = ref('')
let timer: number | undefined
const apiOk = ref(false)

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
})

onBeforeUnmount(() => {
  if (timer) globalThis.clearInterval(timer)
})
</script>
