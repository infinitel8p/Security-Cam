<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { initLocale, t } from "../i18n";
  import { initArchiveBadge, subscribe as subscribeBadge } from "../lib/archive-badge";
  import { initSystemAlerts, subscribe as subscribeAlert, type AlertLevel } from "../lib/system-alert";
  import { initUpdateBadge, subscribe as subscribeUpdate } from "../lib/update-badge";
  import ThemeToggle from "./ThemeToggle.svelte";
  import Icon from "./Icon.svelte";
  import layoutGridIcon from "../icons/layout-grid.svg?raw";
  import archiveIcon from "../icons/archive.svg?raw";
  import settingsIcon from "../icons/settings.svg?raw";
  import fileTextIcon from "../icons/file-text.svg?raw";
  import activityIcon from "../icons/activity.svg?raw";
  import brandGithubIcon from "../icons/brand-github-filled.svg?raw";
  import bookIcon from "../icons/book.svg?raw";

  let badgeCount = $state(0);
  let alertLevel: AlertLevel = $state("ok");
  let updateAvailable = $state(false);
  let unsubBadge: (() => void) | null = null;
  let unsubAlert: (() => void) | null = null;
  let unsubUpdate: (() => void) | null = null;

  // Baked in at build time via vite.define - no fetch, no flash
  const gitBranch = typeof __GIT_BRANCH__ !== "undefined" ? __GIT_BRANCH__ : "";
  const gitCommit = typeof __GIT_COMMIT__ !== "undefined" ? __GIT_COMMIT__ : "";

  onMount(() => {
    initLocale();
    initArchiveBadge();
    initSystemAlerts();
    initUpdateBadge();
    unsubBadge = subscribeBadge((count) => { badgeCount = count; });
    unsubAlert = subscribeAlert((state) => { alertLevel = state.overall; });
    unsubUpdate = subscribeUpdate((state) => { updateAvailable = state.available; });
  });

  onDestroy(() => {
    unsubBadge?.();
    unsubAlert?.();
    unsubUpdate?.();
  });

  const path = $derived(typeof window !== "undefined" ? window.location.pathname : "/");

  const links = [
    { href: "/", labelKey: "nav.dashboard" as const, icon: layoutGridIcon },
    { href: "/archive", labelKey: "nav.archive" as const, icon: archiveIcon },
    { href: "/settings", labelKey: "nav.settings" as const, icon: settingsIcon },
    { href: "/stats", labelKey: "nav.stats" as const, icon: activityIcon },
    { href: "/logs", labelKey: "nav.logs" as const, icon: fileTextIcon },
  ];

  function isActive(href: string): boolean {
    if (href === "/") return path === "/";
    return path.startsWith(href);
  }
</script>

<nav
  class="fixed left-0 top-0 z-40 hidden h-screen w-52 flex-col border-r border-border-subtle bg-surface-raised lg:flex">
  <!-- Logo -->
  <div class="flex items-start gap-3 px-5 py-5">
    <div class="flex h-8 w-8 items-center justify-center">
      <img src="icon.png" alt="Security Cam" width="32" height="32" loading="eager">
    </div>
    <div>
      <span class="text-[0.8125rem] font-bold tracking-tight text-text-primary">Security-Cam</span>
      <p class="text-[0.625rem] leading-none font-medium font-mono tracking-widest text-text-muted">
        v.2026.04.04.11
      </p>
      {#if gitBranch}
        <p class="mt-0.5 text-[0.5625rem] leading-none font-mono text-text-muted/60 truncate max-w-[7.5rem]" title="{gitBranch}{gitCommit ? ' @ ' + gitCommit : ''}">
          {gitBranch} {#if gitCommit}<span class="text-text-muted/40">@ {gitCommit}</span>{/if}
        </p>
      {/if}
    </div>
  </div>

  <!-- Links -->
  <div class="mt-2 flex flex-col gap-0.5 px-3">
    {#each links as { href, labelKey, icon }}
      {@const active = isActive(href)}
      <a
        {href}
        class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[0.8125rem] font-medium transition-all duration-200
          {active
            ? 'bg-accent-muted text-accent'
            : 'text-text-secondary hover:bg-surface-overlay hover:text-text-primary'}"
      >
        {#if active}
          <span class="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-accent"></span>
        {/if}
        <span class="relative">
          <Icon {icon} class="h-[18px] w-[18px] shrink-0" />
          {#if href === "/archive" && badgeCount > 0 && !active}
            <span class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-critical px-1 text-[0.5625rem] font-bold leading-none text-white">
              {badgeCount > 99 ? "99+" : badgeCount}
            </span>
          {/if}
          {#if href === "/" && alertLevel !== "ok" && !active}
            <span class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full {alertLevel === 'critical' ? 'bg-status-critical animate-pulse' : 'bg-status-warning'}"></span>
          {/if}
          {#if href === "/settings" && updateAvailable && !active}
            <span class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-accent"></span>
          {/if}
        </span>
        {t(labelKey)}
      </a>
    {/each}
  </div>

  <!-- Bottom section -->
  <div class="mt-auto border-t border-border-subtle px-3 py-3">
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-1">
        <a
          href="https://dev.infinitel8p.com/Security-Cam/docs/intro"
          target="_blank"
          rel="noopener noreferrer"
          class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary"
          title={t("nav.docs")}
          aria-label={t("nav.docs")}
        >
          <Icon icon={bookIcon} class="h-4 w-4" />
        </a>
        <a
          href="https://github.com/infinitel8p/Security-Cam"
          target="_blank"
          rel="noopener noreferrer"
          class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary"
          title="GitHub"
          aria-label="GitHub repository"
        >
          <Icon icon={brandGithubIcon} class="h-4 w-4" />
        </a>
      </div>
      <ThemeToggle />
    </div>
  </div>
</nav>
