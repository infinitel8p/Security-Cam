<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    variant?: "info" | "warning";
    children: Snippet;
  }

  let { variant = "info", children }: Props = $props();

  const styles = {
    info: {
      border: "border-accent/15",
      bg: "bg-accent/5",
      icon: "text-accent",
      text: "text-accent/80",
    },
    warning: {
      border: "border-status-warning/20",
      bg: "bg-status-warning/5",
      icon: "text-status-warning",
      text: "text-status-warning",
    },
  } as const;

  let s = $derived(styles[variant]);
</script>

<div class="flex items-start gap-2 rounded-lg border {s.border} {s.bg} px-3 py-2">
  {#if variant === "warning"}
    <svg class="mt-0.5 h-3.5 w-3.5 shrink-0 {s.icon}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  {:else}
    <svg class="mt-0.5 h-3.5 w-3.5 shrink-0 {s.icon}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  {/if}
  <p class="text-xs leading-relaxed {s.text}">
    {@render children()}
  </p>
</div>
