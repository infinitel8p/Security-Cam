/// <reference types="astro/client" />

// Build-time git info injected via vite.define in astro.config.mjs
declare const __GIT_BRANCH__: string;
declare const __GIT_COMMIT__: string;

// View Transitions API (progressive enhancement)
interface ViewTransition {
  finished: Promise<void>;
  ready: Promise<void>;
  updateCallbackDone: Promise<void>;
}

interface Document {
  startViewTransition?(callback: () => void | Promise<void>): ViewTransition;
}
