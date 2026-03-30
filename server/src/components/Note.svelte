<script lang="ts">
  import type { Snippet } from "svelte";
  import Icon from "./Icon.svelte";
  import alertTriangleIcon from "../icons/alert-triangle.svg?raw";
  import infoCircleIcon from "../icons/info-circle.svg?raw";

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
    <Icon icon={alertTriangleIcon} class="mt-0.5 h-3.5 w-3.5 shrink-0 {s.icon}" stroke={2.5} />
  {:else}
    <Icon icon={infoCircleIcon} class="mt-0.5 h-3.5 w-3.5 shrink-0 {s.icon}" stroke={2.5} />
  {/if}
  <p class="text-xs leading-relaxed {s.text}">
    {@render children()}
  </p>
</div>
