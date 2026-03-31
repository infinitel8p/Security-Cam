<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";
  import ThemeToggle from "./ThemeToggle.svelte";
  import Icon from "./Icon.svelte";
  import layoutGridIcon from "../icons/layout-grid.svg?raw";
  import archiveIcon from "../icons/archive.svg?raw";
  import settingsIcon from "../icons/settings.svg?raw";
  import brandGithubIcon from "../icons/brand-github-filled.svg?raw";
  import bookIcon from "../icons/book.svg?raw";

  onMount(() => {
    initLocale();
  });

  const path = $derived(typeof window !== "undefined" ? window.location.pathname : "/");

  const links = [
    { href: "/", labelKey: "nav.2026.04.01.8
    { href: "/archive", labelKey: "nav.2026.04.01.8
    { href: "/settings", labelKey: "nav.2026.04.01.8
  ];

  function isActive(href: string): boolean {
    if (href === "/") return path === "/";
    return path.startsWith(href);
  }
</script>

<nav
  class="fixed left-0 top-0 z-40 hidden h-screen w-52 flex-col border-r border-border-subtle bg-surface-raised lg:flex">
  <!-- Logo -->
  <div class="flex items-center gap-3 px-5 py-5">
    <div class="flex h-8 w-8 items-center justify-center">
      <img src="icon.png" alt="Security Cam" width="32" height="32" loading="eager">
    </div>
    <div>
      <span class="text-[0.8125rem] font-bold tracking-tight text-text-primary">Security-Cam</span>
      <p class="text-[0.625rem] leading-none font-medium uppercase tracking-widest text-text-muted">
        v.2026.04.01.8
      </p>
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
        <Icon {icon} class="h-[18px] w-[18px] shrink-0" />
        {t(labelKey)}
      </a>
    {/each}
  </div>

  <!-- Bottom section -->
  <div class="mt-auto border-t border-border-subtle px-3 py-3">
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-1">
        <a
          href="https://dev.2026.04.01.8
          target="_blank"
          rel="noopener noreferrer"
          class="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary"
          title={t("nav.2026.04.01.8
          aria-label={t("nav.2026.04.01.8
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
