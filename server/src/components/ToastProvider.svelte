<script lang="ts">
  import { Toaster, type DefaultToastOptions } from "svelte-5-french-toast";

  const toastOptions: DefaultToastOptions = {
    style: "background: var(--color-surface-elevated); color: var(--color-text-primary); border: 1px solid var(--color-border-default); font-size: 0.8125rem; border-radius: 0.75rem; box-shadow: var(--shadow-md);",
    success: {
      iconTheme: { primary: "var(--color-status-ok)", secondary: "var(--color-surface-elevated)" },
    },
    error: {
      iconTheme: { primary: "var(--color-status-critical)", secondary: "var(--color-surface-elevated)" },
    },
  };
</script>

<Toaster position="bottom-right" {toastOptions} />
