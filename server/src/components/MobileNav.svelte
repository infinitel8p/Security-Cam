<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";
  import ThemeToggle from "./ThemeToggle.svelte";
  import Icon from "./Icon.svelte";
  import layoutGridIcon from "../icons/layout-grid.svg?raw";
  import archiveIcon from "../icons/archive.svg?raw";
  import settingsIcon from "../icons/settings.svg?raw";

  onMount(() => {
    initLocale();
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
    <Icon icon={layoutGridIcon} class="h-5 w-5 shrink-0" />
    <span class="text-[0.6875rem] leading-none font-medium">{t("nav.dashboard")}</span>
  </a>

  <a
    href="/archive"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-200
      {isActive('/archive') ? 'text-accent' : 'text-text-muted'}"
  >
    <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent transition-all duration-200 {isActive('/archive') ? 'opacity-100 scale-x-100' : 'opacity-0 scale-x-0'}"></span>
    <Icon icon={archiveIcon} class="h-5 w-5 shrink-0" />
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
</nav>
