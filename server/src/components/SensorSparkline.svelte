<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  interface Props {
    /** Array of boolean readings (oldest first) */
    history: boolean[];
    /** Current live value */
    value: boolean | null;
    /** Max readings to display */
    maxPoints?: number;
  }

  let { history, value, maxPoints = 40 }: Props = $props();

  let canvas: HTMLCanvasElement | undefined = $state();
  let ctx: CanvasRenderingContext2D | null = null;
  let rafId: number | null = null;
  let reducedMotion = false;
  let dpr = 1;

  // Smooth interpolated positions for drawing
  let smoothPoints: number[] = [];
  let headGlow = 0;
  let headGlowDir = 1;
  let prevValue: boolean | null = null;
  let pulseIntensity = 0;

  // Canvas dimensions (CSS pixels)
  const W = 280;
  const H = 48;
  const PAD_X = 4;
  const PAD_Y = 8;
  const LINE_Y_HIGH = PAD_Y;
  const LINE_Y_LOW = H - PAD_Y;

  // Colors
  const COLOR_HIGH = "#4ade80"; // green for HIGH state
  const COLOR_LOW = "rgba(74, 83, 112, 0.4)";
  const COLOR_GLOW = "rgba(74, 222, 128, 0.6)";
  const COLOR_HEAD_CORE = "#4ade80";
  const COLOR_GRID = "rgba(74, 83, 112, 0.08)";

  function boolToY(val: boolean): number {
    return val ? LINE_Y_HIGH : LINE_Y_LOW;
  }

  function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }

  onMount(() => {
    reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    dpr = window.devicePixelRatio || 1;

    if (canvas) {
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx = canvas.getContext("2d");
      if (ctx) ctx.scale(dpr, dpr);
    }

    // Initialize smooth points from history
    syncSmooth();

    if (!reducedMotion) {
      tick();
    } else {
      drawStatic();
    }
  });

  let destroyed = false;
  onDestroy(() => {
    destroyed = true;
    if (rafId !== null) cancelAnimationFrame(rafId);
  });

  function syncSmooth() {
    const pts = history.slice(-maxPoints);
    // Expand to maxPoints, filling with LOW if not enough data
    while (pts.length < maxPoints) pts.unshift(false);

    const targetYs = pts.map(boolToY);

    if (smoothPoints.length !== maxPoints) {
      smoothPoints = [...targetYs];
    } else {
      // Smooth interpolation toward targets
      for (let i = 0; i < maxPoints; i++) {
        smoothPoints[i] = lerp(smoothPoints[i], targetYs[i], 0.25);
      }
    }
  }

  // Detect state changes for pulse
  $effect(() => {
    if (value !== prevValue && prevValue !== null) {
      pulseIntensity = 1;
    }
    prevValue = value;
  });

  function tick() {
    if (destroyed) return;
    syncSmooth();

    // Head glow breathing
    headGlow += headGlowDir * 0.03;
    if (headGlow > 1) { headGlow = 1; headGlowDir = -1; }
    if (headGlow < 0.3) { headGlow = 0.3; headGlowDir = 1; }

    // Pulse decay
    if (pulseIntensity > 0) pulseIntensity *= 0.92;
    if (pulseIntensity < 0.01) pulseIntensity = 0;

    draw();
    rafId = requestAnimationFrame(tick);
  }

  function drawStatic() {
    syncSmooth();
    // Force instant snap for reduced motion
    const pts = history.slice(-maxPoints);
    while (pts.length < maxPoints) pts.unshift(false);
    smoothPoints = pts.map(boolToY);
    headGlow = 0.6;
    draw();
  }

  function draw() {
    if (!ctx) return;
    const c = ctx;

    c.clearRect(0, 0, W, H);

    // Subtle grid lines
    c.strokeStyle = COLOR_GRID;
    c.lineWidth = 1;
    c.setLineDash([2, 4]);
    c.beginPath();
    c.moveTo(PAD_X, LINE_Y_HIGH);
    c.lineTo(W - PAD_X, LINE_Y_HIGH);
    c.moveTo(PAD_X, LINE_Y_LOW);
    c.lineTo(W - PAD_X, LINE_Y_LOW);
    c.stroke();
    c.setLineDash([]);

    if (smoothPoints.length < 2) return;

    const stepX = (W - PAD_X * 2) / (maxPoints - 1);

    // Draw the line with gradient
    c.beginPath();
    for (let i = 0; i < smoothPoints.length; i++) {
      const x = PAD_X + i * stepX;
      const y = smoothPoints[i];
      if (i === 0) {
        c.moveTo(x, y);
      } else {
        // Step function with slight rounding
        const prevX = PAD_X + (i - 1) * stepX;
        const prevY = smoothPoints[i - 1];
        const midX = (prevX + x) / 2;

        // Sharp step: horizontal then vertical
        c.lineTo(midX, prevY);
        c.lineTo(midX, y);
        c.lineTo(x, y);
      }
    }

    // Create gradient from dim left to bright right
    const grad = c.createLinearGradient(PAD_X, 0, W - PAD_X, 0);
    grad.addColorStop(0, "rgba(74, 222, 128, 0.08)");
    grad.addColorStop(0.5, "rgba(74, 222, 128, 0.25)");
    grad.addColorStop(1, COLOR_HIGH);

    c.strokeStyle = grad;
    c.lineWidth = 2;
    c.lineCap = "round";
    c.lineJoin = "round";
    c.stroke();

    // Fill area under line (subtle)
    const lastIdx = smoothPoints.length - 1;
    const lastX = PAD_X + lastIdx * stepX;
    c.lineTo(lastX, LINE_Y_LOW);
    c.lineTo(PAD_X, LINE_Y_LOW);
    c.closePath();

    const fillGrad = c.createLinearGradient(0, LINE_Y_HIGH, 0, LINE_Y_LOW);
    fillGrad.addColorStop(0, "rgba(74, 222, 128, 0.06)");
    fillGrad.addColorStop(1, "rgba(74, 222, 128, 0)");
    c.fillStyle = fillGrad;
    c.fill();

    // Head glow (last point)
    const headX = lastX;
    const headY = smoothPoints[lastIdx];
    const isHigh = headY < (LINE_Y_HIGH + LINE_Y_LOW) / 2;

    // Pulse ring on state change
    if (pulseIntensity > 0.01) {
      const pulseR = 6 + pulseIntensity * 14;
      const pulseAlpha = pulseIntensity * 0.4;
      c.beginPath();
      c.arc(headX, headY, pulseR, 0, Math.PI * 2);
      c.strokeStyle = `rgba(74, 222, 128, ${pulseAlpha})`;
      c.lineWidth = 1.5;
      c.stroke();
    }

    // Glow halo
    if (isHigh) {
      const glowR = 8 + headGlow * 4;
      const glowGrad = c.createRadialGradient(headX, headY, 0, headX, headY, glowR);
      glowGrad.addColorStop(0, `rgba(74, 222, 128, ${0.3 * headGlow})`);
      glowGrad.addColorStop(1, "rgba(74, 222, 128, 0)");
      c.beginPath();
      c.arc(headX, headY, glowR, 0, Math.PI * 2);
      c.fillStyle = glowGrad;
      c.fill();
    }

    // Head dot
    c.beginPath();
    c.arc(headX, headY, 3.5, 0, Math.PI * 2);
    c.fillStyle = isHigh ? COLOR_HEAD_CORE : COLOR_LOW;
    c.fill();

    // Inner bright core
    if (isHigh) {
      c.beginPath();
      c.arc(headX, headY, 1.5, 0, Math.PI * 2);
      c.fillStyle = "#fff";
      c.fill();
    }
  }

  // Redraw on history changes in reduced-motion mode
  $effect(() => {
    const _ = history.length;
    if (reducedMotion && ctx) drawStatic();
  });
</script>

<canvas
  bind:this={canvas}
  class="w-full rounded-md"
  style="height: {H}px; max-width: {W}px;"
  role="img"
  aria-label="Sensor reading history: {value ? 'HIGH' : 'LOW'}, {history.filter(Boolean).length} of {history.length} readings active"
></canvas>
