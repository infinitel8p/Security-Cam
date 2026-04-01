<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";

  let greeting = $state("");

  function getGreeting(): string {
    const h = new Date().getHours();
    if (h < 5) return t("greeting.night");
    if (h < 12) return t("greeting.morning");
    if (h < 17) return t("greeting.afternoon");
    if (h < 21) return t("greeting.evening");
    return t("greeting.night");
  }

  onMount(() => {
    initLocale();
    greeting = getGreeting();
  });
</script>

<span>{greeting || t("page.dashboard")}</span>
