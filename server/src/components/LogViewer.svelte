<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { apiFetch } from "../lib/fetch";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import searchIcon from "../icons/search.svg?raw";
  import loaderIcon from "../icons/loader-2.svg?raw";
  import alertIcon from "../icons/alert-circle.svg?raw";
  import downloadIcon from "../icons/download.svg?raw";
  import xIcon from "../icons/x.svg?raw";
  import chevronDownIcon from "../icons/chevron-down.svg?raw";

  interface LogEntry {
    ts: string;
    level: string;
    source: string;
    message: string;
  }

  interface InstallLog {
    name: string;
    size: number;
    category: string;
  }

  let activeTab = $state<"api" | "mediamtx" | "install">("api");

  // API logs state
  let logs = $state<LogEntry[]>([]);
  let loading = $state(true);
  let error = $state(false);
  let levelFilter = $state<string>("");
  let searchInput = $state("");
  let sourceFilter = $state("");
  let autoRefresh = $state(true);
  let refreshTimer: ReturnType<typeof setInterval> | null = null;
  let newCount = $state(0); // number of new entries from last refresh
  let newCountTimer: ReturnType<typeof setTimeout> | null = null;

  // Keyboard navigation
  let focusedRow = $state(-1);
  let searchEl: HTMLInputElement | undefined = $state();

  // Install logs state
  let installLogs = $state<InstallLog[]>([]);
  let installLoading = $state(false);
  let installError = $state(false);
  let selectedInstallLog = $state<string>("");
  let installContent = $state<string>("");
  let installContentLoading = $state(false);

  // MediaMTX logs state
  let mtxLogs = $state<LogEntry[]>([]);
  let mtxLoading = $state(false);
  let mtxError = $state(false);
  let mtxLevelFilter = $state<string>("");
  let mtxSearchInput = $state("");
  let mtxSourceFilter = $state("");
  let mtxSearchEl: HTMLInputElement | undefined = $state();

  const REFRESH_INTERVAL = 5000;

  let fetchingApi = false;
  let fetchingMtx = false;

  async function fetchMtxLogs() {
    if (typeof document !== "undefined" && document.hidden) return;
    if (fetchingMtx) return;
    fetchingMtx = true;
    try {
      const params = new URLSearchParams({ limit: "2000" });
      if (mtxLevelFilter) params.set("level", mtxLevelFilter);
      const res = await apiFetch(`${getBackendUrl()}/logs/mediamtx?${params}`);
      if (!res.ok) throw new Error();
      mtxLogs = await res.json();
      mtxError = false;
    } catch {
      // Only show error state if we have no data yet
      if (mtxLogs.length === 0) mtxError = true;
    } finally {
      mtxLoading = false;
      fetchingMtx = false;
    }
  }

  async function fetchApiLogs() {
    if (typeof document !== "undefined" && document.hidden) return;
    if (fetchingApi) return; // prevent overlapping requests
    fetchingApi = true;
    try {
      const params = new URLSearchParams({ limit: "2000" });
      if (levelFilter) params.set("level", levelFilter);
      if (sourceFilter) params.set("source", sourceFilter);
      const res = await apiFetch(`${getBackendUrl()}/logs/api?${params}`);
      if (!res.ok) throw new Error();
      const fresh: LogEntry[] = await res.json();
      // Detect how many new entries appeared since last fetch
      if (logs.length > 0 && fresh.length > 0 && fresh[0].ts !== logs[0].ts) {
        const prevTop = logs[0].ts;
        const added = fresh.findIndex((e) => e.ts === prevTop);
        if (added > 0) {
          newCount = added;
          if (newCountTimer) clearTimeout(newCountTimer);
          newCountTimer = setTimeout(() => { newCount = 0; }, 3000);
        }
      }
      logs = fresh;
      error = false;
    } catch {
      // Only show error state if we have no data yet
      if (logs.length === 0) error = true;
    } finally {
      loading = false;
      fetchingApi = false;
    }
  }

  async function fetchInstallLogs() {
    installLoading = true;
    installError = false;
    try {
      const res = await apiFetch(`${getBackendUrl()}/logs/install`);
      if (!res.ok) throw new Error();
      installLogs = await res.json();
      // Auto-select newest
      if (installLogs.length > 0 && !selectedInstallLog) {
        selectedInstallLog = installLogs[0].name;
        await fetchInstallContent(installLogs[0].name);
      }
    } catch {
      installError = true;
    } finally {
      installLoading = false;
    }
  }

  async function fetchInstallContent(name: string) {
    installContentLoading = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/logs/script/${name}`);
      if (!res.ok) throw new Error();
      installContent = await res.text();
    } catch {
      installContent = t("logs.errorLoading");
    } finally {
      installContentLoading = false;
    }
  }

  function startAutoRefresh() {
    stopAutoRefresh();
    if (autoRefresh && (activeTab === "api" || activeTab === "mediamtx")) {
      const fn = activeTab === "api" ? fetchApiLogs : fetchMtxLogs;
      refreshTimer = setInterval(fn, REFRESH_INTERVAL);
    }
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  function handleLevelChange(level: string) {
    levelFilter = level;
    loading = true;
    fetchApiLogs();
    startAutoRefresh();
  }

  function handleTabChange(tab: "api" | "mediamtx" | "install") {
    activeTab = tab;
    focusedRow = -1;
    scrollTop = 0;
    if (scrollContainerEl) scrollContainerEl.scrollTop = 0;
    if (tab === "install" && installLogs.length === 0) {
      fetchInstallLogs();
    }
    if (tab === "mediamtx" && mtxLogs.length === 0) {
      mtxLoading = true;
      fetchMtxLogs();
    }
    if (tab === "api" || tab === "mediamtx") {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }

  async function handleInstallLogSelect(name: string) {
    selectedInstallLog = name;
    await fetchInstallContent(name);
  }

  function downloadLog() {
    if (activeTab === "api" || activeTab === "mediamtx") {
      const entries = activeTab === "api" ? logs : mtxLogs;
      if (entries.length === 0) return;
      const filename = activeTab === "api" ? "security-cam-api.log" : "mediamtx.log";
      const text = entries
        .map((l) => `${l.ts} [${l.level}] ${l.source}: ${l.message}`)
        .join("\n");
      const blob = new Blob([text], { type: "text/plain" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    } else if (selectedInstallLog && installContent) {
      const blob = new Blob([installContent], { type: "text/plain" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = selectedInstallLog.split("/").pop() || selectedInstallLog;
      a.click();
      URL.revokeObjectURL(a.href);
    }
  }

  function levelColor(level: string): string {
    switch (level) {
      case "ERROR": return "text-status-critical";
      case "WARNING": return "text-status-warning";
      case "INFO": return "text-status-ok";
      case "DEBUG": return "text-text-muted";
      default: return "text-text-secondary";
    }
  }

  function levelBgColor(level: string): string {
    switch (level) {
      case "ERROR": return "bg-status-critical/10";
      case "WARNING": return "bg-status-warning/10";
      case "INFO": return "bg-status-ok/10";
      case "DEBUG": return "bg-surface-overlay";
      default: return "bg-surface-overlay";
    }
  }

  /** Active filter pill style keyed to level - semantic color instead of generic accent */
  function levelActiveClass(level: string): string {
    switch (level) {
      case "ERROR": return "bg-status-critical/15 text-status-critical";
      case "WARNING": return "bg-status-warning/15 text-status-warning";
      case "INFO": return "bg-status-ok/15 text-status-ok";
      case "DEBUG": return "bg-surface-elevated text-text-secondary";
      default: return "bg-accent/15 text-accent"; // "All" filter
    }
  }

  /** Deterministic hue from source name - makes log sources visually distinct */
  function sourceHue(name: string): number {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
    return Math.abs(hash) % 360;
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function categoryLabel(category: string): string {
    const labels: Record<string, string> = {
      install: t("logs.catInstall"),
      update: t("logs.catUpdate"),
      "ap-setup": t("logs.catApSetup"),
      "bluetooth-pairing": t("logs.catBluetooth"),
    };
    return labels[category] || category;
  }

  /** Category color dot - semantic association for install log types */
  function categoryDotColor(category: string): string {
    switch (category) {
      case "install": return "bg-accent";
      case "update": return "bg-status-ok";
      case "ap-setup": return "bg-status-warning";
      case "bluetooth-pairing": return "bg-[#8b5cf6]"; // violet for wireless
      default: return "bg-text-muted";
    }
  }

  let expandedCategories = $state<Set<string>>(new Set());

  let groupedInstallLogs = $derived.by(() => {
    const groups = new Map<string, InstallLog[]>();
    for (const log of installLogs) {
      const cat = log.category || "install";
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push(log);
    }
    return [...groups.entries()];
  });

  // Auto-expand category only when a NEW log is selected (not on re-render)
  let lastAutoExpanded = "";
  $effect(() => {
    if (selectedInstallLog && selectedInstallLog !== lastAutoExpanded) {
      lastAutoExpanded = selectedInstallLog;
      const match = installLogs.find((l) => l.name === selectedInstallLog);
      if (match) {
        const cat = match.category || "install";
        if (!expandedCategories.has(cat)) {
          expandedCategories = new Set([...expandedCategories, cat]);
        }
      }
    }
  });

  function toggleCategory(category: string) {
    const next = new Set(expandedCategories);
    if (next.has(category)) {
      next.delete(category);
      // Clear selected log if it belongs to the collapsed category
      if (selectedInstallLog) {
        const match = installLogs.find((l) => l.name === selectedInstallLog);
        if (match && (match.category || "install") === category) {
          selectedInstallLog = "";
        }
      }
    } else {
      next.add(category);
    }
    expandedCategories = next;
  }

  // Client-side instant search: filter the already-loaded entries by text match
  let filteredApiLogs = $derived.by(() => {
    const q = searchInput.toLowerCase().trim();
    if (!q) return logs;
    return logs.filter((e) => e.message.toLowerCase().includes(q) || e.source.toLowerCase().includes(q) || e.ts.includes(q));
  });
  let filteredMtxLogs = $derived.by(() => {
    const q = mtxSearchInput.toLowerCase().trim();
    if (!q) return mtxSourceFilter ? mtxLogs.filter((l) => l.source === mtxSourceFilter) : mtxLogs;
    const base = mtxSourceFilter ? mtxLogs.filter((l) => l.source === mtxSourceFilter) : mtxLogs;
    return base.filter((e) => e.message.toLowerCase().includes(q) || e.source.toLowerCase().includes(q) || e.ts.includes(q));
  });

  // Virtual scroll state
  const ROW_H = 28; // px per row (desktop table)
  const VIEWPORT_ROWS = 25; // visible rows in scroll container
  const OVERSCAN = 5; // extra rows rendered above/below viewport
  let scrollTop = $state(0);
  let scrollContainerEl: HTMLDivElement | undefined = $state();

  // Unique source names - accumulated across fetches so the dropdown stays populated
  let knownSourcesApi = new Set<string>();
  let knownSourcesMtx = new Set<string>();
  let sourcesApi = $derived.by(() => {
    for (const l of logs) knownSourcesApi.add(l.source);
    return [...knownSourcesApi].sort();
  });
  let sourcesMtx = $derived.by(() => {
    for (const l of mtxLogs) knownSourcesMtx.add(l.source);
    return [...knownSourcesMtx].sort();
  });

  // Count by level for filter badges (show when no server-side filters active)
  let levelCounts = $derived.by(() => {
    if (levelFilter || sourceFilter) return null;
    const counts: Record<string, number> = {};
    for (const l of logs) {
      counts[l.level] = (counts[l.level] || 0) + 1;
    }
    return counts;
  });

  function handleKeydown(e: KeyboardEvent) {
    // Don't capture when typing in an input
    const tag = (e.target as HTMLElement)?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
      if (e.key === "Escape") { (e.target as HTMLElement).blur(); e.preventDefault(); }
      return;
    }
    if (activeTab === "install") return;

    const entries = activeTab === "api" ? filteredApiLogs : filteredMtxLogs;
    const maxIdx = entries.length - 1;

    switch (e.key) {
      case "j": case "ArrowDown":
        e.preventDefault();
        focusedRow = Math.min(focusedRow + 1, maxIdx);
        scrollToFocused();
        break;
      case "k": case "ArrowUp":
        e.preventDefault();
        focusedRow = Math.max(focusedRow - 1, 0);
        scrollToFocused();
        break;
      case "g":
        focusedRow = 0;
        scrollToFocused();
        break;
      case "G":
        focusedRow = maxIdx;
        scrollToFocused();
        break;
      case "/":
        e.preventDefault();
        const el = activeTab === "api" ? searchEl : mtxSearchEl;
        el?.focus();
        break;
      case "e":
        handleLevelQuickFilter("ERROR");
        break;
      case "w":
        handleLevelQuickFilter("WARNING");
        break;
      case "i":
        handleLevelQuickFilter("INFO");
        break;
      case "d":
        handleLevelQuickFilter("DEBUG");
        break;
      case "a":
        handleLevelQuickFilter("");
        break;
      case "Escape":
        focusedRow = -1;
        break;
    }
  }

  function handleLevelQuickFilter(level: string) {
    if (activeTab === "api") {
      if (levelFilter === level) return;
      handleLevelChange(level);
    } else if (activeTab === "mediamtx") {
      if (mtxLevelFilter === level) return;
      mtxLevelFilter = level;
      mtxLoading = true;
      fetchMtxLogs();
    }
    focusedRow = -1;
  }

  function scrollToFocused() {
    if (!scrollContainerEl || focusedRow < 0) return;
    const rowTop = focusedRow * ROW_H;
    const viewH = scrollContainerEl.clientHeight;
    if (rowTop < scrollContainerEl.scrollTop) {
      scrollContainerEl.scrollTop = rowTop;
    } else if (rowTop + ROW_H > scrollContainerEl.scrollTop + viewH) {
      scrollContainerEl.scrollTop = rowTop + ROW_H - viewH;
    }
  }

  function handleScroll() {
    if (scrollContainerEl) scrollTop = scrollContainerEl.scrollTop;
  }

  // Reset focused row when data changes
  $effect(() => { filteredApiLogs; filteredMtxLogs; focusedRow = -1; });

  onMount(() => {
    initLocale();
    fetchApiLogs();
    startAutoRefresh();
    document.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    stopAutoRefresh();
    if (newCountTimer) clearTimeout(newCountTimer);
    if (typeof document !== "undefined") document.removeEventListener("keydown", handleKeydown);
  });

  // Restart auto-refresh when toggle changes
  $effect(() => {
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  });
</script>

<!-- ── Reusable snippets for log display (shared between API + MediaMTX tabs) ── -->

{#snippet logSkeleton()}
  <div class="card px-4 py-3">
    <div class="space-y-2">
      {#each Array(8) as _, i}
        <div class="flex gap-3 animate-pulse" style="animation-delay: {i * 60}ms">
          <div class="h-4 w-36 rounded bg-surface-overlay"></div>
          <div class="h-4 w-12 rounded bg-surface-overlay"></div>
          <div class="h-4 flex-1 rounded bg-surface-overlay"></div>
        </div>
      {/each}
    </div>
  </div>
{/snippet}

{#snippet logError(retryFn: () => void)}
  <div class="card flex flex-col items-center gap-3 px-4 py-10 text-center">
    <Icon icon={alertIcon} class="h-8 w-8 text-text-muted" />
    <p class="text-[0.8125rem] text-text-muted">{t("logs.errorLoading")}</p>
    <button
      onclick={retryFn}
      class="rounded-lg bg-accent/10 px-4 py-2 text-[0.8125rem] font-medium text-accent transition-colors hover:bg-accent/20"
    >
      {t("btn.retry")}
    </button>
  </div>
{/snippet}

{#snippet logEmpty(hasFilters: boolean)}
  <div class="card flex flex-col items-center gap-3 px-4 py-12 text-center">
    <div class="flex items-center gap-1 text-text-muted/30">
      <span class="text-2xl font-mono font-bold leading-none">&#x2205;</span>
    </div>
    <p class="text-[0.8125rem] text-text-muted">{hasFilters ? t("logs.empty") : t("logs.emptyNoFilters")}</p>
  </div>
{/snippet}

{#snippet logTable(entries: LogEntry[])}
  {@const totalH = entries.length * ROW_H}
  {@const startIdx = Math.max(0, Math.floor(scrollTop / ROW_H) - OVERSCAN)}
  {@const endIdx = Math.min(entries.length, Math.ceil((scrollTop + VIEWPORT_ROWS * ROW_H) / ROW_H) + OVERSCAN)}
  {@const visibleEntries = entries.slice(startIdx, endIdx)}
  {@const offsetY = startIdx * ROW_H}

  <!-- Desktop: virtualized table -->
  <div class="hidden sm:block">
    <table class="w-full log-table">
      <thead>
        <tr class="border-b border-border-subtle text-left text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">
          <th class="px-4 py-2.5" style="width: 160px;">{t("logs.timestamp")}</th>
          <th class="px-4 py-2.5" style="width: 80px;">{t("logs.level")}</th>
          <th class="px-4 py-2.5" style="width: 112px;">{t("logs.source")}</th>
          <th class="px-4 py-2.5">{t("logs.message")}</th>
        </tr>
      </thead>
    </table>
    <div
      bind:this={scrollContainerEl}
      onscroll={handleScroll}
      class="overflow-y-auto overflow-x-hidden"
      style="max-height: {VIEWPORT_ROWS * ROW_H}px;"
      role="log"
    >
      <div style="height: {totalH}px; position: relative;">
        <table class="w-full log-table" style="position: absolute; top: {offsetY}px;">
          <tbody class="font-mono text-[0.75rem]">
            {#each visibleEntries as entry, vi}
              {@const idx = startIdx + vi}
              <tr
                class="log-row border-b border-border-subtle/50 cursor-pointer transition-colors
                  {idx === focusedRow ? 'log-row-focused' : 'hover:bg-surface-overlay/50'}
                  {entry.level === 'ERROR' && idx !== focusedRow ? 'log-row-error' : entry.level === 'WARNING' && idx !== focusedRow ? 'log-row-warn' : ''}"
                style="height: {ROW_H}px;"
                onclick={() => { focusedRow = idx; }}
              >
                <td class="whitespace-nowrap px-4 py-1.5 text-text-muted" style="width: 160px;">{entry.ts}</td>
                <td class="px-4 py-1.5" style="width: 80px;">
                  <span class="inline-flex rounded px-1.5 py-0.5 text-[0.625rem] font-semibold {levelColor(entry.level)} {levelBgColor(entry.level)}">
                    {entry.level}
                  </span>
                </td>
                <td class="whitespace-nowrap px-4 py-1.5" style="width: 112px;">
                  <span class="log-source" style="--src-hue: {sourceHue(entry.source)}">{entry.source}</span>
                </td>
                <td class="px-4 py-1.5 text-text-primary truncate max-w-0">{entry.message}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Mobile: stacked card layout (no virtual scroll needed - fewer visible rows) -->
  <div class="sm:hidden divide-y divide-border-subtle/50 max-h-[70vh] overflow-y-auto">
    {#each entries.slice(0, 200) as entry, i (entry.ts + entry.source + i)}
      <div class="log-row px-3.5 py-2.5 {entry.level === 'ERROR' ? 'log-row-error' : entry.level === 'WARNING' ? 'log-row-warn' : ''}">
        <div class="flex items-center gap-2">
          <span class="inline-flex rounded px-1.5 py-0.5 text-[0.625rem] font-semibold {levelColor(entry.level)} {levelBgColor(entry.level)}">
            {entry.level}
          </span>
          <span class="font-mono text-[0.6875rem] text-text-muted">{entry.ts}</span>
          <span class="log-source ml-auto" style="--src-hue: {sourceHue(entry.source)}">{entry.source}</span>
        </div>
        <p class="mt-1 font-mono text-[0.75rem] text-text-primary break-all leading-relaxed">{entry.message}</p>
      </div>
    {/each}
  </div>
{/snippet}

{#snippet logStatusBar(shown: number, total: number, showNewBadge: boolean)}
  <div class="border-t border-border-subtle px-4 py-2 text-[0.6875rem] text-text-muted flex items-center justify-between">
    <span>{t("logs.showing", { n: String(shown), total: String(total) })}</span>
    <span class="inline-flex items-center gap-3">
      {#if showNewBadge && newCount > 0}
        <span class="log-new-badge">+{newCount}</span>
      {/if}
      {#if autoRefresh}
        <span class="inline-flex items-center gap-1.5 text-status-ok">
          <span class="log-live-dot"></span>
          <span class="text-[0.625rem] font-semibold uppercase tracking-wider">{t("logs.live")}</span>
        </span>
      {/if}
    </span>
  </div>
{/snippet}

<div class="mt-6 animate-in space-y-5" style="--stagger: 1">
  <!-- Tab bar + controls -->
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <!-- Tabs -->
    <div class="flex gap-1 rounded-xl bg-surface-overlay p-1">
      <button
        onclick={() => handleTabChange("api")}
        class="rounded-lg px-3 py-2 sm:px-4 text-[0.8125rem] font-medium transition-all duration-200
          {activeTab === 'api'
            ? 'bg-surface-raised text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'}"
      >
        {t("logs.apiLogs")}
      </button>
      <button
        onclick={() => handleTabChange("mediamtx")}
        class="rounded-lg px-3 py-2 sm:px-4 text-[0.8125rem] font-medium transition-all duration-200
          {activeTab === 'mediamtx'
            ? 'bg-surface-raised text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'}"
      >
        {t("logs.mediamtxLogs")}
      </button>
      <button
        onclick={() => handleTabChange("install")}
        class="rounded-lg px-3 py-2 sm:px-4 text-[0.8125rem] font-medium transition-all duration-200
          {activeTab === 'install'
            ? 'bg-surface-raised text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'}"
      >
        {t("logs.installLogs")}
      </button>
    </div>

    <!-- Controls -->
    <div class="flex items-center gap-2">
      {#if activeTab === "api" || activeTab === "mediamtx"}
        <label class="flex items-center gap-2 text-[0.75rem] text-text-muted">
          <input
            type="checkbox"
            bind:checked={autoRefresh}
            class="h-3.5 w-3.5 rounded border-border-subtle accent-accent"
          />
          {t("logs.autoRefresh")}
        </label>
      {/if}
      <button
        onclick={downloadLog}
        class="flex h-8 items-center gap-1.5 rounded-lg bg-surface-overlay px-2.5 sm:px-3 text-[0.75rem] font-medium text-text-secondary transition-colors hover:bg-surface-raised hover:text-text-primary"
        title={t("btn.download")}
        aria-label={t("btn.download")}
      >
        <Icon icon={downloadIcon} class="h-3.5 w-3.5" />
        <span class="hidden sm:inline">{t("btn.download")}</span>
      </button>
    </div>
  </div>

  {#key activeTab}
  <div class="log-tab-content">
  {#if activeTab === "api"}
    <!-- API log filters -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
      <!-- Search (instant client-side filtering) -->
      <div class="relative flex-1">
        <Icon icon={searchIcon} class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          bind:this={searchEl}
          type="text"
          bind:value={searchInput}
          placeholder="{t('logs.searchPlaceholder')} (/)"
          class="h-9 w-full rounded-lg border border-border-subtle bg-surface-overlay pl-9 pr-8 text-[0.8125rem] text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        />
        {#if searchInput}
          <button
            type="button"
            onclick={() => { searchInput = ""; }}
            class="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 text-text-muted hover:text-text-secondary"
          >
            <Icon icon={xIcon} class="h-3.5 w-3.5" />
          </button>
        {/if}
      </div>

      <!-- Category filter -->
      {#if sourcesApi.length > 1}
        <select
          value={sourceFilter}
          onchange={(e) => { sourceFilter = (e.target as HTMLSelectElement).value; loading = true; fetchApiLogs(); startAutoRefresh(); }}
          class="h-9 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 text-[0.75rem] font-medium text-text-secondary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        >
          <option value="">{t("logs.allSources")}</option>
          {#each sourcesApi as src}
            <option value={src}>{src}</option>
          {/each}
        </select>
      {/if}

      <!-- Level filter -->
      <div class="flex gap-1 shrink-0">
        {#each [
          { value: "", label: t("logs.all") },
          { value: "ERROR", label: t("logs.levelError") },
          { value: "WARNING", label: t("logs.levelWarn") },
          { value: "INFO", label: t("logs.levelInfo") },
          { value: "DEBUG", label: t("logs.levelDebug") },
        ] as { value, label }}
          <button
            onclick={() => handleLevelChange(value)}
            class="shrink-0 rounded-lg px-2.5 py-1.5 text-[0.75rem] font-medium transition-all duration-200
              {levelFilter === value
                ? levelActiveClass(value)
                : 'text-text-muted hover:bg-surface-overlay hover:text-text-secondary'}"
          >
            {label}
            {#if !levelFilter && !sourceFilter && levelCounts && value && levelCounts[value]}
              <span class="ml-1 rounded-md bg-surface-overlay px-1 py-px text-[0.625rem] font-semibold tabular-nums">{levelCounts[value]}</span>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- API log output -->
    {#if loading && logs.length === 0}
      {@render logSkeleton()}
    {:else if error}
      {@render logError(() => { loading = true; fetchApiLogs(); })}
    {:else if logs.length === 0}
      {@render logEmpty(!!(levelFilter || sourceFilter))}
    {:else}
      <div class="card overflow-hidden">
        {#if filteredApiLogs.length === 0}
          {@render logEmpty(true)}
        {:else}
          {@render logTable(filteredApiLogs)}
          {@render logStatusBar(filteredApiLogs.length, logs.length, true)}
        {/if}
      </div>
    {/if}

  {:else if activeTab === "mediamtx"}
    <!-- MediaMTX log filters -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="relative flex-1">
        <Icon icon={searchIcon} class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          bind:this={mtxSearchEl}
          type="text"
          bind:value={mtxSearchInput}
          placeholder="{t('logs.searchPlaceholder')} (/)"
          class="h-9 w-full rounded-lg border border-border-subtle bg-surface-overlay pl-9 pr-8 text-[0.8125rem] text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        />
        {#if mtxSearchInput}
          <button
            type="button"
            onclick={() => { mtxSearchInput = ""; }}
            class="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 text-text-muted hover:text-text-secondary"
          >
            <Icon icon={xIcon} class="h-3.5 w-3.5" />
          </button>
        {/if}
      </div>

      <!-- Category filter -->
      {#if sourcesMtx.length > 1}
        <select
          value={mtxSourceFilter}
          onchange={(e) => { mtxSourceFilter = (e.target as HTMLSelectElement).value; }}
          class="h-9 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 text-[0.75rem] font-medium text-text-secondary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        >
          <option value="">{t("logs.allSources")}</option>
          {#each sourcesMtx as src}
            <option value={src}>{src}</option>
          {/each}
        </select>
      {/if}

      <div class="flex gap-1">
        {#each [
          { value: "", label: t("logs.all") },
          { value: "ERROR", label: t("logs.levelError") },
          { value: "WARNING", label: t("logs.levelWarn") },
          { value: "INFO", label: t("logs.levelInfo") },
          { value: "DEBUG", label: t("logs.levelDebug") },
        ] as { value, label }}
          <button
            onclick={() => { mtxLevelFilter = value; mtxLoading = true; fetchMtxLogs(); }}
            class="rounded-lg px-2.5 py-1.5 text-[0.75rem] font-medium transition-all duration-200
              {mtxLevelFilter === value
                ? levelActiveClass(value)
                : 'text-text-muted hover:bg-surface-overlay hover:text-text-secondary'}"
          >
            {label}
          </button>
        {/each}
      </div>
    </div>

    <!-- MediaMTX log output -->
    {#if mtxLoading && mtxLogs.length === 0}
      {@render logSkeleton()}
    {:else if mtxError}
      {@render logError(() => { mtxLoading = true; fetchMtxLogs(); })}
    {:else if mtxLogs.length === 0}
      {@render logEmpty(!!(mtxLevelFilter || mtxSourceFilter))}
    {:else}
      <div class="card overflow-hidden">
        {#if filteredMtxLogs.length === 0}
          {@render logEmpty(true)}
        {:else}
          {@render logTable(filteredMtxLogs)}
          {@render logStatusBar(filteredMtxLogs.length, mtxLogs.length, false)}
        {/if}
      </div>
    {/if}

  {:else}
    <!-- Install logs -->
    {#if installLoading}
      <div class="card px-4 py-10">
        <div class="flex items-center justify-center gap-2 text-text-muted">
          <Icon icon={loaderIcon} class="h-5 w-5 animate-spin" />
          <span class="text-[0.8125rem]">{t("status.loading")}</span>
        </div>
      </div>
    {:else if installError}
      {@render logError(() => fetchInstallLogs())}
    {:else if installLogs.length === 0}
      <div class="card flex flex-col items-center gap-2 px-4 py-10 text-center">
        <p class="text-[0.8125rem] text-text-muted">{t("logs.noInstallLogs")}</p>
      </div>
    {:else}
      <div class="flex flex-col gap-4 lg:flex-row">
        <!-- File list -->
        <div class="card w-full overflow-y-auto p-2 lg:max-h-[70vh] lg:w-72 lg:shrink-0">
          <p class="section-label px-2 pt-1">{t("logs.logFiles")}</p>
          {#each groupedInstallLogs as [category, files]}
            <button
              onclick={() => toggleCategory(category)}
              class="mt-1 flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-[0.625rem] font-semibold uppercase tracking-wider text-text-muted transition-colors hover:bg-surface-overlay first:mt-0"
            >
              <Icon
                icon={chevronDownIcon}
                class="h-3 w-3 shrink-0 transition-transform duration-200 {expandedCategories.has(category) ? '' : '-rotate-90'}"
              />
              <span class="h-1.5 w-1.5 rounded-full {categoryDotColor(category)}"></span>
              {categoryLabel(category)}
              <span class="ml-auto text-[0.625rem] font-normal tabular-nums opacity-60">{files.length}</span>
            </button>
            {#if expandedCategories.has(category)}
              <div class="animate-slide-down space-y-0.5 pb-1">
                {#each files as log, fi}
                  <button
                    onclick={() => handleInstallLogSelect(log.name)}
                    class="log-file-item flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-[0.8125rem] transition-colors
                      {selectedInstallLog === log.name
                        ? 'bg-accent/10 text-accent'
                        : 'text-text-secondary hover:bg-surface-overlay'}"
                    style="animation-delay: {fi * 30}ms"
                  >
                    <span class="truncate font-mono text-[0.75rem]">{log.name.split("/").pop()}</span>
                    <span class="ml-2 shrink-0 text-[0.625rem] text-text-muted">{formatSize(log.size)}</span>
                  </button>
                {/each}
              </div>
            {/if}
          {/each}
        </div>

        <!-- Content -->
        <div class="card flex-1 overflow-hidden">
          {#if installContentLoading}
            <div class="flex items-center justify-center gap-2 px-4 py-10 text-text-muted">
              <Icon icon={loaderIcon} class="h-5 w-5 animate-spin" />
              <span class="text-[0.8125rem]">{t("status.loading")}</span>
            </div>
          {:else if selectedInstallLog}
            {#key selectedInstallLog}
              <div class="log-tab-content">
                <div class="flex items-center gap-2 border-b border-border-subtle bg-surface-base/50 px-4 py-2">
                  <span class="h-2 w-2 rounded-full bg-status-ok"></span>
                  <span class="font-mono text-[0.6875rem] font-medium text-text-secondary">{selectedInstallLog.split("/").pop()}</span>
                </div>
                <div class="overflow-x-auto p-4">
                  <pre class="font-mono text-[0.75rem] leading-relaxed text-text-secondary whitespace-pre-wrap break-all">{installContent}</pre>
                </div>
              </div>
            {/key}
          {:else}
            <div class="flex items-center justify-center px-4 py-10">
              <p class="text-[0.8125rem] text-text-muted">{t("logs.selectFile")}</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {/if}
  </div>
  {/key}
</div>

<style>
  /* ── Virtual scroll table alignment ────────────────────────────────── */
  .log-table {
    table-layout: fixed;
  }

  /* ── Log row severity accents ────────────────────────────────────────── */
  .log-row {
    position: relative;
  }

  .log-row-error {
    background: rgba(240, 104, 104, 0.03);
    box-shadow: inset 2px 0 0 0 var(--color-status-critical);
  }

  .log-row-warn {
    box-shadow: inset 2px 0 0 0 rgba(240, 185, 58, 0.4);
  }

  .log-row-error:hover {
    background: rgba(240, 104, 104, 0.06);
  }

  /* ── Live streaming indicator ────────────────────────────────────────── */
  .log-live-dot {
    position: relative;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }

  .log-live-dot::after {
    content: "";
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    border: 1.5px solid currentColor;
    opacity: 0;
    animation: log-live-ring 2.5s ease-out infinite;
  }

  @keyframes log-live-ring {
    0% { transform: scale(0.6); opacity: 0.6; }
    100% { transform: scale(1.6); opacity: 0; }
  }

  /* ── Focused row (keyboard navigation) ─────────────────────────────── */
  .log-row-focused {
    background: rgba(77, 148, 255, 0.08) !important;
    box-shadow: inset 2px 0 0 0 var(--color-accent);
  }

  :global(.light) .log-row-focused {
    background: rgba(37, 99, 235, 0.06) !important;
  }

  /* ── Source color badges ──────────────────────────────────────────── */
  .log-source {
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    font-weight: 500;
    color: hsl(var(--src-hue, 210) 50% 68%);
  }

  :global(.light) .log-source {
    color: hsl(var(--src-hue, 210) 45% 42%);
  }

  /* ── Tab content transition ────────────────────────────────────────── */
  .log-tab-content {
    animation: log-fade-in 0.2s cubic-bezier(0.25, 1, 0.5, 1) both;
  }

  @keyframes log-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ── File list stagger ───────────────────────────────────────────── */
  .log-file-item {
    animation: log-fade-in 0.2s cubic-bezier(0.25, 1, 0.5, 1) both;
  }

  /* ── New entries badge ─────────────────────────────────────────────── */
  .log-new-badge {
    font-size: 0.625rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--color-accent);
    background: rgba(77, 148, 255, 0.1);
    border-radius: 6px;
    padding: 1px 6px;
    animation: log-badge-in 0.3s cubic-bezier(0.25, 1, 0.5, 1) both;
  }

  @keyframes log-badge-in {
    from { opacity: 0; transform: translateY(4px) scale(0.8); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  @media (prefers-reduced-motion: reduce) {
    .log-tab-content, .log-file-item, .log-new-badge { animation: none; opacity: 1; transform: none; }
    .log-live-dot::after { animation: none; opacity: 0.3; transform: scale(1); }
  }
</style>
