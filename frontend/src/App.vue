<template>
  <v-app>
    <v-app-bar density="comfortable" class="appbar-gradient">
      <v-app-bar-title class="d-flex align-center">
        <img :src="urnaSrc" @error="onUrnaError" alt="Urna" class="brand-logo" loading="eager" decoding="async" />
        Prode 2025
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn to="/" variant="text">🏠 Inicio</v-btn>
      <v-btn to="/play" variant="text">🗳️ Jugar</v-btn>
      <v-btn to="/results" variant="text">📊 Resultados</v-btn>
      <v-btn to="/ranking" variant="text">🏆 Ranking</v-btn>
    </v-app-bar>
    <v-main class="bg-pattern">
      <router-view />
    </v-main>
  </v-app>
  <v-footer class="footer py-2">
    <div class="footer-inner">
      <div class="footer-left">
        <strong>Hecho por</strong>
        <a href="https://github.com/f3d3to" target="_blank" rel="noopener" class="link">@f3d3to</a>
        <span class="sep">•</span>
        <a href="https://github.com/f3d3to/prode-elecciones" target="_blank" rel="noopener" class="link">Repositorio</a>
        <span class="sep">•</span>
        <a href="https://www.linkedin.com/in/f3d3to" target="_blank" rel="noopener" class="link">LinkedIn</a>
        <span class="sep">•</span>
        <a href="mailto:reemplazar@email.com" class="link">Contacto</a>
      </div>
      <div class="footer-right">
        <span>MVP 2025</span>
      </div>
    </div>
  </v-footer>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const urnaSrc = ref('/urna_voto.png')
function onUrnaError() {
  // Si la PNG es muy grande o no existe, utilizamos el SVG del favicon como fallback
  if (urnaSrc.value !== '/favicon.svg') {
    urnaSrc.value = '/favicon.svg'
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
  min-height: calc(100vh - 64px);
}
.brand-logo {
  height: 22px;
  width: auto;
  margin-right: 8px;
  vertical-align: middle;
  object-fit: contain;
  border-radius: 3px;
}

.footer {
  background-color: #F9C000 !important; /* amarillo */
  color: #fff !important;
}
.footer-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 4px 12px;
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
