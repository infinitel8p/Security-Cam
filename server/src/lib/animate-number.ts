/**
 * Svelte 5 rune-compatible animated number.
 *
 * Usage:
 *   const anim = animatedNumber();
 *   anim.set(42);          // animates from current to 42
 *   anim.value;            // current interpolated value (reactive via $state)
 */

const DURATION = 800; // ms

function easeOutCubic(x: number): number {
  return 1 - Math.pow(1 - x, 3);
}

export function animatedNumber(initial = 0) {
  let current = $state(initial);
  let from = initial;
  let to = initial;
  let startTime = 0;
  let rafId: number | null = null;

  function tick(now: number) {
    const p = easeOutCubic(Math.min((now - startTime) / DURATION, 1));
    current = from + (to - from) * p;
    if (p < 1) {
      rafId = requestAnimationFrame(tick);
    } else {
      rafId = null;
    }
  }

  return {
    get value() { return current; },
    set(target: number) {
      if (rafId != null) cancelAnimationFrame(rafId);
      from = current;
      to = target;
      startTime = performance.now();
      rafId = requestAnimationFrame(tick);
    },
    destroy() {
      if (rafId != null) cancelAnimationFrame(rafId);
    },
  };
}
