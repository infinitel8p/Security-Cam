// @ts-check
import { defineConfig } from 'astro/config';
import { execSync } from 'child_process';

import tailwindcss from '@tailwindcss/vite';

import svelte from '@astrojs/svelte';

function gitInfo() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();
    const commit = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
    return { branch, commit };
  } catch {
    return { branch: '', commit: '' };
  }
}

const git = gitInfo();

// https://astro.build/config
export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
    define: {
      __GIT_BRANCH__: JSON.stringify(git.branch),
      __GIT_COMMIT__: JSON.stringify(git.commit),
    },
  },

  integrations: [svelte()]
});