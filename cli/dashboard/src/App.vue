<template>
  <div id="app" class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <AppHeader />
    
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'

// Don't import store here - let components handle their own data loading
onMounted(() => {
  // Components will load their own data
})
</script>

<style>
@import './assets/main.css';
</style>
