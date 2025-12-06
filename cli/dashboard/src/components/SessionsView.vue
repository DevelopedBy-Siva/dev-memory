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
      <!-- Insights -->
      <section class="mb-8" v-if="sessions.length > 0">
        <div class="flex items-center justify-between mb-3">
          <h2
            style="margin-top: 50px; color: #fff; font-size: 28px"
            class="text-lg font-semibold text-slate-100"
          >
            Memory Insights
          </h2>
          <p style="color: #d8d8d8" class="text-xs text-slate-400">
            Last {{ insights?.window_days || 30 }} days
          </p>
        </div>

        <div v-if="insightsError" class="text-xs text-red-300 mb-2">
          {{ insightsError }}
        </div>

        <div v-if="insights" class="grid md:grid-cols-3 gap-4">
          <!-- Streaks -->
          <div
            style="border-radius: 10px; border-color: grey"
            class="bg-slate-900/70 border border-slate-700/70 rounded-xl p-4"
          >
            <h3
              style="color: grey; font-size: 18px; margin-bottom: 20px"
              class="text-xs font-semibold text-slate-300 mb-2"
            >
              Streaks
            </h3>
            <div
              style="font-size: 48px; color: #d8d8d8"
              class="text-3xl font-bold text-slate-50"
            >
              {{ insights.current_streak
              }}<span style="color: grey" class="text-base text-slate-400 ml-1"
                >d</span
              >
            </div>
            <div style="color: grey" class="text-[11px] text-slate-300 mt-1">
              Current streak
            </div>
            <div style="color: grey" class="text-[11px] text-slate-400 mt-2">
              Longest streak:
              <span class="text-slate-100"
                >{{ insights.longest_streak }} days</span
              >
            </div>
          </div>

          <!-- Hot files -->
          <div
            style="border-radius: 10px; border-color: grey"
            class="bg-slate-900/70 border border-slate-700/70 rounded-xl p-4"
          >
            <h3
              style="color: grey; font-size: 18px; margin-bottom: 20px"
              class="text-xs font-semibold text-slate-300 mb-2"
            >
              Top edited files
            </h3>
            <ul class="space-y-1 max-h-40 overflow-auto">
              <li
                style="color: grey; font-size: 12px"
                v-for="hf in insights.hot_files"
                :key="hf.file"
                class="flex justify-between text-[11px] text-slate-300"
              >
                <span class="truncate font-mono">{{ hf.file }}</span>
                <span style="color: #d8d8d8" class="text-slate-400"
                  >{{ hf.edits }} edits</span
                >
              </li>
              <li
                v-if="insights.hot_files.length === 0"
                class="text-[11px] text-slate-400"
              >
                No file activity yet.
              </li>
            </ul>
          </div>

          <!-- Activity heatmap -->
          <div
            style="border-radius: 10px; border-color: grey"
            class="bg-slate-900/70 border border-slate-700/70 rounded-xl p-4"
          >
            <h3
              style="color: grey; font-size: 18px; margin-bottom: 20px"
              class="text-xs font-semibold text-slate-300 mb-2"
            >
              Activity
            </h3>
            <div class="flex flex-wrap gap-1">
              <div
                v-for="day in insights.activity"
                :key="day.date"
                class="w-3 h-3 rounded-sm"
                :class="{
                  'bg-slate-700': day.count === 0,
                  'bg-sky-900': day.count === 1,
                  'bg-sky-600': day.count === 2,
                  'bg-sky-400': day.count >= 3,
                }"
                :title="`${day.date}: ${day.count} snapshots`"
              ></div>
            </div>
            <div style="color: grey" class="text-[10px] text-slate-400 mt-2">
              One square = 1 day
            </div>
          </div>
        </div>
      </section>

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
      <div style="margin-top: 40px" v-else class="space-y-4">
        <div class="flex items-center justify-between mb-2">
          <h2
            style="font-size: 28px; color: #fff"
            class="text-lg font-semibold text-slate-100"
          >
            Sessions
          </h2>
          <p style="color: #d8d8d8" class="text-xs text-slate-300">
            Showing {{ sessions.length }} session{{
              sessions.length === 1 ? "" : "s"
            }}
          </p>
        </div>

        <div class="space-y-3">
          <article
            style="padding: 30px; border-color: grey; border-radius: 10px"
            v-for="session in sessions"
            :key="session.session_id"
            class="rounded-xl border border-slate-700/60 bg-slate-900/60 shadow-sm hover:border-slate-500/70 transition-colors"
          >
            <!-- Session header row -->
            <button
              class="w-full flex flex-col gap-3 px-4 py-3 text-left"
              @click="toggleSession(session.session_id)"
            >
              <div class="w-full flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <span
                    style="margin-right: 25px"
                    class="inline-flex items-center justify-center w-7 h-7 rounded-full text-[11px] font-semibold"
                    :class="
                      session.status === 'active'
                        ? 'text-green-400'
                        : 'text-slate-400'
                    "
                  >
                    {{ session.status === "active" ? "LIVE" : "DONE" }}
                  </span>

                  <div>
                    <p
                      style="color: #d8d8d8; font-size: 18px"
                      class="text-sm font-medium text-slate-100 truncate max-w-md"
                    >
                      {{ session.context || "No context provided" }}
                    </p>
                    <p style="color: grey" class="text-xs text-slate-400 mt-1">
                      Started: {{ formatDateTime(session.started_at) }}
                      <span v-if="session.stopped_at">
                        • Ended: {{ formatDateTime(session.stopped_at) }}
                      </span>
                    </p>
                  </div>
                </div>

                <div class="flex items-center space-x-4 text-xs text-slate-400">
                  <span style="color: grey" class="flex items-center space-x-1">
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
                    style="color: grey"
                    class="w-4 h-4 text-slate-400 transform transition-transform"
                    :class="
                      expandedId === session.session_id ? 'rotate-90' : ''
                    "
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
              </div>

              <!-- Timeline -->
              <div v-if="session.patch_count" class="mt-1">
                <div class="text-[11px] text-slate-400 mb-1">Timeline</div>
                <div
                  class="relative h-2 bg-slate-800 rounded-full overflow-hidden"
                >
                  <div
                    class="absolute inset-y-0 left-0 right-0 bg-slate-700/60"
                  ></div>
                  <div
                    v-for="pt in getTimelinePoints(session)"
                    :key="pt.file"
                    class="absolute -top-1 w-2 h-2 rounded-full bg-sky-400 shadow"
                    :style="{ left: `calc(${pt.ratio * 100}% - 4px)` }"
                    :title="`${pt.time} • ${pt.commit.slice(0, 8)}`"
                  ></div>
                </div>
              </div>
            </button>

            <!-- Expanded details -->
            <div
              style="border: none"
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
                    style="font-weight: 700; color: #d8d8d8"
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
                        <p
                          style="color: grey"
                          class="text-xs text-slate-400 mb-0.5"
                        >
                          {{ note.time || formatTime(note.timestamp) }}
                        </p>
                        <p class="text-sm text-slate-100">
                          {{ note.text }}
                        </p>
                      </div>
                    </div>
                  </div>
                  <p style="color: grey" v-else class="text-xs text-slate-400">
                    No notes in this session.
                  </p>
                </div>

                <!-- Patches summary -->
                <div class="mb-4">
                  <h3
                    style="font-weight: 700; color: #d8d8d8"
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
                    <p style="color: grey" class="text-xs text-slate-400 mb-1">
                      {{ selectedSession.patches.length }} snapshots captured
                    </p>
                    <ul
                      style="
                        margin-top: 10px;
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                      "
                      class="text-xs text-slate-400 space-y-1 max-h-40 overflow-auto pr-1"
                    >
                      <li
                        v-for="p in selectedSession.patches.slice(0, 10)"
                        :key="p.file"
                        class="flex items-center justify-between gap-2"
                      >
                        <div class="flex flex-col">
                          <span class="text-slate-200" style="color: gray">
                            {{ p.time }} • {{ p.commit.slice(0, 8) }}
                          </span>
                          <span
                            style="color: gray"
                            class="truncate max-w-xs text-slate-400"
                          >
                            {{ p.file }}
                          </span>
                        </div>
                        <button
                          style="
                            border-radius: 5px;
                            background-color: gray;
                            color: #000;
                            cursor: pointer;
                          "
                          class="text-[11px] px-2 py-1 rounded-md text-slate-200 hover:bg-slate-800"
                          @click.stop="openPatch(p.file)"
                        >
                          View diff
                        </button>
                      </li>
                    </ul>
                    <p
                      v-if="selectedSession.patches.length > 10"
                      class="text-[11px] text-slate-400 mt-1"
                    >
                      (+{{ selectedSession.patches.length - 10 }} more…)
                    </p>
                  </div>
                  <p v-else class="text-xs text-slate-400">
                    No patches found for this session window.
                  </p>
                </div>

                <!-- AI summary -->
                <div style="margin-top: 20px">
                  <div class="flex items-center justify-between mb-2">
                    <button
                      style="
                        border-radius: 5px;
                        background: #fff;
                        color: #000;
                        cursor: pointer;
                      "
                      class="inline-flex items-center px-2 py-1 rounded-md text-[11px] text-sky-200 hover:bg-sky-500/10 disabled:opacity-50"
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
                    style="
                      margin-top: 30px;
                      border: none;
                      padding: 30px;
                      background: #c2c2c2;
                    "
                    v-if="
                      summary && summaryForId === selectedSession.session_id
                    "
                    class="text-xs leading-relaxed text-slate-200 whitespace-pre-wrap bg-slate-900/80 border border-slate-700/70 rounded-lg px-3 py-2"
                  >
                    {{ summary.summary || summary }}
                  </div>
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

    <!-- Patch diff modal -->
    <div
      style="border: none"
      v-if="showPatchModal"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
    >
      <div
        style="padding: 10px; border: none"
        class="bg-slate-900 border border-slate-700 rounded-xl shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col"
      >
        <div class="flex items-center justify-between px-4 py-3">
          <div style="color: gray" class="text-sm font-semibold text-slate-200">
            Snapshot Diff
          </div>
          <button
            style="
              background: #fff;
              padding: 3px 8px;
              border-radius: 8px;
              color: red;
              margin: 0 25px;
              cursor: pointer;
            "
            class="text-slate-400 hover:text-slate-100 p-1"
            @click="showPatchModal = false"
            title="Close"
          >
            close
          </button>
        </div>
        <div class="flex-1 overflow-auto bg-slate-950">
          <div v-if="patchLoading" class="p-4 text-sm text-slate-300">
            Loading diff...
          </div>
          <div v-else-if="patchError" class="p-4 text-sm text-red-400">
            {{ patchError }}
          </div>
          <pre
            style="
              color: #d8d8d8;
              background-color: #171717;
              border-radius: 15px;
              padding: 30px;
            "
            v-else
            class="p-4 text-xs font-mono text-slate-100 whitespace-pre-wrap"
            >{{ selectedPatchText }}</pre
          >
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

const sessions = ref([]);
const expandedId = ref(null);
const selectedSession = ref(null);

const summary = ref(null);
const summaryForId = ref(null);
const summaryLoading = ref(false);
const summaryError = ref(null);

const selectedPatchFile = ref(null);
const selectedPatchText = ref("");
const patchLoading = ref(false);
const patchError = ref(null);
const showPatchModal = ref(false);

const insights = ref(null);
const insightsError = ref(null);

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

async function loadSessions() {
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

async function openPatch(patchFile) {
  patchLoading.value = true;
  patchError.value = null;
  selectedPatchFile.value = patchFile;
  selectedPatchText.value = "";
  showPatchModal.value = true;

  try {
    const res = await fetch(
      `${apiUrl}/api/patch/${encodeURIComponent(patchFile)}`
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to load patch (${res.status}): ${text}`);
    }
    const text = await res.text();
    selectedPatchText.value = text;
  } catch (err) {
    console.error("Error loading patch:", err);
    patchError.value = err.message || "Failed to load patch";
  } finally {
    patchLoading.value = false;
  }
}

function getTimelinePoints(session) {
  if (!session.patches || session.patches.length === 0) return [];

  const start = new Date(session.started_at).getTime();
  const end = new Date(session.stopped_at || Date.now()).getTime();
  if (end <= start) return [];

  return session.patches.map((p) => {
    const t = new Date(p.datetime).getTime();
    const ratio = Math.min(1, Math.max(0, (t - start) / (end - start)));
    return { ...p, ratio };
  });
}

async function loadInsights() {
  insightsError.value = null;
  try {
    const res = await fetch(`${apiUrl}/api/insights?days=30`);
    if (!res.ok) {
      throw new Error(`Failed to load insights (${res.status})`);
    }
    insights.value = await res.json();
  } catch (err) {
    console.error("Error loading insights:", err);
    insightsError.value = err.message || "Failed to load insights";
  }
}

onMounted(() => {
  loadSessions();
  loadInsights();
});
</script>
