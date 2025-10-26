<template>
  <div class="pa-6">
    <div class="text-center mb-4">
      <v-avatar size="72" class="mb-2" color="secondary">
        <v-icon icon="mdi-trophy-variant-outline" size="42" class="text-white" />
      </v-avatar>
      <h2 class="mb-1 text-primary">Ranking</h2>
    </div>

    <div class="mx-auto mb-4" style="max-width: 720px;">
      <v-text-field v-model="query" density="comfortable" variant="outlined" prepend-inner-icon="mdi-magnify" label="Buscar por nombre o email" clearable @keyup.enter="fetchRanking" @click:clear="onClear" />
    </div>

    <div v-if="loading" class="d-flex justify-center my-6">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <div v-else-if="error" class="mx-auto" style="max-width: 720px;">
      <v-alert type="info" variant="tonal">
        {{ error }}
      </v-alert>
    </div>

    <div v-else class="mx-auto" style="max-width: 980px;">
      <v-card elevation="1">
        <v-card-text>
          <div class="text-medium-emphasis mb-2">{{ items.length }} participantes<span v-if="generatedAt"> • Generado: {{ generatedAt }}</span></div>
          <v-alert v-if="items.length === 0" type="info" variant="tonal">
            A la espera de resultados oficiales o no hay participantes para mostrar.
          </v-alert>
          <v-table v-else density="comfortable">
            <thead>
              <tr>
                <th scope="col" class="text-left">Pos.</th>
                <th scope="col" class="text-left">Usuario</th>
                <th scope="col" class="text-left">Email</th>
                <th scope="col" class="text-left">Puntaje</th>
                <th scope="col" class="text-left">Bonus</th>
                <th scope="col" class="text-left">Envío</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in items" :key="it.email">
                <td>{{ it.position }}</td>
                <td>{{ it.username }}</td>
                <td class="text-medium-emphasis">{{ it.email }}</td>
                <td><strong>{{ it.score.toFixed(2) }}</strong></td>
                <td>{{ it.bonus }}</td>
                <td class="text-medium-emphasis">{{ fmtDate(it.submitted_at) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

type RankItem = {
  position: number
  username: string
  email: string
  score: number
  bonus: number
  submitted_at: string
}

const items = ref<RankItem[]>([])
const loading = ref(true)
const error = ref('')
const generatedAt = ref('')
const query = ref('')

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('es-AR')
  } catch {
    return iso
  }
}

async function fetchRanking() {
  loading.value = true
  error.value = ''
  const base = import.meta.env.VITE_API_BASE
  try {
    const url = query.value ? `${base}/api/ranking?q=${encodeURIComponent(query.value)}` : `${base}/api/ranking`
    const { data } = await axios.get(url)
    items.value = data.results || []
    generatedAt.value = new Date(data.generated_at || Date.now()).toLocaleString('es-AR')
  } catch (e: any) {
    items.value = []
    generatedAt.value = ''
    error.value = e?.response?.data?.detail || 'A la espera de resultados oficiales'
  } finally {
    loading.value = false
  }
}

function onClear() {
  query.value = ''
  fetchRanking()
}

onMounted(fetchRanking)
</script>
