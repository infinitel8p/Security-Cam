<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";
  import Icon from "./Icon.svelte";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";
  import sunIcon from "../icons/sun.svg?raw";
  import moonIcon from "../icons/moon.svg?raw";

  type ThemeMode = "system" | "light" | "dark";

  let mode: ThemeMode = $state("system");

  const order: ThemeMode[] = ["system", "light", "dark"];

  onMount(() => {
    initLocale();
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    mode = saved === "light" || saved === "dark" ? saved : "system";
  });

  function apply(m: ThemeMode) {
    const isLight =
      m === "light" ||
      (m === "system" && window.matchMedia("(prefers-color-scheme: light)").matches);
    document.documentElement.classList.toggle("light", isLight);
  }

  function cycle() {
    const next = order[(order.indexOf(mode) + 1) % order.length];
    mode = next;
    if (next === "system") {
      localStorage.removeItem("theme");
    } else {
      localStorage.setItem("theme", next);
    }
    apply(next);
  }
</script>

<button
  onclick={cycle}
  class="btn-press flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition-colors duration-150 hover:bg-surface-overlay hover:text-text-secondary"
  title="{mode === 'system' ? t('theme.system') : mode === 'light' ? t('theme.light') : t('theme.dark')}"
  aria-label="Cycle theme: system, light, dark"
>
  {#if mode === "system"}
    <Icon icon={deviceDesktopIcon} class="h-4 w-4" />
  {:else if mode === "light"}
    <Icon icon={sunIcon} class="h-4 w-4" />
  {:else}
    <Icon icon={moonIcon} class="h-4 w-4" />
  {/if}
</button>
