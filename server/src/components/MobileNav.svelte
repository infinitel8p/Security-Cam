<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { initLocale, t } from "../i18n";
  import { initArchiveBadge, subscribe as subscribeBadge } from "../lib/archive-badge";
  import { initSystemAlerts, subscribe as subscribeAlert, type AlertLevel } from "../lib/system-alert";
  import ThemeToggle from "./ThemeToggle.svelte";
  import Icon from "./Icon.svelte";
  import layoutGridIcon from "../icons/layout-grid.svg?raw";
  import archiveIcon from "../icons/archive.svg?raw";
  import settingsIcon from "../icons/settings.svg?raw";
  import fileTextIcon from "../icons/file-text.svg?raw";
  import activityIcon from "../icons/activity.svg?raw";

  let badgeCount = $state(0);
  let alertLevel: AlertLevel = $state("ok");
  let unsubBadge: (() => void) | null = null;
  let unsubAlert: (() => void) | null = null;

  onMount(() => {
    initLocale();
    initArchiveBadge();
    initSystemAlerts();
    unsubBadge = subscribeBadge((count) => { badgeCount = count; });
    unsubAlert = subscribeAlert((state) => { alertLevel = state.overall; });
  });

  onDestroy(() => {
    unsubBadge?.();
    unsubAlert?.();
  });

  const path = $derived(typeof window !== "undefined" ? window.location.pathname : "/");

  function isActive(href: string): boolean {
    if (href === "/") return path === "/";
    return path.startsWith(href);
  }
</script>

<!-- Bottom tab bar - visible only below lg -->
<nav
  class="fixed bottom-0 left-0 right-0 z-40 flex items-stretch border-t border-border-subtle bg-surface-glass backdrop-blur-xl landscape:hidden lg:hidden"
  style="padding-bottom: env(safe-area-inset-bottom, 0px);"
>
  <a
    href="/"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <span class="relative">
      <Icon icon={layoutGridIcon} class="h-5 w-5 shrink-0" />
      {#if alertLevel !== "ok" && !isActive('/')}
        <span class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full {alertLevel === 'critical' ? 'bg-status-critical animate-pulse' : 'bg-status-warning'}"></span>
      {/if}
    </span>
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.dashboard")}</span>
  </a>

  <a
    href="/archive"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/archive') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/archive') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <span class="relative">
      <Icon icon={archiveIcon} class="h-5 w-5 shrink-0" />
      {#if badgeCount > 0 && !isActive('/archive')}
        <span class="absolute -right-1.5 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-critical px-1 text-[0.5625rem] font-bold leading-none text-white">
          {badgeCount > 99 ? "99+" : badgeCount}
        </span>
      {/if}
    </span>
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.archive")}</span>
  </a>

  <a
    href="/settings"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/settings') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/settings') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <Icon icon={settingsIcon} class="h-5 w-5 shrink-0" />
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.settings")}</span>
  </a>

  <a
    href="/stats"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/stats') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/stats') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <Icon icon={activityIcon} class="h-5 w-5 shrink-0" />
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.stats")}</span>
  </a>

  <a
    href="/logs"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/logs') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/logs') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <Icon icon={fileTextIcon} class="h-5 w-5 shrink-0" />
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.logs")}</span>
  </a>
</nav>
