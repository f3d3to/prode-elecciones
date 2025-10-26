<template>
  <div class="pa-4">
    <div class="d-flex align-center mb-3">
      <v-avatar size="40" class="mr-3" color="secondary"><span style="font-size:22px;">🗳️</span></v-avatar>
      <h2 class="mb-0 text-primary">Pronóstico (MVP)</h2>
    </div>
    <v-alert v-if="afterDeadline" type="error" variant="tonal" class="mb-3">
      Cerraron los comicios — edición deshabilitada.
    </v-alert>

    <!-- Identificación modal -->
    <v-dialog v-model="showIdDialog" persistent max-width="520">
      <v-card>
        <v-card-title>Identificación</v-card-title>
        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-3">Ingresá nombre y email para precargar/crear tu pronóstico.</v-alert>
          <v-text-field v-model="form.username" label="Nombre" required :disabled="afterDeadline"></v-text-field>
          <v-text-field v-model="form.email" label="Email" required type="email" :disabled="afterDeadline" @blur="normalizeEmail"></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showIdDialog = false">Cerrar</v-btn>
          <v-btn color="primary" :disabled="!canContinueId || afterDeadline" :loading="idLoading" @click="confirmIdentification">Continuar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Stepper -->
  <v-stepper v-model="step" color="primary">
      <v-stepper-header>
        <v-stepper-item :value="1" title="Identificación" :complete="identified" />
        <v-divider></v-divider>
  <v-stepper-item :value="2" title="Nacional" :disabled="!identified || afterDeadline" />
        <v-divider></v-divider>
  <v-stepper-item :value="3" title="Provinciales" :disabled="!identified || afterDeadline" />
        <v-divider></v-divider>
  <v-stepper-item :value="4" title="Bonus y Resumen" :disabled="!identified || afterDeadline" />
      </v-stepper-header>

      <v-stepper-window>
        <!-- Paso 1: Identificación -->
        <v-stepper-window-item :value="1">
          <v-alert type="info" class="mb-4">Usá el diálogo para identificarte. Podés reabrirlo con el botón abajo.</v-alert>
          <v-alert v-if="idNotice" type="success" variant="tonal" class="mb-3">{{ idNotice }}</v-alert>
          <v-btn @click="showIdDialog = true" color="primary" :disabled="afterDeadline">Identificarme</v-btn>
          <div v-if="identified" class="mt-4">
            <strong>Jugador:</strong> {{ form.username }} — {{ form.email }}
          </div>
          <div class="mt-6">
            <v-btn color="primary" :disabled="!identified" @click="step = 2">Ir a Nacional</v-btn>
          </div>
        </v-stepper-window-item>

        <!-- Paso 2: Nacional -->
        <v-stepper-window-item :value="2">
          <v-card variant="outlined" class="mb-4">
            <v-card-text>
              <v-form @submit.prevent="goToSummary">
            <h3 class="mb-2">Top-3 fuerzas</h3>
            <v-select v-model="form.top3" :items="fuerzas" label="Seleccioná hasta 3" multiple chips :counter="3" :rules="[max3]" :disabled="afterDeadline" />

            <v-divider class="my-4"></v-divider>
            <h3>Porcentajes nacionales</h3>
            <div class="d-flex flex-wrap gap-4">
              <div v-for="f in fuerzas" :key="f" style="width: 220px;">
                <v-text-field type="number" min="0" max="100" step="0.1" :label="f" v-model.number="form.national_percentages[f]" :disabled="afterDeadline" />
              </div>
            </div>
            <div class="mt-2">Total: <strong :class="{ 'text-error': totalPercent < 95 || totalPercent > 105 }">{{ totalPercent.toFixed(1) }}%</strong> (ideal ≈ 100%)</div>

            <v-row class="mt-2" dense>
              <v-col cols="12" md="4">
                <v-text-field type="number" min="0" max="100" step="0.1" label="Participación (%)" v-model.number="form.participation" :disabled="afterDeadline" />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field type="number" min="0" max="100" step="0.1" label="Margen 1° vs 2° (%)" v-model.number="form.margin_1_2" :disabled="afterDeadline" />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field type="number" min="0" max="100" step="0.1" label="Blanco/Nulo/Impugnado (%)" v-model.number="form.blanco_nulo_impugnado" :disabled="afterDeadline" />
              </v-col>
            </v-row>
            <v-row class="mt-1" dense>
              <v-col cols="12" md="4">
                <v-text-field type="number" min="0" step="1" label="Total de votos (opcional)" v-model.number="form.total_votes" :disabled="afterDeadline" />
              </v-col>
            </v-row>

            <div class="my-4 d-flex align-center gap-3">
              <v-btn variant="text" @click="step = 1">← Atrás</v-btn>
              <v-spacer />
              <v-btn color="primary" @click="step = 3" :disabled="afterDeadline">Continuar →</v-btn>
            </div>
              </v-form>
            </v-card-text>
          </v-card>
        </v-stepper-window-item>

        <!-- Paso 3: Provinciales -->
        <v-stepper-window-item :value="3">
          <div class="mb-4">
            <h3>Pronóstico por provincia</h3>
            <div class="text-body-2">Ingresá porcentajes por fuerza y elegí la fuerza ganadora para cada provincia. La suma ideal por provincia es ≈ 100%.</div>
          </div>

          <div class="d-flex flex-column gap-4">
            <v-card v-for="prov in provincias" :key="prov" variant="outlined">
              <v-card-title class="d-flex align-center justify-space-between">
                <span>{{ prov }}</span>
                <span class="text-caption">Total: <strong :class="{ 'text-error': provTotal(prov) < 95 || provTotal(prov) > 105 }">{{ provTotal(prov).toFixed(1) }}%</strong></span>
              </v-card-title>
              <v-card-text>
                <v-row dense>
                  <v-col v-for="f in fuerzas" :key="f" cols="12" md="3">
                    <v-text-field type="number" min="0" max="100" step="0.1" :label="f" :disabled="afterDeadline"
                      v-model.number="form.provinciales[prov].porcentajes[f]" />
                  </v-col>
                </v-row>
                <div class="mt-2" style="max-width: 360px;">
                  <v-select :items="fuerzas" label="Ganador" v-model="form.provinciales[prov].winner" :disabled="afterDeadline" />
                </div>
              </v-card-text>
            </v-card>
          </div>

          <div class="my-4 d-flex align-center gap-3">
            <v-btn variant="text" @click="step = 2">← Atrás</v-btn>
            <v-spacer />
            <v-btn color="primary" @click="step = 4" :disabled="afterDeadline">Continuar →</v-btn>
          </div>
        </v-stepper-window-item>

        <!-- Paso 4: Bonus y Resumen -->
        <v-stepper-window-item :value="4">
          <h3 class="mb-2">Bonus y Resumen</h3>
          <v-alert v-if="afterDeadline" type="warning" class="mb-3">Elecciones finalizadas: edición deshabilitada.</v-alert>
          <div class="text-body-2 mb-4">
            <div><strong>Jugador:</strong> {{ form.username }} — {{ form.email }}</div>
          </div>

          <v-card variant="outlined" class="mb-4">
            <v-card-title>Nacional</v-card-title>
            <v-card-text>
              <div class="mb-2"><strong>Top-3:</strong> {{ form.top3.join(', ') || '—' }}</div>
              <v-row dense class="mb-1">
                <v-col cols="12" md="3"><strong>Participación:</strong> {{ form.participation ?? '—' }}<span v-if="form.participation != null">%</span></v-col>
                <v-col cols="12" md="3"><strong>Margen 1° vs 2°:</strong> {{ form.margin_1_2 ?? '—' }}<span v-if="form.margin_1_2 != null">%</span></v-col>
                <v-col cols="12" md="3"><strong>Blanco/Nulo:</strong> {{ form.blanco_nulo_impugnado ?? '—' }}<span v-if="form.blanco_nulo_impugnado != null">%</span></v-col>
                <v-col cols="12" md="3"><strong>Total votos:</strong> {{ form.total_votes ?? '—' }}</v-col>
              </v-row>
              <div class="mb-1"><strong>Total nacional:</strong> {{ totalPercent.toFixed(1) }}%</div>
              <div class="d-flex flex-wrap gap-3">
                <v-chip v-for="it in nationalSorted" :key="it.force" class="ma-1" size="small" variant="tonal">
                  {{ it.force }}: {{ it.value.toFixed(1) }}%
                </v-chip>
              </div>
            </v-card-text>
          </v-card>

          <v-card variant="outlined" class="mb-4">
            <v-card-title>Bonus y especiales</v-card-title>
            <v-card-text>
              <v-row dense>
                <v-col cols="12" md="6">
                  <v-select :items="provincias" label="Provincia más reñida" v-model="form.bonus.mas_renida" :disabled="afterDeadline" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select :items="provincias" label="Cambia el ganador vs 2023" v-model="form.bonus.cambia_ganador" :disabled="afterDeadline" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select :items="provincias" label="FIT con mayor porcentaje" v-model="form.bonus.fit_mayor" :disabled="afterDeadline" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select :items="provincias" label="LLA donde más crece" v-model="form.bonus.lla_mas_crece" :disabled="afterDeadline" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select :items="provincias" label="Fuerza Patria con mayor %" v-model="form.bonus.fuerza_patria_mayor" :disabled="afterDeadline" />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card variant="outlined" class="mb-4">
            <v-card-title>Provinciales</v-card-title>
            <v-card-text>
              <div class="mb-2"><strong>Prov. completas:</strong> {{ provsCompleted }} / {{ provincias.length }}</div>
              <div class="d-flex flex-wrap gap-3">
                <v-chip v-for="row in provincesWinners" :key="row.province" class="ma-1" size="small" color="primary" variant="tonal">
                  {{ row.province }}: {{ row.winner || '—' }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>

          <div class="my-4 d-flex align-center gap-3">
            <v-btn variant="text" @click="step = 3">← Atrás</v-btn>
            <v-spacer />
            <v-btn color="primary" :loading="loading" @click="save" :disabled="afterDeadline">💾 Guardar</v-btn>
          </div>
          <div class="mt-2" v-if="savedAt">
            Guardado a las {{ savedAt }}
            <v-chip v-if="syncPending" size="x-small" color="orange" class="ml-2" variant="flat">Pendiente de sync</v-chip>
            <v-chip v-else size="x-small" color="green" class="ml-2" variant="flat">Sincronizado</v-chip>
          </div>
          <v-alert type="error" v-if="error" class="mt-3">{{ error }}</v-alert>
        </v-stepper-window-item>
      </v-stepper-window>
    </v-stepper>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed, watch } from 'vue'
import axios from 'axios'

const fuerzas = ref<string[]>([])
const provincias = ref<string[]>([])
const loading = ref(false)
const savedAt = ref('')
const error = ref('')
const idLoading = ref(false)
const identified = ref(false)
const showIdDialog = ref(false)
const idNotice = ref('')
const step = ref(1)
const afterDeadline = ref(false)
const syncPending = ref(false)

const form = reactive({
  username: '',
  email: '',
  top3: [] as string[],
  national_percentages: {} as Record<string, number>,
  participation: undefined as number | undefined,
  margin_1_2: undefined as number | undefined,
  blanco_nulo_impugnado: undefined as number | undefined,
  total_votes: undefined as number | undefined,
  provinciales: {} as Record<string, { porcentajes: Record<string, number>, winner?: string }>,
  bonus: {
    mas_renida: undefined as string | undefined,
    cambia_ganador: undefined as string | undefined,
    fit_mayor: undefined as string | undefined,
    lla_mas_crece: undefined as string | undefined,
    fuerza_patria_mayor: undefined as string | undefined,
  },
})

const totalPercent = computed(() => Object.values(form.national_percentages).reduce((a, b) => a + (Number(b) || 0), 0))

const nationalSorted = computed(() => {
  const list = Object.entries(form.national_percentages).map(([force, value]) => ({ force, value: Number(value) || 0 }))
  return list.sort((a, b) => b.value - a.value)
})

function max3(val: unknown) {
  return Array.isArray(val) && val.length <= 3 || 'Máximo 3 fuerzas'
}

async function loadMetadata() {
  const base = import.meta.env.VITE_API_BASE
  const { data } = await axios.get(`${base}/api/metadata`)
  fuerzas.value = data.fuerzas || []
  provincias.value = data.provincias || []
  if (data.deadline) {
    const dl = new Date(data.deadline)
    afterDeadline.value = Date.now() >= dl.getTime()
  }
  // init percentages for inputs
  for (const f of fuerzas.value) {
    if (!(f in form.national_percentages)) form.national_percentages[f] = 0
  }
  // init provinciales structure
  for (const prov of provincias.value) {
    if (!form.provinciales[prov]) form.provinciales[prov] = { porcentajes: {} }
    for (const f of fuerzas.value) {
      if (!(f in form.provinciales[prov].porcentajes)) form.provinciales[prov].porcentajes[f] = 0
    }
  }
}

async function preload() {
  if (!form.email) return
  try {
    const base = import.meta.env.VITE_API_BASE
    const { data } = await axios.get(`${base}/api/predictions/mine`, { params: { email: form.email, soft: 1 } })
    if (data?.exists && data?.prediction) {
      Object.assign(form, data.prediction)
      savedAt.value = new Date(data.prediction.updated_at).toLocaleTimeString()
      syncPending.value = !!data.prediction.sync_pending
    } else {
      idNotice.value = 'No encontramos un pronóstico previo para este email, vamos a crear uno nuevo.'
    }
    identified.value = true
    step.value = 2
    // asegurar estructura provinciales completa
    for (const prov of provincias.value) {
      if (!form.provinciales[prov]) form.provinciales[prov] = { porcentajes: {} }
      for (const f of fuerzas.value) {
        if (!(f in form.provinciales[prov].porcentajes)) form.provinciales[prov].porcentajes[f] = 0
      }
    }
  } catch (err: any) {
    // rethrow unknown errors
    if (!(err?.response)) {
      const msg = err?.response?.data?.detail || err?.message || 'Error al precargar tus datos. Probá nuevamente.'
      error.value = msg
      return
    }
    identified.value = true
    step.value = 2
  }
}

async function save() {
  error.value = ''
  loading.value = true
  try {
    const base = import.meta.env.VITE_API_BASE
    const { data } = await axios.post(`${base}/api/predictions`, form)
    savedAt.value = new Date(data.updated_at).toLocaleTimeString()
    syncPending.value = !!data.sync_pending
    try { localStorage.setItem('prode_email', form.email); localStorage.setItem('prode_name', form.username) } catch {}
  } catch (e: any) {
    const d = e?.response?.data
    if (typeof d === 'string') error.value = d
    else if (d && typeof d === 'object') error.value = JSON.stringify(d)
    else error.value = 'Error al guardar'
  } finally {
    loading.value = false
  }
}

const canContinueId = computed(() => !!form.username && !!form.email && /.+@.+\..+/.test(form.email))

async function confirmIdentification() {
  if (!canContinueId.value) return
  idLoading.value = true
  try {
    await preload()
    // Persist email y nombre localmente para futuras sesiones
    try { localStorage.setItem('prode_email', form.email); localStorage.setItem('prode_name', form.username) } catch {}
    showIdDialog.value = false
  } finally {
    idLoading.value = false
  }
}

onMounted(() => {
  loadMetadata()
  // Abrir diálogo de identificación si no hay email cargado
  try {
    const savedEmail = localStorage.getItem('prode_email') || ''
    const savedName = localStorage.getItem('prode_name') || ''
    if (savedEmail) form.email = savedEmail
    if (savedName) form.username = savedName
  } catch {}
  if (!form.email) showIdDialog.value = true
})

// Persiste cambios de nombre/email en localStorage para mejorar la resiliencia
watch(() => form.email, (v) => { try { if (v) localStorage.setItem('prode_email', v) } catch {} })
watch(() => form.username, (v) => { try { if (v) localStorage.setItem('prode_name', v) } catch {} })

function goToSummary() {
  step.value = 4
}

function provTotal(prov: string) {
  const p = form.provinciales[prov]?.porcentajes || {}
  return Object.values(p).reduce((a: number, b: any) => a + (Number(b) || 0), 0)
}

function normalizeEmail() {
  if (form.email) form.email = String(form.email).trim().toLowerCase()
}

const provincesWinners = computed(() => {
  const rows: Array<{ province: string, winner: string | undefined }> = []
  for (const prov of provincias.value) {
    const winner = form.provinciales[prov]?.winner
    if (winner) rows.push({ province: prov, winner })
  }
  return rows
})

const provsCompleted = computed(() => {
  let n = 0
  for (const prov of provincias.value) {
    const total = provTotal(prov)
    const winner = form.provinciales[prov]?.winner
    if (total > 0 || !!winner) n++
  }
  return n
})
</script>
