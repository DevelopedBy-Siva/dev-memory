import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useDevMemoryStore = defineStore("devmemory", () => {
  // State
  const apiUrl = ref(
    window.DEVMEMORY_CONFIG?.API_URL || "http://127.0.0.1:8000"
  );
  const status = ref({});
  const patches = ref([]);
  const sessions = ref([]);
  const context = ref(null);
  const selectedPatch = ref(null);
  const patchDetails = ref(null);
  const loading = ref(false);
  const error = ref(null);

  // Computed
  const isRunning = computed(() => status.value.running === true);
  const totalPatches = computed(() => patches.value.length);

  // Actions
  async function fetchStatus() {
    try {
      const res = await fetch(`${apiUrl.value}/api/status`);
      if (!res.ok) throw new Error("Failed to fetch status");
      status.value = await res.json();
    } catch (err) {
      error.value = err.message;
      status.value = { running: false };
    }
  }

  async function fetchPatches(limit = null, date = null) {
    loading.value = true;
    error.value = null;
    try {
      let url = `${apiUrl.value}/api/patches`;
      const params = new URLSearchParams();
      if (limit) params.append("limit", limit);
      if (date) params.append("date", date);
      if (params.toString()) url += `?${params}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch patches");
      const data = await res.json();
      patches.value = data.patches;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function fetchPatchDetails(commitPrefix) {
    loading.value = true;
    try {
      const res = await fetch(`${apiUrl.value}/api/patch/${commitPrefix}`);
      if (!res.ok) throw new Error("Patch not found");
      patchDetails.value = await res.json();
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function fetchSessions() {
    loading.value = true;
    try {
      const res = await fetch(`${apiUrl.value}/api/sessions`);
      if (!res.ok) throw new Error("Failed to fetch sessions");
      const data = await res.json();
      sessions.value = data.sessions;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function restoreContext() {
    loading.value = true;
    try {
      const res = await fetch(`${apiUrl.value}/api/context/restore`);
      if (!res.ok) throw new Error("Failed to restore context");
      context.value = await res.json();
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  }

  async function summarizePatches(date = null, commitIds = null) {
    loading.value = true;
    try {
      const body = {};
      if (date) body.date = date;
      if (commitIds) body.commit_ids = commitIds;

      const res = await fetch(`${apiUrl.value}/api/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error("Failed to summarize");
      return await res.json();
    } catch (err) {
      error.value = err.message;
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function searchPatches(query) {
    loading.value = true;
    try {
      const res = await fetch(
        `${apiUrl.value}/api/search?query=${encodeURIComponent(query)}`
      );
      if (!res.ok) throw new Error("Search failed");
      return await res.json();
    } catch (err) {
      error.value = err.message;
      return null;
    } finally {
      loading.value = false;
    }
  }

  function selectPatch(patch) {
    selectedPatch.value = patch;
    fetchPatchDetails(patch.commit);
  }

  async function refreshAll() {
    await Promise.all([fetchStatus(), fetchPatches(), fetchSessions()]);
  }

  return {
    // State
    apiUrl,
    status,
    patches,
    sessions,
    context,
    selectedPatch,
    patchDetails,
    loading,
    error,
    // Computed
    isRunning,
    totalPatches,
    // Actions
    fetchStatus,
    fetchPatches,
    fetchPatchDetails,
    fetchSessions,
    restoreContext,
    summarizePatches,
    searchPatches,
    selectPatch,
    refreshAll,
  };
});
