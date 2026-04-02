<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
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
  let searchQuery = $state("");
  let searchInput = $state("");
  let sourceFilter = $state("");
  let autoRefresh = $state(true);
  let refreshTimer: ReturnType<typeof setInterval> | null = null;
  let displayLimit = $state(200);

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
  let mtxSearchQuery = $state("");
  let mtxSearchInput = $state("");
  let mtxSourceFilter = $state("");
  let mtxDisplayLimit = $state(200);

  const REFRESH_INTERVAL = 5000;

  async function fetchMtxLogs() {
    try {
      const params = new URLSearchParams({ limit: "2000" });
      if (mtxLevelFilter) params.set("level", mtxLevelFilter);
      if (mtxSearchQuery) params.set("search", mtxSearchQuery);
      const res = await fetch(`${getBackendUrl()}/logs/mediamtx?${params}`);
      if (!res.ok) throw new Error();
      mtxLogs = await res.json();
      mtxError = false;
    } catch {
      mtxError = true;
    } finally {
      mtxLoading = false;
    }
  }

  async function fetchApiLogs() {
    try {
      const params = new URLSearchParams({ limit: "2000" });
      if (levelFilter) params.set("level", levelFilter);
      if (searchQuery) params.set("search", searchQuery);
      const res = await fetch(`${getBackendUrl()}/logs/api?${params}`);
      if (!res.ok) throw new Error();
      logs = await res.json();
      error = false;
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  async function fetchInstallLogs() {
    installLoading = true;
    installError = false;
    try {
      const res = await fetch(`${getBackendUrl()}/logs/install`);
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
      const res = await fetch(`${getBackendUrl()}/logs/script/${name}`);
      if (!res.ok) throw new Error();
      installContent = await res.text();
    } catch {
      installContent = "Failed to load log file.";
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

  function handleSearch() {
    searchQuery = searchInput;
    displayLimit = 200;
    loading = true;
    fetchApiLogs();
  }

  function clearSearch() {
    searchInput = "";
    searchQuery = "";
    displayLimit = 200;
    loading = true;
    fetchApiLogs();
  }

  function handleLevelChange(level: string) {
    levelFilter = level;
    displayLimit = 200;
    loading = true;
    fetchApiLogs();
  }

  function handleTabChange(tab: "api" | "mediamtx" | "install") {
    activeTab = tab;
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
          selectedInstallLog = null;
        }
      }
    } else {
      next.add(category);
    }
    expandedCategories = next;
  }

  let filteredLogs = $derived(sourceFilter ? logs.filter((l) => l.source === sourceFilter) : logs);
  let displayedLogs = $derived(filteredLogs.slice(0, displayLimit));
  let hasMore = $derived(filteredLogs.length > displayLimit);

  // Unique source categories from loaded logs
  let sourcesApi = $derived([...new Set(logs.map((l) => l.source))].sort());
  let sourcesMtx = $derived([...new Set(mtxLogs.map((l) => l.source))].sort());

  // Count by level for filter badges
  let levelCounts = $derived.by(() => {
    if (levelFilter || searchQuery || sourceFilter) return null;
    const counts: Record<string, number> = {};
    for (const l of logs) {
      counts[l.level] = (counts[l.level] || 0) + 1;
    }
    return counts;
  });

  onMount(() => {
    initLocale();
    fetchApiLogs();
    startAutoRefresh();
  });

  onDestroy(() => {
    stopAutoRefresh();
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

<div class="mt-6 animate-in space-y-5" style="--stagger: 1">
  <!-- Tab bar + controls -->
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <!-- Tabs -->
    <div class="flex gap-1 rounded-xl bg-surface-overlay p-1">
      <button
        onclick={() => handleTabChange("api")}
        class="rounded-lg px-4 py-2 text-[0.8125rem] font-medium transition-all duration-200
          {activeTab === 'api'
            ? 'bg-surface-raised text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'}"
      >
        {t("logs.apiLogs")}
      </button>
      <button
        onclick={() => handleTabChange("mediamtx")}
        class="rounded-lg px-4 py-2 text-[0.8125rem] font-medium transition-all duration-200
          {activeTab === 'mediamtx'
            ? 'bg-surface-raised text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'}"
      >
        {t("logs.mediamtxLogs")}
      </button>
      <button
        onclick={() => handleTabChange("install")}
        class="rounded-lg px-4 py-2 text-[0.8125rem] font-medium transition-all duration-200
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
        class="flex h-8 items-center gap-1.5 rounded-lg bg-surface-overlay px-3 text-[0.75rem] font-medium text-text-secondary transition-colors hover:bg-surface-raised hover:text-text-primary"
        title={t("btn.download")}
      >
        <Icon icon={downloadIcon} class="h-3.5 w-3.5" />
        {t("btn.download")}
      </button>
    </div>
  </div>

  {#if activeTab === "api"}
    <!-- API log filters -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
      <!-- Search -->
      <form
        onsubmit={(e) => { e.preventDefault(); handleSearch(); }}
        class="relative flex-1"
      >
        <Icon icon={searchIcon} class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          bind:value={searchInput}
          placeholder={t("logs.searchPlaceholder")}
          class="h-9 w-full rounded-lg border border-border-subtle bg-surface-overlay pl-9 pr-8 text-[0.8125rem] text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        />
        {#if searchInput}
          <button
            type="button"
            onclick={clearSearch}
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
          >
            <Icon icon={xIcon} class="h-3.5 w-3.5" />
          </button>
        {/if}
      </form>

      <!-- Category filter -->
      {#if sourcesApi.length > 1}
        <select
          value={sourceFilter}
          onchange={(e) => { sourceFilter = (e.target as HTMLSelectElement).value; displayLimit = 200; }}
          class="h-9 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 text-[0.75rem] font-medium text-text-secondary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        >
          <option value="">{t("logs.allCategories")}</option>
          {#each sourcesApi as src}
            <option value={src}>{src}</option>
          {/each}
        </select>
      {/if}

      <!-- Level filter -->
      <div class="flex gap-1">
        {#each [
          { value: "", label: t("logs.all") },
          { value: "ERROR", label: "Error" },
          { value: "WARNING", label: "Warn" },
          { value: "INFO", label: "Info" },
          { value: "DEBUG", label: "Debug" },
        ] as { value, label }}
          <button
            onclick={() => handleLevelChange(value)}
            class="rounded-lg px-2.5 py-1.5 text-[0.75rem] font-medium transition-all duration-200
              {levelFilter === value
                ? 'bg-accent/15 text-accent'
                : 'text-text-muted hover:bg-surface-overlay hover:text-text-secondary'}"
          >
            {label}
            {#if !levelFilter && !searchQuery && !sourceFilter && levelCounts && value && levelCounts[value]}
              <span class="ml-1 text-[0.625rem] opacity-60">{levelCounts[value]}</span>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- API log output -->
    {#if loading && logs.length === 0}
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
    {:else if error}
      <div class="card flex flex-col items-center gap-3 px-4 py-10 text-center">
        <Icon icon={alertIcon} class="h-8 w-8 text-text-muted" />
        <p class="text-[0.8125rem] text-text-muted">{t("logs.errorLoading")}</p>
        <button
          onclick={() => { loading = true; fetchApiLogs(); }}
          class="rounded-lg bg-accent/10 px-4 py-2 text-[0.8125rem] font-medium text-accent transition-colors hover:bg-accent/20"
        >
          {t("btn.retry")}
        </button>
      </div>
    {:else if logs.length === 0}
      <div class="card flex flex-col items-center gap-2 px-4 py-10 text-center">
        <p class="text-[0.8125rem] text-text-muted">{t("logs.empty")}</p>
      </div>
    {:else}
      <div class="card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[640px]">
            <thead>
              <tr class="border-b border-border-subtle text-left text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">
                <th class="px-4 py-2.5 w-40">{t("logs.timestamp")}</th>
                <th class="px-4 py-2.5 w-20">{t("logs.level")}</th>
                <th class="px-4 py-2.5 w-28">{t("logs.source")}</th>
                <th class="px-4 py-2.5">{t("logs.message")}</th>
              </tr>
            </thead>
            <tbody class="font-mono text-[0.75rem]">
              {#each displayedLogs as entry, i}
                <tr class="border-b border-border-subtle/50 transition-colors hover:bg-surface-overlay/50 {entry.level === 'ERROR' ? 'bg-status-critical/[0.03]' : ''}">
                  <td class="whitespace-nowrap px-4 py-1.5 text-text-muted">{entry.ts}</td>
                  <td class="px-4 py-1.5">
                    <span class="inline-flex rounded px-1.5 py-0.5 text-[0.625rem] font-semibold {levelColor(entry.level)} {levelBgColor(entry.level)}">
                      {entry.level}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-4 py-1.5 text-text-secondary">{entry.source}</td>
                  <td class="px-4 py-1.5 text-text-primary break-all">{entry.message}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        {#if hasMore}
          <div class="border-t border-border-subtle px-4 py-3 text-center">
            <button
              onclick={() => { displayLimit += 200; }}
              class="inline-flex items-center gap-1.5 text-[0.75rem] font-medium text-accent transition-colors hover:text-accent/80"
            >
              <Icon icon={chevronDownIcon} class="h-3.5 w-3.5" />
              {t("btn.showMore")} ({filteredLogs.length - displayLimit} {t("logs.remaining")})
            </button>
          </div>
        {/if}

        <div class="border-t border-border-subtle px-4 py-2 text-[0.6875rem] text-text-muted">
          {t("logs.showing", { n: String(displayedLogs.length), total: String(filteredLogs.length) })}
          {#if autoRefresh}
            <span class="ml-2 inline-flex items-center gap-1">
              <span class="h-1.5 w-1.5 rounded-full bg-status-ok animate-pulse"></span>
              {t("logs.live")}
            </span>
          {/if}
        </div>
      </div>
    {/if}

  {:else if activeTab === "mediamtx"}
    <!-- MediaMTX log filters -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
      <form
        onsubmit={(e) => { e.preventDefault(); mtxSearchQuery = mtxSearchInput; mtxDisplayLimit = 200; mtxLoading = true; fetchMtxLogs(); }}
        class="relative flex-1"
      >
        <Icon icon={searchIcon} class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          bind:value={mtxSearchInput}
          placeholder={t("logs.searchPlaceholder")}
          class="h-9 w-full rounded-lg border border-border-subtle bg-surface-overlay pl-9 pr-8 text-[0.8125rem] text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        />
        {#if mtxSearchInput}
          <button
            type="button"
            onclick={() => { mtxSearchInput = ""; mtxSearchQuery = ""; mtxDisplayLimit = 200; mtxLoading = true; fetchMtxLogs(); }}
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
          >
            <Icon icon={xIcon} class="h-3.5 w-3.5" />
          </button>
        {/if}
      </form>

      <!-- Category filter -->
      {#if sourcesMtx.length > 1}
        <select
          value={mtxSourceFilter}
          onchange={(e) => { mtxSourceFilter = (e.target as HTMLSelectElement).value; mtxDisplayLimit = 200; }}
          class="h-9 rounded-lg border border-border-subtle bg-surface-overlay px-2.5 text-[0.75rem] font-medium text-text-secondary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
        >
          <option value="">{t("logs.allCategories")}</option>
          {#each sourcesMtx as src}
            <option value={src}>{src}</option>
          {/each}
        </select>
      {/if}

      <div class="flex gap-1">
        {#each [
          { value: "", label: t("logs.all") },
          { value: "ERROR", label: "Error" },
          { value: "WARNING", label: "Warn" },
          { value: "INFO", label: "Info" },
          { value: "DEBUG", label: "Debug" },
        ] as { value, label }}
          <button
            onclick={() => { mtxLevelFilter = value; mtxDisplayLimit = 200; mtxLoading = true; fetchMtxLogs(); }}
            class="rounded-lg px-2.5 py-1.5 text-[0.75rem] font-medium transition-all duration-200
              {mtxLevelFilter === value
                ? 'bg-accent/15 text-accent'
                : 'text-text-muted hover:bg-surface-overlay hover:text-text-secondary'}"
          >
            {label}
          </button>
        {/each}
      </div>
    </div>

    <!-- MediaMTX log output -->
    {#if mtxLoading && mtxLogs.length === 0}
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
    {:else if mtxError}
      <div class="card flex flex-col items-center gap-3 px-4 py-10 text-center">
        <Icon icon={alertIcon} class="h-8 w-8 text-text-muted" />
        <p class="text-[0.8125rem] text-text-muted">{t("logs.errorLoading")}</p>
        <button
          onclick={() => { mtxLoading = true; fetchMtxLogs(); }}
          class="rounded-lg bg-accent/10 px-4 py-2 text-[0.8125rem] font-medium text-accent transition-colors hover:bg-accent/20"
        >
          {t("btn.retry")}
        </button>
      </div>
    {:else if mtxLogs.length === 0}
      <div class="card flex flex-col items-center gap-2 px-4 py-10 text-center">
        <p class="text-[0.8125rem] text-text-muted">{t("logs.empty")}</p>
      </div>
    {:else}
      {@const mtxFiltered = mtxSourceFilter ? mtxLogs.filter((l) => l.source === mtxSourceFilter) : mtxLogs}
      {@const displayed = mtxFiltered.slice(0, mtxDisplayLimit)}
      {@const hasMoreMtx = mtxFiltered.length > mtxDisplayLimit}
      <div class="card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[640px]">
            <thead>
              <tr class="border-b border-border-subtle text-left text-[0.6875rem] font-medium uppercase tracking-wider text-text-muted">
                <th class="px-4 py-2.5 w-40">{t("logs.timestamp")}</th>
                <th class="px-4 py-2.5 w-20">{t("logs.level")}</th>
                <th class="px-4 py-2.5 w-28">{t("logs.source")}</th>
                <th class="px-4 py-2.5">{t("logs.message")}</th>
              </tr>
            </thead>
            <tbody class="font-mono text-[0.75rem]">
              {#each displayed as entry}
                <tr class="border-b border-border-subtle/50 transition-colors hover:bg-surface-overlay/50 {entry.level === 'ERROR' ? 'bg-status-critical/[0.03]' : ''}">
                  <td class="whitespace-nowrap px-4 py-1.5 text-text-muted">{entry.ts}</td>
                  <td class="px-4 py-1.5">
                    <span class="inline-flex rounded px-1.5 py-0.5 text-[0.625rem] font-semibold {levelColor(entry.level)} {levelBgColor(entry.level)}">
                      {entry.level}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-4 py-1.5 text-text-secondary">{entry.source}</td>
                  <td class="px-4 py-1.5 text-text-primary break-all">{entry.message}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        {#if hasMoreMtx}
          <div class="border-t border-border-subtle px-4 py-3 text-center">
            <button
              onclick={() => { mtxDisplayLimit += 200; }}
              class="inline-flex items-center gap-1.5 text-[0.75rem] font-medium text-accent transition-colors hover:text-accent/80"
            >
              <Icon icon={chevronDownIcon} class="h-3.5 w-3.5" />
              {t("btn.showMore")} ({mtxFiltered.length - mtxDisplayLimit} {t("logs.remaining")})
            </button>
          </div>
        {/if}

        <div class="border-t border-border-subtle px-4 py-2 text-[0.6875rem] text-text-muted">
          {t("logs.showing", { n: String(displayed.length), total: String(mtxFiltered.length) })}
          {#if autoRefresh}
            <span class="ml-2 inline-flex items-center gap-1">
              <span class="h-1.5 w-1.5 rounded-full bg-status-ok animate-pulse"></span>
              {t("logs.live")}
            </span>
          {/if}
        </div>
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
      <div class="card flex flex-col items-center gap-3 px-4 py-10 text-center">
        <Icon icon={alertIcon} class="h-8 w-8 text-text-muted" />
        <p class="text-[0.8125rem] text-text-muted">{t("logs.errorLoading")}</p>
        <button
          onclick={() => fetchInstallLogs()}
          class="rounded-lg bg-accent/10 px-4 py-2 text-[0.8125rem] font-medium text-accent transition-colors hover:bg-accent/20"
        >
          {t("btn.retry")}
        </button>
      </div>
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
              {categoryLabel(category)}
              <span class="ml-auto text-[0.625rem] font-normal tabular-nums opacity-60">{files.length}</span>
            </button>
            {#if expandedCategories.has(category)}
              <div class="space-y-0.5 pb-1">
                {#each files as log}
                  <button
                    onclick={() => handleInstallLogSelect(log.name)}
                    class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-[0.8125rem] transition-colors
                      {selectedInstallLog === log.name
                        ? 'bg-accent/10 text-accent'
                        : 'text-text-secondary hover:bg-surface-overlay'}"
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
            <div class="overflow-x-auto p-4">
              <pre class="font-mono text-[0.75rem] leading-relaxed text-text-secondary whitespace-pre-wrap break-all">{installContent}</pre>
            </div>
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
