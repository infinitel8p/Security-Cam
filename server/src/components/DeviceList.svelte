<script lang="ts">
  interface Props {
    title: string;
    icon: "bluetooth" | "wifi";
    devices: { name: string; address: string }[];
  }

  let { title, icon, devices }: Props = $props();
</script>

<div class="card overflow-hidden">
  <div class="flex items-center gap-2.5 border-b border-border-subtle px-4 py-3 sm:px-5 sm:py-3.5">
    {#if icon === "bluetooth"}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6.5 6.5 17.5 17.5 12 23 12 1 17.5 6.5 6.5 17.5" />
        </svg>
      </div>
    {:else}
      <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10">
        <svg class="h-3.5 w-3.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0" />
          <path d="M1.42 9a16 16 0 0 1 21.16 0" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <line x1="12" y1="20" x2="12.01" y2="20" />
        </svg>
      </div>
    {/if}
    <h3 class="text-sm font-semibold text-text-primary">{title}</h3>
    <span class="ml-auto rounded-full bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold text-text-muted">
      {devices.length}
    </span>
  </div>

  {#if devices.length === 0}
    <p class="px-4 py-6 sm:px-5 sm:py-8 text-center text-sm text-text-muted">No devices configured</p>
  {:else}
    <ul class="divide-y divide-border-subtle">
      {#each devices as device, i (i)}
        <li class="flex flex-col gap-1 px-4 py-2.5 transition-colors hover:bg-surface-overlay/50 sm:flex-row sm:items-center sm:justify-between sm:px-5 sm:py-3">
          <div class="flex min-w-0 items-center gap-3">
            <span class="h-2 w-2 shrink-0 rounded-full bg-status-ok shadow-[0_0_6px_rgba(0,230,118,0.4)]"></span>
            <span class="truncate text-sm font-medium text-text-primary">{device.name}</span>
          </div>
          <code class="ml-5 shrink-0 rounded-lg bg-surface-elevated px-2.5 py-1 text-[0.6875rem] font-medium text-text-muted sm:ml-0">{device.address}</code>
        </li>
      {/each}
    </ul>
  {/if}
</div>
