/**
 * Animated number with rAF + easeOutCubic interpolation.
 *
 * Returns a plain object - the component reads .value and
 * calls .set() to trigger animation. The onUpdate callback
 * is called each frame so the component can re-render.
 */

const DURATION = 800; // ms

function easeOutCubic(x: number): number {
  return 1 - Math.pow(1 - x, 3);
}

export function animatedNumber(initial = 0, onUpdate?: () => void) {
  let current = initial;
  let from = initial;
  let to = initial;
  let startTime = 0;
  let rafId: number | null = null;

  function tick(now: number) {
    const p = easeOutCubic(Math.min((now - startTime) / DURATION, 1));
    current = from + (to - from) * p;
    onUpdate?.();
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
