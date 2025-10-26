<template>
  <div class="pa-6">
    <div class="text-center mb-4">
      <v-avatar size="72" class="mb-2" color="secondary">
        <v-icon icon="mdi-chart-bar" size="42" class="text-white" />
      </v-avatar>
      <h2 class="mb-1 text-primary">Resultados</h2>
    </div>

    <div v-if="loading" class="d-flex justify-center my-6">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <div v-else-if="error" class="mx-auto" style="max-width: 720px;">
      <v-alert type="info" variant="tonal">
        A la espera de resultados oficiales
      </v-alert>
    </div>

    <div v-else class="mx-auto" style="max-width: 980px;">
      <v-card class="mb-6" elevation="1">
        <v-card-title>Panel Nacional</v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-3 mb-4">
            <v-chip v-for="(pct, fuerza) in results.national_percentages" :key="fuerza" color="primary" label>
              {{ fuerza }}: <strong class="ml-1">{{ fmtPct(pct) }}</strong>
            </v-chip>
          </div>
          <div class="d-flex flex-wrap gap-3">
            <v-chip color="secondary" label>Participación: <strong class="ml-1">{{ fmtPct(results.participation) }}</strong></v-chip>
            <v-chip color="secondary" label>Margen 1.º-2.º: <strong class="ml-1">{{ fmtPct(results.margin_1_2) }}</strong></v-chip>
            <v-chip color="secondary" label>Blanco/Nulo/Imp.: <strong class="ml-1">{{ fmtPct(results.blanco_nulo_impugnado) }}</strong></v-chip>
            <v-chip color="secondary" label>Total de votos: <strong class="ml-1">{{ fmtInt(results.total_votes) }}</strong></v-chip>
          </div>
        </v-card-text>
      </v-card>

      <v-card elevation="1">
        <v-card-title>Resultados por provincia</v-card-title>
        <v-card-text>
          <v-table density="comfortable">
            <thead>
              <tr>
                <th scope="col" class="text-left">Provincia</th>
                <th scope="col" class="text-left">Ganador</th>
                <th scope="col" class="text-left">Porcentajes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="prov in provinciasOrdenadas" :key="prov">
                <td>{{ prov }}</td>
                <td>{{ provinciales[prov]?.winner || '-' }}</td>
                <td>
                  <div class="d-flex flex-wrap gap-2">
                    <v-chip v-for="(pct, fuerza) in provinciales[prov]?.percentages || {}" :key="prov + '-' + fuerza" size="small" variant="tonal">
                      {{ fuerza }}: {{ fmtPct(pct) }}
                    </v-chip>
                  </div>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </div>
  </div>

</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

type Provinciales = Record<string, { percentages?: Record<string, number>, winner?: string }>

const loading = ref(true)
const error = ref('')
const results = ref({
  national_percentages: {} as Record<string, number>,
  participation: null as number | null,
  margin_1_2: null as number | null,
  blanco_nulo_impugnado: null as number | null,
  total_votes: null as number | null,
  provinciales: {} as Provinciales,
})

const provinciales = computed(() => results.value.provinciales)
const provinciasOrdenadas = computed(() => Object.keys(provinciales.value || {}).sort())

function fmtPct(v: any) {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return `${n.toFixed(1)}%`
}
function fmtInt(v: any) {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return n.toLocaleString('es-AR')
}

onMounted(async () => {
  const base = String(import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '')
  try {
    const { data } = await axios.get(`${base}/api/results`)
    results.value = {
      national_percentages: data.national_percentages || {},
      participation: data.participation ?? null,
      margin_1_2: data.margin_1_2 ?? null,
      blanco_nulo_impugnado: data.blanco_nulo_impugnado ?? null,
      total_votes: data.total_votes ?? null,
      provinciales: data.provinciales || {},
    }
  } catch (e: any) {
    // Guardamos un estado simple para mostrar el aviso informativo
    error.value = e?.response?.data?.detail || 'no-results'
  } finally {
    loading.value = false
  }
})
</script>
