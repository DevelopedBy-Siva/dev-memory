<template>
  <div
    style="background-color: #212121"
    id="app"
    class="min-h-screen from-slate-900 via-slate-800 to-slate-900"
  >
    <AppHeader />

    <main
      style="background-color: #212121"
      class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppHeader from "@/components/AppHeader.vue";
</script>

<style>
@import "./assets/main.css";
</style>
