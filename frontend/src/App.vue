<template>
  <v-app>
    <v-app-bar density="comfortable">
      <v-app-bar-title>🗳️ Prode 2025</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn to="/" variant="text">Inicio</v-btn>
      <v-btn to="/play" variant="text">Jugar</v-btn>
      <v-btn to="/results" variant="text">Resultados</v-btn>
      <v-btn to="/ranking" variant="text">Ranking</v-btn>
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
</script>

<style>
html, body, #app { height: 100%; }
</style>
