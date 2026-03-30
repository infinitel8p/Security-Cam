<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  let time = $state("");
  let interval: ReturnType<typeof setInterval> | null = null;

  function update() {
    const now = new Date();
    time = now.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  onMount(() => {
    update();
    interval = setInterval(update, 1000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

{#if time}
  <span class="text-[0.6875rem] tabular-nums text-text-muted">{time}</span>
{/if}
