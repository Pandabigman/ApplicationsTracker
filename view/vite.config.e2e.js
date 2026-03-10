/**
 * Vite config for E2E tests.
 *
 * Identical to the production config except @clerk/clerk-react is aliased
 * to a mock that always returns a signed-in user, so Playwright tests never
 * see the Clerk login page.
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@clerk/clerk-react': path.resolve(__dirname, 'e2e/clerk-mock.js'),
    },
  },
});
