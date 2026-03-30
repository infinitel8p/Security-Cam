<script lang="ts">
  import ThemeToggle from "./ThemeToggle.svelte";

  const path = $derived(typeof window !== "undefined" ? window.location.pathname : "/");

  function isActive(href: string): boolean {
    if (href === "/") return path === "/";
    return path.startsWith(href);
  }
</script>

<!-- Bottom tab bar — visible only below lg -->
<nav
  class="fixed bottom-0 left-0 right-0 z-40 flex items-stretch border-t border-border-subtle bg-surface-glass backdrop-blur-xl landscape:hidden lg:hidden"
  style="padding-bottom: env(safe-area-inset-bottom, 0px);"
>
  <a
    href="/"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors
      {isActive('/') ? 'text-accent' : 'text-text-muted'}"
  >
    {#if isActive("/")}
      <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent"></span>
    {/if}
    <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
    <span class="text-[0.6875rem] leading-none font-medium">Dashboard</span>
  </a>

  <a
    href="/archive"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors
      {isActive('/archive') ? 'text-accent' : 'text-text-muted'}"
  >
    {#if isActive("/archive")}
      <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent"></span>
    {/if}
    <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
    <span class="text-[0.6875rem] leading-none font-medium">Archive</span>
  </a>

  <a
    href="/settings"
    class="group relative flex min-h-[3rem] flex-1 flex-col items-center justify-center gap-1 py-2.5 transition-colors
      {isActive('/settings') ? 'text-accent' : 'text-text-muted'}"
  >
    {#if isActive("/settings")}
      <span class="absolute top-0 left-1/2 h-[2px] w-8 -translate-x-1/2 rounded-b-full bg-accent"></span>
    {/if}
    <svg class="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
    <span class="text-[0.6875rem] leading-none font-medium">Settings</span>
  </a>
</nav>
