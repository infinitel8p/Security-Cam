<script lang="ts">
  import { onMount } from "svelte";
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
    <!-- Accent glow behind the card -->
    <div class="auth-glow"></div>

    <div class="auth-card" style="animation: auth-enter 0.6s cubic-bezier(0.16, 1, 0.3, 1) both">
      <!-- Shield icon -->
      <div class="auth-icon-wrap">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" />
        </svg>
      </div>

      <!-- Title -->
      <div class="auth-header">
        <h1 class="auth-title">{t("auth.loginTitle")}</h1>
        <p class="auth-subtitle">{t("auth.loginPrompt")}</p>
      </div>

      <!-- Input group -->
      <div class="auth-form" style="animation: auth-enter 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both">
        {#key shakeKey}
          <input
            type="password"
            bind:value={passwordInput}
            onkeydown={handleKeydown}
            placeholder={t("auth.passwordPlaceholder")}
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
    min-height: 100svh;
    background: var(--color-surface-base);
    position: relative;
    overflow: hidden;
  }

  /* ── Ambient glow ──────────────────────────────── */
  .auth-glow {
    position: absolute;
    width: 360px;
    height: 360px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--color-accent) 0%, transparent 70%);
    opacity: 0.04;
    filter: blur(60px);
    pointer-events: none;
  }

  :global(.light) .auth-glow {
    opacity: 0.06;
  }

  /* ── Card ───────────────────────────────────────── */
  .auth-card {
    position: relative;
    width: 100%;
    max-width: 340px;
    padding: 2.5rem 2rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    border-radius: 1.25rem;
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border-default);
    box-shadow: var(--shadow-lg);
  }

  /* ── Shield icon ───────────────────────────────── */
  .auth-icon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 16px;
    background: var(--color-accent-muted);
    color: var(--color-accent);
    border: 1px solid var(--color-accent-strong);
  }

  /* ── Header ────────────────────────────────────── */
  .auth-header {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .auth-title {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
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
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #fff;
    background: var(--color-accent);
    border: none;
    border-radius: 0.75rem;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s, opacity 0.15s;
  }

  .auth-btn:hover:not(:disabled) {
    background: var(--color-accent-hover);
  }

  .auth-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .auth-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
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

  @media (prefers-reduced-motion: reduce) {
    .auth-input-error { animation: none; }
    .auth-card, .auth-form, .auth-error { animation: none; }
  }
</style>
