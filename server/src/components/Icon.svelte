<script lang="ts">
  interface Props {
    icon: string;
    class?: string;
    stroke?: number;
  }

  let { icon, class: className = "", stroke }: Props = $props();

  let processed = $derived.by(() => {
    let svg = icon;
    // Strip the default class attribute from tabler SVGs
    svg = svg.replace(/class="[^"]*"/, "");
    // Apply custom stroke if provided
    if (stroke != null) {
      svg = svg.replace(/stroke-width="\d+"/, `stroke-width="${stroke}"`);
    }
    return svg;
  });
</script>

<span class="inline-flex {className}" style="line-height: 0;">
  {@html processed}
</span>

<style>
  span :global(svg) {
    width: 100%;
    height: 100%;
  }
</style>
