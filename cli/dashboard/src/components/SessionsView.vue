<!-- src/components/SessionsView.vue -->
<template>
  <section>
    <!-- Loading / error states -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="flex items-center space-x-3 text-slate-300">
        <span class="w-3 h-3 rounded-full bg-blue-500 animate-ping"></span>
        <span class="text-sm">Loading sessions…</span>
      </div>
    </div>

    <div v-else-if="error" class="py-8">
      <div
        class="rounded-xl border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-100"
      >
        {{ error }}
      </div>
    </div>

    <div v-else>
      <!-- Empty state -->
      <div
        v-if="sessions.length === 0"
        class="py-12 text-center text-slate-400"
      >
        <p class="text-sm">
          No sessions yet. Start DevMemory in a project and come back here.
        </p>
      </div>

      <!-- Sessions list -->
      <div v-else class="space-y-4">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-lg font-semibold text-slate-100">Sessions</h2>
          <p class="text-xs text-slate-500">
            Showing {{ sessions.length }} session{{
              sessions.length === 1 ? "" : "s"
            }}
          </p>
        </div>

        <div class="space-y-3">
          <article
            v-for="session in sessions"
            :key="session.session_id"
            class="rounded-xl border border-slate-700/60 bg-slate-900/60 shadow-sm hover:border-slate-500/70 transition-colors"
          >
            <!-- Session header row -->
            <button
              class="w-full flex items-center justify-between px-4 py-3 text-left"
              @click="toggleSession(session.session_id)"
            >
              <div class="flex items-center space-x-3">
                <span
                  class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-medium"
                  :class="
                    session.status === 'active'
                      ? 'bg-green-500/20 text-green-300'
                      : 'bg-slate-700/60 text-slate-300'
                  "
                >
                  {{ session.status === "active" ? "LIVE" : "DONE" }}
                </span>
                <div>
                  <p
                    class="text-sm font-medium text-slate-100 truncate max-w-md"
                  >
                    {{ session.context || "No context provided" }}
                  </p>
                  <p class="text-xs text-slate-500 mt-1">
                    Started: {{ formatDateTime(session.started_at) }}
                    <span v-if="session.stopped_at">
                      • Ended: {{ formatDateTime(session.stopped_at) }}
                    </span>
                  </p>
                </div>
              </div>

              <div class="flex items-center space-x-4 text-xs text-slate-400">
                <span class="flex items-center space-x-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                  <span>{{ session.notes?.length || 0 }} notes</span>
                </span>
                <span
                  v-if="session.patch_count != null"
                  class="flex items-center space-x-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                  <span>{{ session.patch_count }} snapshots</span>
                </span>
                <svg
                  class="w-4 h-4 text-slate-400 transform transition-transform"
                  :class="expandedId === session.session_id ? 'rotate-90' : ''"
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

            <!-- Expanded details -->
            <div
              v-if="expandedId === session.session_id"
              class="border-t border-slate-700/70 bg-slate-950/60 px-4 py-4 text-sm text-slate-200"
            >
              <!-- If we have full detail loaded for this session_id, use it -->
              <div
                v-if="
                  selectedSession &&
                  selectedSession.session_id === session.session_id
                "
              >
                <!-- Notes -->
                <div class="mb-4">
                  <h3
                    class="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2"
                  >
                    Notes
                  </h3>
                  <div
                    v-if="selectedSession.notes && selectedSession.notes.length"
                    class="space-y-2"
                  >
                    <div
                      v-for="(note, idx) in selectedSession.notes"
                      :key="idx"
                      class="flex items-start space-x-2"
                    >
                      <div class="mt-1">
                        <span
                          class="w-1.5 h-1.5 rounded-full bg-blue-400 block"
                        ></span>
                      </div>
                      <div>
                        <p class="text-xs text-slate-500 mb-0.5">
                          {{ note.time || formatTime(note.timestamp) }}
                        </p>
                        <p class="text-sm text-slate-100">
                          {{ note.text }}
                        </p>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-xs text-slate-500">
                    No notes in this session.
                  </p>
                </div>

                <!-- Patches summary -->
                <div class="mb-4">
                  <h3
                    class="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2"
                  >
                    Snapshots in this session
                  </h3>
                  <div
                    v-if="
                      selectedSession.patches && selectedSession.patches.length
                    "
                    class="space-y-1.5"
                  >
                    <p class="text-xs text-slate-500 mb-1">
                      {{ selectedSession.patches.length }} snapshots captured
                    </p>
                    <ul
                      class="text-xs text-slate-400 space-y-0.5 max-h-32 overflow-auto pr-1"
                    >
                      <li
                        v-for="p in selectedSession.patches.slice(0, 10)"
                        :key="p.file"
                        class="flex items-center justify-between"
                      >
                        <span class="truncate max-w-xs">
                          {{ p.time }} • {{ p.commit.slice(0, 8) }}
                        </span>
                        <span class="truncate max-w-xs text-slate-500">
                          {{ p.file }}
                        </span>
                      </li>
                    </ul>
                    <p
                      v-if="selectedSession.patches.length > 10"
                      class="text-[11px] text-slate-500 mt-1"
                    >
                      (+{{ selectedSession.patches.length - 10 }} more…)
                    </p>
                  </div>
                  <p v-else class="text-xs text-slate-500">
                    No patches found for this session window.
                  </p>
                </div>

                <!-- AI summary -->
                <div>
                  <div class="flex items-center justify-between mb-2">
                    <h3
                      class="text-xs font-semibold uppercase tracking-wide text-slate-400"
                    >
                      AI Summary
                    </h3>
                    <button
                      class="inline-flex items-center px-2 py-1 rounded-md text-[11px] border border-sky-500/60 text-sky-200 hover:bg-sky-500/10 disabled:opacity-50"
                      :disabled="summaryLoading"
                      @click.stop="loadSummary(selectedSession.session_id)"
                    >
                      <span v-if="summaryLoading">Summarizing…</span>
                      <span v-else>Get Summary</span>
                    </button>
                  </div>

                  <div v-if="summaryError" class="text-xs text-red-300 mb-2">
                    {{ summaryError }}
                  </div>

                  <div
                    v-if="
                      summary && summaryForId === selectedSession.session_id
                    "
                    class="text-xs leading-relaxed text-slate-200 whitespace-pre-wrap bg-slate-900/80 border border-slate-700/70 rounded-lg px-3 py-2"
                  >
                    {{ summary.summary || summary }}
                  </div>

                  <p v-else class="text-xs text-slate-500">
                    Click "Get Summary" to generate an AI summary for this
                    session.
                  </p>
                </div>
              </div>

              <!-- Loading state for selected session -->
              <div v-else class="text-xs text-slate-400">
                Loading session details…
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from "vue";

const apiUrl = window.DEVMEMORY_CONFIG?.API_URL || "http://127.0.0.1:8000";

const loading = ref(true);
const error = ref(null);

const sessions = ref([]); // list from /api/sessions
const expandedId = ref(null); // which card is expanded
const selectedSession = ref(null); // detail from /api/session/{id}

const summary = ref(null); // AI summary payload
const summaryForId = ref(null); // which session the summary belongs to
const summaryLoading = ref(false);
const summaryError = ref(null);

function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString();
}

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString();
}

async function fetchSessions() {
  loading.value = true;
  error.value = null;

  try {
    const res = await fetch(`${apiUrl}/api/sessions`);
    if (!res.ok) {
      throw new Error(`Failed to load sessions (${res.status})`);
    }
    const data = await res.json();
    sessions.value = data.sessions || [];
  } catch (err) {
    console.error("Error loading sessions:", err);
    error.value = err.message || "Failed to load sessions.";
  } finally {
    loading.value = false;
  }
}

async function loadSessionDetail(sessionId) {
  selectedSession.value = null;
  summary.value = null;
  summaryForId.value = null;
  summaryError.value = null;

  try {
    const res = await fetch(
      `${apiUrl}/api/session/${encodeURIComponent(sessionId)}`
    );
    if (!res.ok) {
      throw new Error(`Failed to load session ${sessionId} (${res.status})`);
    }
    const data = await res.json();
    selectedSession.value = data;
  } catch (err) {
    console.error("Error loading session detail:", err);
    summaryError.value = "Could not load this session.";
  }
}

function toggleSession(sessionId) {
  if (expandedId.value === sessionId) {
    expandedId.value = null;
    return;
  }

  expandedId.value = sessionId;
  loadSessionDetail(sessionId);
}

async function loadSummary(sessionId) {
  summaryLoading.value = true;
  summaryError.value = null;
  summary.value = null;
  summaryForId.value = null;

  try {
    const res = await fetch(
      `${apiUrl}/api/session/${encodeURIComponent(sessionId)}/summary`
    );
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Summary failed (${res.status}): ${txt}`);
    }
    const data = await res.json();
    summary.value = data;
    summaryForId.value = sessionId;
  } catch (err) {
    console.error("Error loading summary:", err);
    summaryError.value = err.message || "Failed to generate summary.";
  } finally {
    summaryLoading.value = false;
  }
}

onMounted(() => {
  fetchSessions();
});
</script>
