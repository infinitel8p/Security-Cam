<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  interface Props {
    checked: boolean;
    disabled?: boolean;
    onToggle: () => void;
    size?: "sm" | "md";
    /** Accessible label describing what this toggle controls */
    label?: string;
    /** Accent color class for the ON state track (e.g. 'bg-accent', 'bg-cat-sensor') */
    accent?: string;
    /** Glow rgba for ON state (e.g. 'rgba(77,148,255,0.25)') */
    glow?: string;
  }

  let {
    checked,
    disabled = false,
    onToggle,
    size = "md",
    label,
    accent = "bg-accent",
    glow = "rgba(77,148,255,0.25)",
  }: Props = $props();

  // Dimensions
  const dims = $derived(
    size === "sm"
      ? { track: "h-[1.375rem] w-10", knob: 18, travel: 18, pad: 2 }
      : { track: "h-6 w-11", knob: 20, travel: 20, pad: 2 }
  );

  // Spring solver config
  const SPRING = { stiffness: 400, damping: 28, mass: 1.0 };
  const DT = 1 / 60;
  const REST_THRESHOLD = 0.5; // px - close enough to snap

  let knobX = $state(checked ? dims.travel : 0);
  let glowOpacity = $state(checked ? 1 : 0);
  let velocity = 0;
  let glowVelocity = 0;
  let animating = false;
  let rafId: number | null = null;
  let reducedMotion = false;

  onMount(() => {
    reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Sync initial position without animation
    knobX = checked ? dims.travel : 0;
    glowOpacity = checked ? 1 : 0;
  });

  let destroyed = false;
  onDestroy(() => {
    destroyed = true;
    if (rafId !== null) cancelAnimationFrame(rafId);
  });

  function springStep(
    current: number,
    target: number,
    vel: number,
    config: typeof SPRING
  ): { pos: number; vel: number } {
    const force = -config.stiffness * (current - target);
    const dampForce = -config.damping * vel;
    const accel = (force + dampForce) / config.mass;
    const newVel = vel + accel * DT;
    const newPos = current + newVel * DT;
    return { pos: newPos, vel: newVel };
  }

  function animate() {
    if (destroyed) return;
    const targetX = checked ? dims.travel : 0;
    const targetGlow = checked ? 1 : 0;

    const xStep = springStep(knobX, targetX, velocity, SPRING);
    const gStep = springStep(glowOpacity, targetGlow, glowVelocity, {
      stiffness: 300,
      damping: 26,
      mass: 1,
    });

    knobX = xStep.pos;
    velocity = xStep.vel;
    glowOpacity = Math.max(0, Math.min(1, gStep.pos));
    glowVelocity = gStep.vel;

    const xSettled =
      Math.abs(knobX - targetX) < REST_THRESHOLD &&
      Math.abs(velocity) < REST_THRESHOLD;
    const gSettled =
      Math.abs(glowOpacity - targetGlow) < 0.01 &&
      Math.abs(glowVelocity) < 0.1;

    if (xSettled && gSettled) {
      knobX = targetX;
      glowOpacity = targetGlow;
      velocity = 0;
      glowVelocity = 0;
      animating = false;
      rafId = null;
      return;
    }

    rafId = requestAnimationFrame(animate);
  }

  function startAnimation() {
    if (reducedMotion) {
      knobX = checked ? dims.travel : 0;
      glowOpacity = checked ? 1 : 0;
      velocity = 0;
      glowVelocity = 0;
      return;
    }
    if (!animating) {
      animating = true;
      rafId = requestAnimationFrame(animate);
    }
  }

  // React to checked changes
  $effect(() => {
    // Access checked to create dependency
    const _ = checked;
    startAnimation();
  });

  function handleClick() {
    if (disabled) return;
    onToggle();
  }
</script>

<button
  onclick={handleClick}
  {disabled}
  class="btn-press relative shrink-0 rounded-full overflow-hidden bg-surface-elevated {dims.track} {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
  style="box-shadow: {glowOpacity > 0.05 ? `0 0 ${8 + glowOpacity * 4}px ${glow}` : 'none'};"
  role="switch"
  aria-checked={checked}
  aria-label={label}
>
  <!-- Track color overlay (spring-animated opacity) -->
  <span
    class="absolute inset-0 rounded-full {accent} pointer-events-none"
    style="opacity: {glowOpacity};"
  ></span>

  <!-- Knob (spring-animated position) -->
  <span
    class="absolute rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,0.3),0_1px_1px_rgba(0,0,0,0.15)] pointer-events-none"
    style="
      top: {dims.pad}px;
      left: {dims.pad}px;
      width: {dims.knob}px;
      height: {dims.knob}px;
      transform: translateX({knobX}px);
      will-change: transform;
    "
  ></span>
</button>
