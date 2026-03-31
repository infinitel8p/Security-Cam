<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { sseClient } from "../lib/sse";
  import { initLocale, t } from "../i18n";

  let online = $state(false);
  let checked = $state(false);
  let unsubState: (() => void) | null = null;

  async function check() {
    try {
      const res = await fetch(`${getBackendUrl()}/recording_status`, {
        signal: AbortSignal.timeout(5000),
      });
      online = res.ok;
    } catch {
      online = false;
    }
    checked = true;
  }

  onMount(() => {
    initLocale();
    check();

    const sse = sseClient();
    // SSE connection itself proves the backend is online
    unsubState = sse.onStateChange((state) => {
      online = state.connected;
      checked = true;
    });
  });

  onDestroy(() => {
    unsubState?.();
  });
</script>

{#if checked}
  <div
    class="flex items-center gap-2 rounded-full border px-3 py-1.5 transition-colors duration-300
      {online
        ? 'border-status-ok/15 bg-status-ok/6'
        : 'border-status-critical/15 bg-status-critical/6'}"
  >
    <span
      class="h-1.5 w-1.5 rounded-full
        {online
          ? 'bg-status-ok shadow-[0_0_6px_rgba(52,217,172,0.5)]'
          : 'bg-status-critical shadow-[0_0_6px_rgba(240,104,104,0.5)] animate-pulse'}"
    ></span>
    <span class="text-[0.75rem] font-semibold {online ? 'text-status-ok' : 'text-status-critical'}">
      {online ? t("status.online") : t("status.offline")}
    </span>
  </div>
{:else}
  <div class="flex items-center gap-2 rounded-full border border-border-subtle bg-surface-overlay px-3 py-1.5">
    <span class="h-1.5 w-1.5 rounded-full bg-text-muted/40"></span>
    <span class="text-[0.75rem] font-semibold text-text-muted">…</span>
  </div>
{/if}
