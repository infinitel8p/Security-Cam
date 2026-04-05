<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import type { Snippet } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { getToken, setToken } from "../lib/auth";
  import { initLocale, t } from "../i18n";

  let { children }: { children: Snippet } = $props();

  let state: "checking" | "login" | "authenticated" = $state("checking");
  let passwordInput = $state("");
  let error = $state("");
  let submitting = $state(false);
  let shakeKey = $state(0);

  // Particle canvas
  let canvasEl: HTMLCanvasElement | undefined = $state();
  let animFrame = 0;

  onMount(async () => {
    initLocale();
    try {
      const token = getToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${getBackendUrl()}/auth/status`, { headers });
      if (!res.ok) {
        state = "authenticated";
        return;
      }
      const data = await res.json();

      if (!data.enabled) {
        state = "authenticated";
        return;
      }

      if (data.valid === true) {
        state = "authenticated";
      } else {
        state = "login";
      }
    } catch {
      state = "authenticated";
    }
  });

  // Particle system - starts when login screen is shown
  $effect(() => {
    if (state !== "login" || !canvasEl) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvasEl!.width = window.innerWidth;
      canvasEl!.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const COUNT = 35;
    const CONNECT_DIST = 120;
    const particles: { x: number; y: number; vx: number; vy: number; r: number }[] = [];

    for (let i = 0; i < COUNT; i++) {
      particles.push({
        x: Math.random() * canvasEl!.width,
        y: Math.random() * canvasEl!.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
      });
    }

    const isLight = document.documentElement.classList.contains("light");
    const dotColor = isLight ? "37, 99, 235" : "77, 148, 255";

    function draw() {
      const w = canvasEl!.width;
      const h = canvasEl!.height;
      ctx!.clearRect(0, 0, w, h);

      // Move
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
      }

      // Lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECT_DIST) {
            const alpha = (1 - dist / CONNECT_DIST) * 0.7;
            ctx!.strokeStyle = `rgba(${dotColor}, ${alpha})`;
            ctx!.lineWidth = 0.5;
            ctx!.beginPath();
            ctx!.moveTo(particles[i].x, particles[i].y);
            ctx!.lineTo(particles[j].x, particles[j].y);
            ctx!.stroke();
          }
        }
      }

      // Dots
      for (const p of particles) {
        ctx!.fillStyle = `rgba(${dotColor}, 0.9)`;
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx!.fill();
      }

      animFrame = requestAnimationFrame(draw);
    }

    animFrame = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animFrame);
      window.removeEventListener("resize", resize);
    };
  });

  onDestroy(() => {
    if (typeof cancelAnimationFrame !== "undefined") cancelAnimationFrame(animFrame);
  });

  async function handleLogin() {
    if (!passwordInput.trim() || submitting) return;
    submitting = true;
    error = "";

    try {
      const res = await fetch(`${getBackendUrl()}/auth/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: passwordInput.trim() }),
      });

      if (!res.ok) throw new Error("network");

      const data = await res.json();

      if (data.valid && data.token) {
        setToken(data.token);
        sessionStorage.removeItem("auth-reload");
        state = "authenticated";
      } else {
        error = t("toast.wrongPassword");
        shakeKey++;
      }
    } catch (e: any) {
      error = e?.message === "network"
        ? t("toast.networkError")
        : t("toast.wrongPassword");
      shakeKey++;
    } finally {
      submitting = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") handleLogin();
  }
</script>

{#if state === "checking"}
  <div class="auth-screen">
    <div class="auth-spinner"></div>
  </div>
{:else if state === "login"}
  <div class="auth-screen">
    <!-- Layer 1: dot grid (CSS) -->
    <div class="auth-grid"></div>

    <!-- Layer 2: particles (Canvas) -->
    <canvas class="auth-particles" bind:this={canvasEl}></canvas>

    <!-- Layer 3: ambient glows -->
    <div class="auth-glow auth-glow-primary"></div>
    <div class="auth-glow auth-glow-secondary"></div>

    <!-- Layer 4: card -->
    <div class="auth-card" style="animation: auth-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1) both">
      <!-- Shield icon -->
      <div class="auth-icon-wrap" style="animation: auth-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.05s both">
        <div class="auth-icon-pulse"></div>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" />
          <path d="M10 12l2 2 4-4" stroke-width="1.5" />
        </svg>
      </div>

      <!-- Title -->
      <div class="auth-header" style="animation: auth-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both">
        <h1 class="auth-title">{t("auth.loginTitle")}</h1>
        <p class="auth-subtitle">{t("auth.loginPrompt")}</p>
      </div>

      <!-- Form -->
      <div class="auth-form" style="animation: auth-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both">
        {#key shakeKey}
          <input
            type="password"
            bind:value={passwordInput}
            onkeydown={handleKeydown}
            placeholder={t("auth.passwordPlaceholder")}
            maxlength={128}
            autocomplete="current-password"
            aria-label={t("auth.passwordPlaceholder")}
            class="auth-input"
            class:auth-input-error={!!error}
            autofocus
          />
        {/key}
        {#if error}
          <p class="auth-error" role="alert" style="animation: auth-enter 0.3s cubic-bezier(0.16, 1, 0.3, 1) both">{error}</p>
        {/if}
        <button
          onclick={handleLogin}
          disabled={submitting || !passwordInput.trim()}
          class="auth-btn"
        >
          {#if submitting}
            <span class="auth-btn-spinner"></span>
          {/if}
          {submitting ? t("btn.loggingIn") : t("btn.login")}
        </button>
      </div>
    </div>
  </div>
{:else}
  {@render children()}
{/if}

<style>
  /* ── Screen ────────────────────────────────────── */
  .auth-screen {
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    inset: 0;
    background: var(--color-surface-base);
    z-index: 50;
    overflow: hidden;
  }

  /* ── Layer 1: Dot grid ─────────────────────────── */
  .auth-grid {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, var(--color-accent) 0.5px, transparent 0.5px);
    background-size: 32px 32px;
    opacity: 0.24;
    mask-image: radial-gradient(ellipse 60% 50% at 50% 50%, black 20%, transparent 70%);
    pointer-events: none;
  }

  :global(.light) .auth-grid { opacity: 0.18; }

  /* ── Layer 2: Particle canvas ──────────────────── */
  .auth-particles {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  /* ── Layer 3: Ambient glows ────────────────────── */
  .auth-glow {
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
    filter: blur(80px);
  }

  .auth-glow-primary {
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, var(--color-accent) 0%, transparent 70%);
    opacity: 0.22;
    animation: auth-glow-drift 8s ease-in-out infinite alternate;
  }

  .auth-glow-secondary {
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, var(--color-accent) 0%, transparent 70%);
    opacity: 0.12;
    animation: auth-glow-drift 8s ease-in-out 2s infinite alternate-reverse;
  }

  :global(.light) .auth-glow-primary { opacity: 0.25; }
  :global(.light) .auth-glow-secondary { opacity: 0.15; }

  /* ── Layer 4: Card ─────────────────────────────── */
  .auth-card {
    position: relative;
    width: 100%;
    max-width: 360px;
    padding: 3rem 2.25rem 2.25rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.75rem;
    border-radius: 1.5rem;
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border-default);
    box-shadow:
      var(--shadow-lg),
      0 0 100px -10px rgba(77, 148, 255, 0.2);
    backdrop-filter: blur(8px);
  }

  :global(.light) .auth-card {
    box-shadow:
      var(--shadow-lg),
      0 0 100px -10px rgba(37, 99, 235, 0.18);
  }

  /* ── Shield icon ───────────────────────────────── */
  .auth-icon-wrap {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 72px;
    height: 72px;
    border-radius: 22px;
    background: linear-gradient(
      135deg,
      var(--color-accent-muted) 0%,
      rgba(77, 148, 255, 0.18) 100%
    );
    color: var(--color-accent);
    border: 1px solid var(--color-accent-strong);
  }

  .auth-icon-pulse {
    position: absolute;
    inset: -4px;
    border-radius: 26px;
    border: 1.5px solid var(--color-accent);
    opacity: 0;
    animation: auth-pulse 3s ease-out infinite;
  }

  /* ── Header ────────────────────────────────────── */
  .auth-header {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .auth-title {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--color-text-primary);
  }

  .auth-subtitle {
    font-size: 0.8125rem;
    color: var(--color-text-muted);
    line-height: 1.4;
  }

  /* ── Form ───────────────────────────────────────── */
  .auth-form {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .auth-input {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-family: var(--font-sans);
    letter-spacing: 0;
    color: var(--color-text-primary);
    background: var(--color-surface-overlay);
    border: 1.5px solid var(--color-border-default);
    border-radius: 0.75rem;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .auth-input::placeholder {
    color: var(--color-text-muted);
    opacity: 0.7;
  }

  .auth-input:focus {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 3px var(--color-accent-muted);
  }

  .auth-input-error {
    border-color: var(--color-status-critical);
    animation: shake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
  }

  .auth-input-error:focus {
    border-color: var(--color-status-critical);
    box-shadow: 0 0 0 3px rgba(240, 104, 104, 0.1);
  }

  .auth-error {
    font-size: 0.75rem;
    color: var(--color-status-critical);
    padding-left: 0.25rem;
  }

  /* ── Button ────────────────────────────────────── */
  .auth-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.875rem 1rem;
    font-size: 0.875rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #fff;
    background: var(--color-accent);
    border: none;
    border-radius: 0.75rem;
    cursor: pointer;
    transition: background 0.2s, transform 0.15s, box-shadow 0.2s, opacity 0.15s;
    box-shadow: 0 2px 12px rgba(77, 148, 255, 0.25);
  }

  :global(.light) .auth-btn {
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.2);
  }

  .auth-btn:hover:not(:disabled) {
    background: var(--color-accent-hover);
    box-shadow: 0 4px 20px rgba(77, 148, 255, 0.35);
    transform: translateY(-1px);
  }

  .auth-btn:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
    box-shadow: 0 1px 6px rgba(77, 148, 255, 0.2);
  }

  .auth-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    box-shadow: none;
  }

  .auth-btn-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  /* ── Loading spinner ───────────────────────────── */
  .auth-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--color-border-default);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  /* ── Keyframes ─────────────────────────────────── */
  @keyframes auth-enter {
    from {
      opacity: 0;
      transform: translateY(16px) scale(0.97);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes shake {
    10%, 90% { transform: translateX(-1px); }
    20%, 80% { transform: translateX(2px); }
    30%, 50%, 70% { transform: translateX(-3px); }
    40%, 60% { transform: translateX(3px); }
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @keyframes auth-pulse {
    0% { opacity: 0.4; transform: scale(1); }
    100% { opacity: 0; transform: scale(1.3); }
  }

  @keyframes auth-glow-drift {
    from { transform: translate(-10%, -10%); }
    to { transform: translate(10%, 10%); }
  }

  @media (prefers-reduced-motion: reduce) {
    .auth-input-error { animation: none; }
    .auth-card, .auth-form, .auth-header, .auth-icon-wrap, .auth-error { animation: none; }
    .auth-icon-pulse { animation: none; display: none; }
    .auth-glow-primary, .auth-glow-secondary { animation: none; }
    .auth-particles { display: none; }
  }
</style>
