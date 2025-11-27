<template>
  <header class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo & Title -->
        <div class="flex items-center space-x-3">
          <div class="bg-gradient-to-r from-blue-500 to-purple-500 p-2 rounded-lg">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white">DevMemory</h1>
            <p class="text-sm text-slate-400">AI-Powered Context Restoration</p>
          </div>
        </div>

        <!-- Status & Actions -->
        <div class="flex items-center space-x-4">
          <div v-if="store.isRunning" class="hidden sm:flex items-center text-sm text-slate-300">
            <span class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            <span class="font-mono text-xs truncate max-w-xs">{{ store.status.projectRoot }}</span>
          </div>

          <div v-if="store.totalPatches > 0" class="hidden md:flex items-center space-x-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span class="text-sm font-semibold text-blue-300">{{ store.totalPatches }}</span>
          </div>

          <button @click="handleRefresh" :disabled="store.loading" class="p-2 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50" title="Refresh">
            <svg class="w-5 h-5 text-slate-300" :class="{ 'animate-spin': store.loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <nav class="mt-4 flex space-x-2">
        <router-link to="/" custom v-slot="{ isActive, navigate }">
          <button @click="navigate" :class="isActive ? 'bg-blue-500 text-white' : 'bg-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700'" class="px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span>Context</span>
          </button>
        </router-link>

        <router-link to="/patches" custom v-slot="{ isActive, navigate }">
          <button @click="navigate" :class="isActive ? 'bg-blue-500 text-white' : 'bg-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700'" class="px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Patches</span>
          </button>
        </router-link>

        <router-link to="/sessions" custom v-slot="{ isActive, navigate }">
          <button @click="navigate" :class="isActive ? 'bg-blue-500 text-white' : 'bg-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700'" class="px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Sessions</span>
          </button>
        </router-link>
      </nav>

      <!-- Error Banner -->
      <div v-if="store.error" class="mt-3 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-sm text-red-300">{{ store.error }}</span>
        </div>
        <button @click="store.error = null" class="text-red-400 hover:text-red-300">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useDevMemoryStore } from '@/stores/devmemory'

const store = useDevMemoryStore()

const handleRefresh = async () => {
  await store.refreshAll()
}
</script>
