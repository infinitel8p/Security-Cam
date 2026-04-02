<script lang="ts">
  import { onMount } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import activityIcon from "../icons/activity.svg?raw";

  interface EventEntry {
    ts: string;
    type: string;
    severity: "ok" | "warn" | "critical";
  }

  const ROWS = 7;
  const DAY_MS = 86400000;
  const CELL_SIZE = 11;
  const GAP = 2;
  const LABEL_WIDTH = 14;

  const dayLabels = ["M", "", "W", "", "F", "", "S"];

  interface Cell {
    date: string;
    label: string;
    count: number;
    maxSeverity: "empty" | "ok" | "warn" | "critical";
    inRange: boolean;
  }

  let containerEl: HTMLDivElement;
  let weeks = $state(0);
  let cells: Cell[] = $state([]);
  let allEvents: EventEntry[] = $state([]);
  let loading = $state(true);
  let error = $state(false);
  let hoveredCell: Cell | null = $state(null);
  let maxCount = $state(1);

  function calcWeeks(containerWidth: number): number {
    const padding = 40;
    const labelAndGap = LABEL_WIDTH + 6;
    const available = containerWidth - padding - labelAndGap;
    return Math.max(4, Math.floor(available / (CELL_SIZE + GAP)));
  }

  function buildCells(events: EventEntry[], numWeeks: number): Cell[] {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const todayDay = today.getDay();
    const mondayOffset = todayDay === 0 ? -6 : 1 - todayDay;
    const thisMonday = new Date(today.getTime() + mondayOffset * DAY_MS);
    const gridStart = new Date(thisMonday.getTime() - (numWeeks - 1) * 7 * DAY_MS);

    const eventsByDate = new Map<string, EventEntry[]>();
    for (const e of events) {
      const d = new Date(e.ts);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      const arr = eventsByDate.get(key);
      if (arr) arr.push(e);
      else eventsByDate.set(key, [e]);
    }

    const result: Cell[] = [];
    let maxC = 0;

    for (let col = 0; col < numWeeks; col++) {
      for (let row = 0; row < ROWS; row++) {
        const dayOffset = col * 7 + row;
        const cellDate = new Date(gridStart.getTime() + dayOffset * DAY_MS);
        const key = `${cellDate.getFullYear()}-${String(cellDate.getMonth() + 1).padStart(2, "0")}-${String(cellDate.getDate()).padStart(2, "0")}`;
        const dayEvents = eventsByDate.get(key) ?? [];
        const count = dayEvents.length;
        if (count > maxC) maxC = count;

        let maxSeverity: Cell["maxSeverity"] = "empty";
        if (dayEvents.some((e) => e.severity === "critical")) maxSeverity = "critical";
        else if (dayEvents.some((e) => e.severity === "warn")) maxSeverity = "warn";
        else if (dayEvents.length > 0) maxSeverity = "ok";

        const inRange = cellDate <= today;
        const label = cellDate.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
        result.push({ date: key, label, count, maxSeverity, inRange });
      }
    }

    maxCount = Math.max(maxC, 1);
    return result;
  }

  function cellColor(cell: Cell): string {
    if (!cell.inRange || cell.count === 0) return "bg-surface-elevated";
    const intensity = Math.min(cell.count / maxCount, 1);
    if (cell.maxSeverity === "critical") {
      if (intensity > 0.6) return "bg-status-critical";
      if (intensity > 0.3) return "bg-status-critical/60";
      return "bg-status-critical/30";
    }
    if (cell.maxSeverity === "warn") {
      if (intensity > 0.6) return "bg-status-warning";
      if (intensity > 0.3) return "bg-status-warning/60";
      return "bg-status-warning/30";
    }
    if (intensity > 0.6) return "bg-status-ok";
    if (intensity > 0.3) return "bg-status-ok/60";
    return "bg-status-ok/30";
  }

  function rebuild() {
    if (!containerEl || containerEl.clientWidth === 0) return;
    const w = calcWeeks(containerEl.clientWidth);
    weeks = w;
    cells = buildCells(allEvents, weeks);
  }

  async function fetchEvents() {
    loading = true;
    error = false;
    try {
      const res = await apiFetch(`${getBackendUrl()}/event_history?hours=4380`);
      if (!res.ok) throw new Error();
      allEvents = await res.json();
      rebuild();
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    initLocale();
    fetchEvents();
    const ro = new ResizeObserver(() => rebuild());
    ro.observe(containerEl);
    return () => ro.disconnect();
  });
</script>

<div bind:this={containerEl} class="card overflow-hidden px-4 py-3 sm:px-5 sm:py-3.5">
  <div class="flex min-h-[1.25rem] items-center justify-between gap-2">
    <div class="flex shrink-0 items-center gap-1.5">
      <Icon icon={activityIcon} class="h-3 w-3 text-text-muted" />
      <p class="text-[0.625rem] font-medium uppercase tracking-wider text-text-muted">
        {t("label.activityHeatmap")}
      </p>
    </div>
    {#if hoveredCell && hoveredCell.inRange}
      <span class="truncate text-[0.625rem] tabular-nums text-text-muted">
        {hoveredCell.label} ·
        <span class="{hoveredCell.maxSeverity === 'critical' ? 'text-status-critical' : hoveredCell.maxSeverity === 'warn' ? 'text-status-warning' : hoveredCell.count > 0 ? 'text-status-ok' : 'text-text-muted'}">
          {hoveredCell.count} {hoveredCell.count === 1 ? "event" : "events"}
        </span>
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="mt-2">
      <div class="skeleton h-[38px] w-full rounded-[3px]"></div>
    </div>
  {:else if error}
    <div class="mt-2 flex items-center justify-center gap-2">
      <p class="text-[0.6875rem] text-text-muted">{t("error.eventData")}</p>
      <button onclick={fetchEvents} class="text-[0.6875rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
    </div>
  {:else if weeks > 0}
    <div class="mt-2 flex gap-1" onmouseleave={() => (hoveredCell = null)}>
      <!-- Day labels -->
      <div class="grid shrink-0 gap-[2px]" style="grid-template-rows: repeat(7, {CELL_SIZE}px);">
        {#each dayLabels as day}
          <div class="flex items-center">
            <span class="text-[0.5rem] leading-none text-text-muted">{day}</span>
          </div>
        {/each}
      </div>

      <!-- Heatmap -->
      <div class="heatmap">
        {#each cells as cell}
          <div
            class="rounded-[2px] transition-opacity duration-100
              {cellColor(cell)}
              {cell.inRange ? 'cursor-crosshair' : 'opacity-30'}
              {hoveredCell && hoveredCell !== cell ? 'opacity-40' : ''}"
            role="presentation"
            onmouseenter={() => { if (cell.inRange) hoveredCell = cell; }}
          ></div>
        {/each}
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-1.5 flex items-center justify-end gap-1.5">
      <span class="text-[0.5rem] text-text-muted">Less</span>
      <div class="flex gap-[2px]">
        <div class="h-1.5 w-1.5 rounded-[1px] bg-surface-elevated"></div>
        <div class="h-1.5 w-1.5 rounded-[1px] bg-status-ok/30"></div>
        <div class="h-1.5 w-1.5 rounded-[1px] bg-status-ok"></div>
        <div class="h-1.5 w-1.5 rounded-[1px] bg-status-warning"></div>
        <div class="h-1.5 w-1.5 rounded-[1px] bg-status-critical"></div>
      </div>
      <span class="text-[0.5rem] text-text-muted">More</span>
    </div>
  {/if}
</div>

<style>
  .heatmap {
    display: grid;
    grid-template-rows: repeat(7, 11px);
    grid-auto-flow: column;
    grid-auto-columns: 11px;
    gap: 2px;
  }
</style>
