<template>
  <div class="space-y-6">
    <!-- Main Context Card -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-white flex items-center">
          <svg class="w-7 h-7 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          What Was I Working On?
        </h2>
        
        <button 
          @click="loadContext"
          :disabled="store.loading"
          class="btn-primary flex items-center space-x-2"
        >
          <svg v-if="!store.loading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ store.loading ? 'Loading...' : 'Restore Context' }}</span>
        </button>
      </div>

      <!-- Context Content -->
      <div v-if="store.context" class="space-y-4">
        <div class="bg-slate-900/50 rounded-lg p-6 border border-slate-700/30">
          <div v-html="formatMarkdown(store.context.context)" class="prose prose-invert max-w-none text-slate-300 leading-relaxed space-y-4"></div>
        </div>

        <!-- Metadata -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-700/50">
          <div class="flex items-center space-x-3">
            <div class="p-2 bg-blue-500/10 rounded-lg">
              <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p class="text-xs text-slate-500">Activity Period</p>
              <p class="text-sm text-slate-300 font-medium">{{ store.context.activePeriod }}</p>
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <div class="p-2 bg-purple-500/10 rounded-lg">
              <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p class="text-xs text-slate-500">Snapshots Analyzed</p>
              <p class="text-sm text-slate-300 font-medium">{{ store.context.recentPatches }}</p>
            </div>
          </div>
        </div>

        <!-- Files in Focus -->
        <div v-if="store.context.filesInFocus && store.context.filesInFocus.length > 0" class="pt-4 border-t border-slate-700/50">
          <p class="text-sm text-slate-500 mb-3">Files in Focus:</p>
          <div class="flex flex-wrap gap-2">
            <span 
              v-for="file in store.context.filesInFocus" 
              :key="file"
              class="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 rounded-lg text-sm font-mono hover:bg-blue-500/20 transition-colors"
            >
              {{ file }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-16">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-purple-500/10 rounded-full mb-4">
          <svg class="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-slate-300 mb-2">Ready to Restore Context</h3>
        <p class="text-slate-500 mb-6">Click "Restore Context" to see what you were working on</p>
        <p class="text-sm text-slate-600">AI will analyze your recent snapshots and provide a clear summary</p>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 mb-1">Total Snapshots</p>
            <p class="text-3xl font-bold text-white">{{ store.totalPatches }}</p>
          </div>
          <div class="p-3 bg-blue-500/10 rounded-lg">
            <svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 mb-1">Coding Sessions</p>
            <p class="text-3xl font-bold text-white">{{ store.sessions.length }}</p>
          </div>
          <div class="p-3 bg-purple-500/10 rounded-lg">
            <svg class="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 mb-1">Latest Activity</p>
            <p class="text-xl font-bold text-white">
              {{ formatLatestActivity() }}
            </p>
          </div>
          <div class="p-3 bg-green-500/10 rounded-lg">
            <svg class="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDevMemoryStore } from '@/stores/devmemory'

const store = useDevMemoryStore()

// Load initial data when component mounts
onMounted(async () => {
  await store.refreshAll()
})

const loadContext = async () => {
  await store.restoreContext()
}

const formatMarkdown = (text) => {
  if (!text) return ''
  
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold text-white mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-white mt-6 mb-3">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mt-8 mb-4">$1</h1>')
    .replace(/^- (.+)$/gm, '<li class="ml-4">• $1</li>')
    .replace(/\n\n/g, '</p><p class="mt-3">')
    .replace(/^(.+)$/gm, '<p>$1</p>')
}

const formatLatestActivity = () => {
  if (!store.status.latestActivity) return 'No activity'
  
  const date = new Date(store.status.latestActivity)
  const now = new Date()
  const diff = now - date
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}
</script>
