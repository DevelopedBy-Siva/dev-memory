<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Coding Sessions</h2>
        <p class="text-sm text-slate-500 mt-1">
          Sessions are automatically grouped when you take breaks longer than 30
          minutes
        </p>
      </div>
      <div
        class="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg"
      >
        <span class="text-sm text-slate-400">Total Sessions:</span>
        <span class="ml-2 text-lg font-bold text-blue-300">{{
          store.sessions.length
        }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="store.loading && !store.sessions.length"
      class="card p-12 text-center"
    >
      <svg
        class="w-12 h-12 text-slate-400 animate-spin mx-auto mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
      <p class="text-slate-400">Loading sessions...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!store.sessions.length" class="card p-12 text-center">
      <div
        class="inline-flex items-center justify-center w-16 h-16 bg-slate-700/30 rounded-full mb-4"
      >
        <svg
          class="w-8 h-8 text-slate-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <p class="text-lg text-slate-400 mb-2">No coding sessions yet</p>
      <p class="text-sm text-slate-600">
        Start coding and DevMemory will track your sessions
      </p>
    </div>

    <!-- Sessions List -->
    <div v-else class="space-y-4">
      <div
        v-for="(session, idx) in store.sessions"
        :key="idx"
        class="card p-6 hover:border-blue-500/30 transition-all cursor-pointer group"
      >
        <div class="flex items-start justify-between mb-4">
          <!-- Session Info -->
          <div class="flex-1">
            <div class="flex items-center space-x-3 mb-2">
              <div
                class="p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors"
              >
                <svg
                  class="w-5 h-5 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">
                  Session {{ store.sessions.length - idx }}
                </h3>
                <p class="text-sm text-slate-400">
                  {{ formatSessionTime(session) }}
                </p>
              </div>
            </div>

            <div class="flex items-center space-x-4 text-sm">
              <div class="flex items-center space-x-2">
                <svg
                  class="w-4 h-4 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span class="text-slate-400">{{
                  calculateDuration(session)
                }}</span>
              </div>
              <div class="flex items-center space-x-2">
                <svg
                  class="w-4 h-4 text-slate-500"
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
                <span class="text-slate-400"
                  >{{ session.patches }} snapshots</span
                >
              </div>
            </div>
          </div>

          <!-- Session Stats -->
          <div class="text-right">
            <div
              class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg border border-blue-500/20"
            >
              <span class="text-2xl font-bold text-white">{{
                session.patches
              }}</span>
            </div>
          </div>
        </div>

        <!-- Commits Preview -->
        <div
          class="flex items-center space-x-2 mt-4 pt-4 border-t border-slate-700/50"
        >
          <span class="text-xs text-slate-500">Recent commits:</span>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="commit in session.commits"
              :key="commit"
              class="px-2 py-1 bg-slate-900/50 text-slate-400 rounded text-xs font-mono hover:bg-slate-700/50 transition-colors"
            >
              {{ commit }}
            </span>
            <span
              v-if="session.patches > 3"
              class="px-2 py-1 text-xs text-slate-500"
            >
              +{{ session.patches - 3 }} more
            </span>
          </div>
        </div>

        <!-- Timeline Indicator -->
        <div class="mt-4 pt-4 border-t border-slate-700/50">
          <div class="flex items-center space-x-2">
            <div
              class="flex-1 h-2 bg-slate-700/30 rounded-full overflow-hidden"
            >
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                :style="{ width: calculateIntensity(session) + '%' }"
              ></div>
            </div>
            <span class="text-xs text-slate-500 whitespace-nowrap">
              {{ calculateIntensity(session) }}% active
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useDevMemoryStore } from "@/stores/devmemory";

const store = useDevMemoryStore();

const formatSessionTime = (session) => {
  const start = new Date(session.start);
  const end = new Date(session.end);

  const formatTime = (date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  // If same day, show date once
  if (start.toDateString() === end.toDateString()) {
    return `${formatDate(start)} • ${formatTime(start)} → ${formatTime(end)}`;
  }

  return `${formatDate(start)} ${formatTime(start)} → ${formatDate(
    end
  )} ${formatTime(end)}`;
};

const calculateDuration = (session) => {
  const start = new Date(session.start);
  const end = new Date(session.end);
  const diffMs = end - start;

  const minutes = Math.floor(diffMs / 60000);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    const remainingMins = minutes % 60;
    return `${hours}h ${remainingMins}m`;
  }

  return `${minutes}m`;
};

const calculateIntensity = (session) => {
  // Calculate "intensity" based on patches per minute
  const start = new Date(session.start);
  const end = new Date(session.end);
  const durationMinutes = (end - start) / 60000;

  if (durationMinutes === 0) return 100;

  const patchesPerMinute = session.patches / durationMinutes;

  // Scale to percentage (max 1 patch/minute = 100%)
  return Math.min(Math.round(patchesPerMinute * 100), 100);
};
</script>
