/**
 * Playwright auth fixture.
 *
 * Provides an `authenticatedPage` that:
 * 1. Stubs all API routes so the app never hits a real backend
 * 2. Injects Gemini key into localStorage
 * 3. Navigates to the root URL
 *
 * Auth strategy: Clerk requires a real browser session with a signed-in
 * user for true E2E. In CI we stub the backend routes and add a flag
 * (`window.__CLERK_TESTING__`) that the app can use in development builds
 * to skip the auth check. For full auth E2E, use Clerk's test mode with
 * a dedicated test account and set CLERK_TESTING_TOKEN in the environment.
 */
import { test as base } from '@playwright/test';

// ---------------------------------------------------------------------------
// Shared stub data
// ---------------------------------------------------------------------------

const STUB_APPLICATIONS = [];

const STUB_SCRAPED_JOB = {
  company_name: 'Anthropic',
  position_title: 'Research Engineer',
  location: 'San Francisco',
  salary: '$250k',
  description: 'Build safe AI systems',
  requirements: 'ML background required',
  ai_thoughts: 'Highlight safety research experience',
  application_deadline: null,
  job_url: 'https://anthropic.com/careers/1',
  clean_text_content: 'Mocked clean text',
};

const STUB_CREATED_APP = {
  id: 42,
  company_name: 'Anthropic',
  position_title: 'Research Engineer',
  location: 'San Francisco',
  salary: '$250k',
  status: 'Applied',
  job_url: 'https://anthropic.com/careers/1',
  date_applied: new Date().toISOString(),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  notes: [],
  activities: [],
  deadlines: [],
  job_details: null,
};

// ---------------------------------------------------------------------------
// Extended test fixture
// ---------------------------------------------------------------------------

export const test = base.extend({
  /**
   * `authenticatedPage` — a page with all API calls stubbed and a Gemini key
   * pre-loaded in localStorage. Navigate to '/' to start each test.
   */
  authenticatedPage: async ({ page }, use) => {
    // Stub the backend API — no real Render/Neon required in E2E
    await page.route('**/applications', async (route) => {
      const method = route.request().method();
      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(STUB_APPLICATIONS),
        });
      } else if (method === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ ...STUB_CREATED_APP, ...body, id: 42 }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/applications/**', async (route) => {
      const method = route.request().method();
      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...STUB_CREATED_APP, notes: [], activities: [], deadlines: [], job_details: null }),
        });
      } else if (method === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(STUB_CREATED_APP),
        });
      } else if (method === 'DELETE') {
        await route.fulfill({ status: 204 });
      } else {
        await route.continue();
      }
    });

    await page.route('**/scrape', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(STUB_SCRAPED_JOB),
      });
    });

    await page.route('**/validate-key', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ valid: true }),
      });
    });

    await page.route('**/export/excel', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        body: Buffer.from('fake xlsx'),
      });
    });

    // Inject localStorage values before page load
    await page.addInitScript(() => {
      localStorage.setItem('gemini_api_key', 'e2e-test-gemini-key');
      // Flag for the app to know we're in E2E test mode
      window.__E2E_TEST__ = true;
    });

    await page.goto('/');
    await use(page);
  },
});

export { expect } from '@playwright/test';
