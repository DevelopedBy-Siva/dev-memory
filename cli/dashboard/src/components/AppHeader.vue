<!-- src/components/AppHeader.vue -->
<template>
  <header
    class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-50"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div
            class="bg-gradient-to-r from-blue-500 to-purple-500 p-2 rounded-lg"
          >
            <svg
              class="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white">DevMemory</h1>
            <p class="text-sm text-slate-400">Session-Based Context Tracking</p>
          </div>
        </div>

        <div class="flex items-center space-x-4">
          <div v-if="isActive" class="flex items-center text-sm text-slate-300">
            <span
              class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"
            ></span>
            <span class="text-xs">Session Active</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from "vue";

const apiUrl = window.DEVMEMORY_CONFIG?.API_URL || "http://127.0.0.1:8000";
const isActive = ref(false);

onMounted(async () => {
  try {
    const res = await fetch(`${apiUrl}/api/status`);
    if (!res.ok) return;
    const data = await res.json();
    isActive.value = data.currentSession?.status === "active";
  } catch (err) {
    console.error("Error checking status:", err);
  }
});
</script>
