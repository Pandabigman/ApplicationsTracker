/**
 * Playwright auth fixture.
 *
 * The Clerk mock in e2e/clerk-mock.js (aliased via vite.config.e2e.js) means
 * the app always thinks the user is signed in. This fixture only needs to:
 *   1. Stub the backend API so tests never need a real Render/Neon instance
 *   2. Navigate to the root URL
 */
import { test as base } from '@playwright/test';

export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    // Stub backend API — no real server required
    await page.route('**/api/*/applications', stubApplications);
    await page.route('**/applications', stubApplications);
    await page.route('**/applications/**', stubApplicationDetail);
    await page.route('**/scrape', stubScrape);
    await page.route('**/export/excel', stubExport);

    await page.goto('/');
    await use(page);
  },
});

export { expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// Route stubs
// ---------------------------------------------------------------------------

async function stubApplications(route) {
  const method = route.request().method();
  if (method === 'GET') {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  } else if (method === 'POST') {
    const body = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 42,
        company_name: body.company_name || 'Test Corp',
        position_title: body.position_title || 'Test Role',
        location: body.location || null,
        salary: body.salary || null,
        status: body.status || 'Applied',
        job_url: body.job_url || null,
        date_applied: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        notes: [],
        activities: [],
        deadlines: [],
        job_details: null,
      }),
    });
  } else {
    await route.continue();
  }
}

async function stubApplicationDetail(route) {
  const method = route.request().method();
  if (method === 'GET') {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
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
        job_details: {
          id: 1,
          application_id: 42,
          description: 'Build safe AI',
          requirements: 'ML experience',
          ai_thoughts: 'Focus on safety research',
          clean_text_content: '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      }),
    });
  } else if (method === 'PUT') {
    const body = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 42, ...body }),
    });
  } else if (method === 'DELETE') {
    await route.fulfill({ status: 204 });
  } else if (method === 'POST') {
    const body = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ id: 1, application_id: 42, ...body }),
    });
  } else {
    await route.continue();
  }
}

async function stubScrape(route) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      company_name: 'Anthropic',
      position_title: 'Research Engineer',
      location: 'San Francisco',
      salary: '$250k',
      description: 'Build safe AI systems',
      requirements: 'ML background required',
      ai_thoughts: 'Highlight safety research experience',
      application_deadline: null,
      job_url: 'https://anthropic.com/careers/1',
      clean_text_content: 'mocked clean text',
    }),
  });
}

async function stubExport(route) {
  await route.fulfill({
    status: 200,
    contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    body: Buffer.from('fake xlsx'),
  });
}
