/**
 * Animated number with rAF + easeOutCubic interpolation.
 *
 * Duration scales with the magnitude of change:
 *   - tiny change (< 3):   snap instantly, no animation
 *   - small change (< 10): 200ms quick slide
 *   - medium change:        400ms
 *   - large change (> 30):  800ms full count-up
 *
 * easeOutCubic makes numbers roll fast at the start and
 * settle slowly at the end for a satisfying deceleration.
 */

const MIN_DURATION = 200;
const MAX_DURATION = 800;

function easeOutCubic(x: number): number {
  return 1 - Math.pow(1 - x, 3);
}

function getDuration(delta: number): number {
  const abs = Math.abs(delta);
  if (abs < 3) return 0; // snap - not worth animating
  if (abs < 10) return MIN_DURATION;
  if (abs < 30) return 400;
  return MAX_DURATION;
}

export function animatedNumber(initial = 0, onUpdate?: () => void) {
  let current = initial;
  let from = initial;
  let to = initial;
  let duration = 0;
  let startTime = 0;
  let rafId: number | null = null;

  function tick(now: number) {
    const p = easeOutCubic(Math.min((now - startTime) / duration, 1));
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
      duration = getDuration(target - from);
      if (duration === 0) {
        current = target;
        // Schedule via rAF to avoid synchronous $state mutation inside
        // Svelte $effect (which causes effect_update_depth_exceeded when
        // multiple animated numbers snap in the same reactive flush).
        if (onUpdate) rafId = requestAnimationFrame(() => { rafId = null; onUpdate(); });
        return;
      }
      startTime = performance.now();
      rafId = requestAnimationFrame(tick);
    },
    destroy() {
      if (rafId != null) cancelAnimationFrame(rafId);
    },
  };
}
