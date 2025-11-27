<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Left Panel: Patches List -->
    <div class="lg:col-span-1 space-y-4">
      <!-- Search Bar -->
      <div class="card p-4">
        <div class="relative">
          <svg
            class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            v-model="searchQuery"
            @input="handleSearch"
            type="text"
            placeholder="Search commits or dates..."
            class="input-field pl-10"
          />
        </div>
      </div>

      <!-- Patches List -->
      <div class="card overflow-hidden">
        <div class="p-4 border-b border-slate-700/50">
          <h2 class="text-lg font-semibold text-white flex items-center">
            <svg
              class="w-5 h-5 mr-2 text-blue-400"
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
            Recent Snapshots
          </h2>
          <p class="text-sm text-slate-500 mt-1">
            {{ filteredPatches.length }} snapshots
          </p>
        </div>

        <div class="max-h-[600px] overflow-y-auto">
          <div
            v-if="store.loading && !store.patches.length"
            class="p-8 text-center"
          >
            <svg
              class="w-8 h-8 text-slate-400 animate-spin mx-auto mb-2"
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
            <p class="text-slate-400">Loading patches...</p>
          </div>

          <div v-else-if="!filteredPatches.length" class="p-8 text-center">
            <svg
              class="w-12 h-12 text-slate-600 mx-auto mb-3"
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
            <p class="text-slate-400">No patches found</p>
          </div>

          <div v-else class="divide-y divide-slate-700/50">
            <div v-for="(group, date) in groupedPatches" :key="date">
              <div
                class="px-4 py-2 bg-slate-900/30 sticky top-0 backdrop-blur-sm"
              >
                <div class="flex items-center text-sm text-slate-400">
                  <svg
                    class="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  {{ formatDate(date) }}
                </div>
              </div>

              <button
                v-for="patch in group"
                :key="patch.commit"
                @click="selectPatch(patch)"
                :class="[
                  'w-full text-left px-4 py-3 hover:bg-slate-700/30 transition-colors',
                  store.selectedPatch?.commit === patch.commit
                    ? 'bg-blue-500/10 border-l-2 border-blue-500'
                    : '',
                ]"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-mono text-slate-300 truncate">
                      {{ patch.commit.substring(0, 8) }}
                    </p>
                    <p class="text-xs text-slate-500 mt-1">
                      {{ patch.time }}
                    </p>
                  </div>
                  <svg
                    class="w-4 h-4 text-slate-500 flex-shrink-0 ml-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel: Patch Details -->
    <div class="lg:col-span-2">
      <div v-if="store.selectedPatch" class="card overflow-hidden">
        <!-- Header -->
        <div class="p-6 border-b border-slate-700/50 bg-slate-900/30">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h2 class="text-xl font-bold text-white flex items-center mb-2">
                <svg
                  class="w-6 h-6 mr-2 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                  />
                </svg>
                Commit Details
              </h2>
              <p class="text-sm text-slate-400 font-mono break-all">
                {{ store.selectedPatch.commit }}
              </p>
              <p class="text-xs text-slate-500 mt-2">
                {{ formatFullDate(store.selectedPatch.datetime) }}
              </p>
            </div>
          </div>

          <!-- Stats -->
          <div v-if="store.patchDetails?.stats" class="flex flex-wrap gap-4">
            <div
              class="flex items-center space-x-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg"
            >
              <span class="text-green-400 font-semibold"
                >+{{ store.patchDetails.stats.additions }}</span
              >
              <span class="text-xs text-slate-500">additions</span>
            </div>
            <div
              class="flex items-center space-x-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg"
            >
              <span class="text-red-400 font-semibold"
                >-{{ store.patchDetails.stats.deletions }}</span
              >
              <span class="text-xs text-slate-500">deletions</span>
            </div>
            <div
              class="flex items-center space-x-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg"
            >
              <svg
                class="w-4 h-4 text-blue-400"
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
              <span class="text-blue-300 font-semibold">{{
                store.patchDetails.stats.files_changed.length
              }}</span>
              <span class="text-xs text-slate-500">files</span>
            </div>
          </div>

          <!-- Files Changed -->
          <div
            v-if="store.patchDetails?.stats?.files_changed?.length"
            class="mt-4"
          >
            <p class="text-xs text-slate-500 mb-2">Files Changed:</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="file in store.patchDetails.stats.files_changed"
                :key="file"
                class="px-2 py-1 bg-slate-700/50 text-slate-300 rounded text-xs font-mono"
              >
                {{ file }}
              </span>
            </div>
          </div>
        </div>

        <!-- Patch Content -->
        <div class="p-6 overflow-auto max-h-[600px]">
          <pre
            class="text-xs text-slate-300 font-mono bg-slate-900/50 p-4 rounded-lg overflow-x-auto border border-slate-700/30 whitespace-pre-wrap"
            >{{ store.patchDetails?.patch || "Loading..." }}</pre
          >
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="card h-full flex items-center justify-center p-12">
        <div class="text-center">
          <div
            class="inline-flex items-center justify-center w-20 h-20 bg-slate-700/30 rounded-full mb-4"
          >
            <svg
              class="w-10 h-10 text-slate-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </div>
          <p class="text-lg text-slate-400 mb-2">
            Select a patch to view details
          </p>
          <p class="text-sm text-slate-600">
            Click on any snapshot from the list
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useDevMemoryStore } from "@/stores/devmemory";

const store = useDevMemoryStore();
const searchQuery = ref("");

const filteredPatches = computed(() => {
  if (!searchQuery.value) return store.patches;

  const query = searchQuery.value.toLowerCase();
  return store.patches.filter(
    (p) =>
      p.commit.toLowerCase().includes(query) ||
      p.date.includes(query) ||
      p.timestamp.includes(query)
  );
});

const groupedPatches = computed(() => {
  const grouped = {};
  filteredPatches.value.forEach((patch) => {
    if (!grouped[patch.date]) grouped[patch.date] = [];
    grouped[patch.date].push(patch);
  });
  return grouped;
});

const selectPatch = (patch) => {
  store.selectPatch(patch);
};

const handleSearch = () => {
  // Search is reactive through computed property
};

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const formatFullDate = (isoStr) => {
  const date = new Date(isoStr);
  return date.toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};
</script>
