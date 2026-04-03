<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  interface Props {
    /** Data points (oldest first), 0-max range */
    data: number[];
    /** Maximum value for Y-axis scaling */
    max: number;
    /** Stroke color as CSS color string */
    color: string;
    /** Fill gradient top opacity (0-1) */
    fillOpacity?: number;
  }

  let { data, max, color, fillOpacity = 0.12 }: Props = $props();

  let canvas: HTMLCanvasElement | undefined = $state();
  let ctx: CanvasRenderingContext2D | null = null;
  let rafId: number | null = null;
  let usingTimeout = false; // true when using setTimeout instead of rAF
  let reducedMotion = false;
  let dpr = 1;

  // Display points with smooth interpolation toward target
  let displayPoints: number[] = [];
  const LERP_SPEED = 0.12; // per-frame interpolation factor
  const SETTLE_THRESHOLD = 0.1; // stop animating when all points within this of target
  let settled = false;

  // Glow pulse on the leading edge (latest data point)
  let headGlow = 0;
  let headGlowDir = 1;

  // Track last data reference to detect new data arriving
  let lastDataRef: number[] | null = null;

  const H = 32; // CSS px height
  const PAD_Y = 2;

  function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }

  function draw() {
    if (!ctx || !canvas) return;
    const W = canvas.clientWidth;
    if (W === 0) return;

    // Resize backing store if needed (e.g. container resized)
    const needW = Math.round(W * dpr);
    const needH = Math.round(H * dpr);
    if (canvas.width !== needW || canvas.height !== needH) {
      canvas.width = needW;
      canvas.height = needH;
      ctx.scale(dpr, dpr);
    }

    const safeMax = max > 0 ? max : 1;
    const points = data;
    const n = points.length;

    // Detect new data arriving
    if (data !== lastDataRef) {
      lastDataRef = data;
      settled = false;
    }

    // Interpolate display points toward target data
    if (displayPoints.length !== n) {
      displayPoints = points.slice();
      settled = false;
    } else if (!reducedMotion && !settled) {
      let maxDelta = 0;
      for (let i = 0; i < n; i++) {
        displayPoints[i] = lerp(displayPoints[i], points[i], LERP_SPEED);
        maxDelta = Math.max(maxDelta, Math.abs(displayPoints[i] - points[i]));
      }
      if (maxDelta < SETTLE_THRESHOLD) {
        // Snap to final values and stop animating
        for (let i = 0; i < n; i++) displayPoints[i] = points[i];
        settled = true;
      }
    } else if (reducedMotion) {
      for (let i = 0; i < n; i++) displayPoints[i] = points[i];
      settled = true;
    }

    ctx.clearRect(0, 0, W, H);

    if (n < 2) {
      rafId = requestAnimationFrame(draw);
      return;
    }

    const drawH = H - PAD_Y * 2;
    const step = W / (n - 1);

    // Build path once, reuse for fill + stroke
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = i * step;
      const v = Math.min(displayPoints[i], safeMax);
      const y = PAD_Y + drawH - (v / safeMax) * drawH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    // Fill: gradient under the line
    const fillPath = new Path2D();
    for (let i = 0; i < n; i++) {
      const x = i * step;
      const v = Math.min(displayPoints[i], safeMax);
      const y = PAD_Y + drawH - (v / safeMax) * drawH;
      if (i === 0) fillPath.moveTo(x, y);
      else fillPath.lineTo(x, y);
    }
    fillPath.lineTo((n - 1) * step, H);
    fillPath.lineTo(0, H);
    fillPath.closePath();

    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, withAlpha(color, fillOpacity));
    grad.addColorStop(1, withAlpha(color, 0));
    ctx.fillStyle = grad;
    ctx.fill(fillPath);

    // Stroke: the line itself
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.stroke();

    // Head glow: pulsing dot at the latest point
    if (!reducedMotion && n > 0) {
      headGlow += headGlowDir * 0.02;
      if (headGlow > 1) { headGlow = 1; headGlowDir = -1; }
      if (headGlow < 0.3) { headGlow = 0.3; headGlowDir = 1; }

      const lastX = (n - 1) * step;
      const lastV = Math.min(displayPoints[n - 1], safeMax);
      const lastY = PAD_Y + drawH - (lastV / safeMax) * drawH;

      // Outer glow
      const glowR = 4 + headGlow * 2;
      const glowGrad = ctx.createRadialGradient(lastX, lastY, 0, lastX, lastY, glowR);
      glowGrad.addColorStop(0, withAlpha(color, 0.4 * headGlow));
      glowGrad.addColorStop(1, withAlpha(color, 0));
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(lastX, lastY, glowR, 0, Math.PI * 2);
      ctx.fill();

      // Core dot
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 1.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // When data is still interpolating, run at full 60fps.
    // Once settled, slow to ~15fps for the head glow pulse (saves CPU on Pi).
    // In reduced motion mode, stop entirely when settled.
    if (!settled) {
      usingTimeout = false;
      rafId = requestAnimationFrame(draw);
    } else if (!reducedMotion) {
      usingTimeout = true;
      rafId = window.setTimeout(draw, 66); // ~15fps for glow
    } else {
      rafId = null;
    }
  }

  /** Kick the RAF loop back to full speed when props change */
  function wake() {
    if (!ctx) return;
    settled = false;
    if (usingTimeout && rafId !== null) {
      // Switch from slow timeout back to full-speed rAF
      clearTimeout(rafId);
      rafId = requestAnimationFrame(draw);
      usingTimeout = false;
    } else if (rafId === null) {
      rafId = requestAnimationFrame(draw);
    }
  }

  // Watch for data/color changes and restart animation
  $effect(() => {
    // Touch reactive props to create dependency
    data; color; max;
    wake();
  });

  /** Convert a CSS color to the same color with a given alpha */
  function withAlpha(cssColor: string, alpha: number): string {
    if (alpha <= 0) return "transparent";
    // Handle hex colors
    if (cssColor.startsWith("#")) {
      const r = parseInt(cssColor.slice(1, 3), 16);
      const g = parseInt(cssColor.slice(3, 5), 16);
      const b = parseInt(cssColor.slice(5, 7), 16);
      return `rgba(${r},${g},${b},${alpha})`;
    }
    // Handle rgb/rgba
    const match = cssColor.match(/[\d.]+/g);
    if (match && match.length >= 3) {
      return `rgba(${match[0]},${match[1]},${match[2]},${alpha})`;
    }
    return cssColor;
  }

  onMount(() => {
    reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    dpr = Math.min(window.devicePixelRatio || 1, 2); // cap at 2x for Pi perf

    if (canvas) {
      canvas.width = Math.round(canvas.clientWidth * dpr);
      canvas.height = Math.round(H * dpr);
      ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.scale(dpr, dpr);
        draw();
      }
    }
  });

  function cancelLoop() {
    if (rafId !== null) {
      if (usingTimeout) clearTimeout(rafId);
      else cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  onDestroy(cancelLoop);
</script>

<canvas
  bind:this={canvas}
  class="mt-3 h-8 w-full"
  style="height: {H}px;"
  aria-hidden="true"
></canvas>
