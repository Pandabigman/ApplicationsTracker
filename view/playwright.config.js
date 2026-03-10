import { defineConfig, devices } from '@playwright/test';

// E2E tests run on port 5174 locally so they don't conflict with the
// regular dev server (port 5173) running in Docker.
const E2E_PORT = 5174;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    // CI sets PLAYWRIGHT_BASE_URL to the preview server (port 4173).
    // Locally defaults to the E2E Vite server on 5174.
    baseURL: process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${E2E_PORT}`,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Starts a separate Vite dev server on port 5174 with the Clerk mock.
  // Leave the regular app running on 5173 — no conflict.
  webServer: process.env.CI
    ? undefined
    : {
        command: `vite --config vite.config.e2e.js --port ${E2E_PORT}`,
        url: `http://localhost:${E2E_PORT}`,
        reuseExistingServer: false,
      },
});
