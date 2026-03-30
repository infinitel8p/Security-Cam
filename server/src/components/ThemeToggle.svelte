<script lang="ts">
  import { onMount } from "svelte";

  type ThemeMode = "system" | "light" | "dark";

  let mode: ThemeMode = $state("system");

  const order: ThemeMode[] = ["system", "light", "dark"];

  onMount(() => {
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    mode = saved === "light" || saved === "dark" ? saved : "system";
  });

  function apply(m: ThemeMode) {
    const isLight =
      m === "light" ||
      (m === "system" && window.matchMedia("(prefers-color-scheme: light)").matches);
    document.documentElement.classList.toggle("light", isLight);
  }

  function cycle() {
    const next = order[(order.indexOf(mode) + 1) % order.length];
    mode = next;
    if (next === "system") {
      localStorage.removeItem("theme");
    } else {
      localStorage.setItem("theme", next);
    }
    apply(next);
  }
</script>

<button
  onclick={cycle}
  class="btn-press flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary"
  title="{mode === 'system' ? 'Theme: System' : mode === 'light' ? 'Theme: Light' : 'Theme: Dark'}"
  aria-label="Cycle theme: system, light, dark"
>
  {#if mode === "system"}
    <!-- Monitor icon -->
    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
      <line x1="8" y1="21" x2="16" y2="21" />
      <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  {:else if mode === "light"}
    <!-- Sun icon -->
    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  {:else}
    <!-- Moon icon -->
    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  {/if}
</button>
