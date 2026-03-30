<script lang="ts">
  import { onMount } from "svelte";
  import { initLocale, t } from "../i18n";

  interface Props {
    key: string;
    fallback: string;
  }

  let { key, fallback }: Props = $props();
  let text = $state(fallback);

  onMount(() => {
    initLocale();
    text = t(key);
  });
</script>{text}