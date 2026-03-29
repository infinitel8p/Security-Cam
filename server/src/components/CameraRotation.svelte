<script lang="ts">
  import { getBackendUrl } from "../lib/api";

  interface Props {
    current: number;
  }

  let { current }: Props = $props();
  let value = $state(current);
  let saving = $state(false);
  let saved = $state(false);

  async function save() {
    if (value === current) return;
    saving = true;
    try {
      await fetch(`${getBackendUrl()}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ RotationAngle: value }),
      });
      current = value;
      saved = true;
      setTimeout(() => (saved = false), 2000);
    } catch (e) {
      console.error("Failed to save rotation:", e);
      value = current;
    } finally {
      saving = false;
    }
  }
</script>

<div class="card px-4 py-3.5 sm:px-5 sm:py-4">
  <div class="flex items-center gap-2.5">
    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
      <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="1 4 1 10 7 10" />
        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
      </svg>
    </div>
    <label class="text-sm font-semibold text-text-primary" for="rotation">Camera Rotation</label>
  </div>
  <div class="mt-3 flex items-center gap-3">
    <select
      id="rotation"
      bind:value={value}
      onchange={save}
      disabled={saving}
      class="rounded-xl border border-border-default bg-surface-elevated px-3.5 py-2 text-sm font-medium text-text-primary outline-none transition-all duration-200 focus:border-accent focus:shadow-[var(--shadow-glow)] disabled:opacity-50"
    >
      <option value={0}>0&deg; — Default</option>
      <option value={90}>90&deg; — Clockwise</option>
      <option value={180}>180&deg; — Flipped</option>
      <option value={270}>270&deg; — Counter-clockwise</option>
    </select>
    {#if saving}
      <span class="text-xs font-medium text-text-muted">Saving...</span>
    {/if}
    {#if saved}
      <span class="flex items-center gap-1 text-xs font-medium text-status-ok">
        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        Saved
      </span>
    {/if}
  </div>
</div>
