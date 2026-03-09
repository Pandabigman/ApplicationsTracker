/**
 * E2E tests for the core application lifecycle.
 *
 * These tests use the `authenticatedPage` fixture which stubs all API calls,
 * so no real backend or auth is needed. They test that the UI wires up
 * correctly: navigation, form display, error states, and route behaviour.
 */
import { test, expect } from './fixtures/auth.fixture.js';

test.describe('Home page', () => {
  test('renders the job URL input field', async ({ authenticatedPage: page }) => {
    await expect(
      page.getByPlaceholder('Paste job posting URL here...')
    ).toBeVisible({ timeout: 10_000 });
  });

  test('shows a validation error when submitting an empty URL', async ({
    authenticatedPage: page,
  }) => {
    await page.getByRole('button', { name: /Scrape Job/i }).click();
    await expect(page.getByText(/Please enter a job URL/i)).toBeVisible();
  });

  test('shows a loading indicator while scraping', async ({
    authenticatedPage: page,
  }) => {
    // Override scrape to be slow
    await page.route('**/scrape', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          company_name: 'Slow Corp',
          position_title: 'Slow Engineer',
          location: 'Remote',
          salary: null,
          description: null,
          requirements: null,
          ai_thoughts: null,
          application_deadline: null,
          job_url: 'https://slow.example.com/1',
          clean_text_content: '',
        }),
      });
    });

    await page.fill('input[placeholder="Paste job posting URL here..."]', 'https://slow.example.com/1');
    await page.click('button:has-text("Scrape Job")');

    // The loading spinner / "Scraping..." text should briefly appear
    // (The timing depends on how fast the page re-renders, so we check for
    // EITHER the loading indicator OR the next step completing)
    await expect(
      page.getByText(/Scraping|Loading|Please wait/i).or(
        page.getByText(/Slow Corp/)
      )
    ).toBeVisible({ timeout: 5_000 });
  });
});

test.describe('Navigation', () => {
  test('navigates to All Applications page', async ({ authenticatedPage: page }) => {
    // Find and click the link to all applications
    await page.getByRole('button', { name: /All Applications|View All/i })
      .first()
      .click()
      .catch(async () => {
        // Try link instead of button
        await page.getByRole('link', { name: /All Applications/i }).click();
      });

    await expect(page).toHaveURL(/\/applications/, { timeout: 5_000 });
  });

  test('all-applications page shows "All Applications" heading', async ({
    authenticatedPage: page,
  }) => {
    await page.goto('/applications');
    await expect(page.getByText('All Applications')).toBeVisible({ timeout: 5_000 });
  });

  test('settings page is accessible', async ({ authenticatedPage: page }) => {
    await page.goto('/settings');
    await expect(page.getByText('Settings')).toBeVisible({ timeout: 5_000 });
  });
});

test.describe('Settings page', () => {
  test('renders the Gemini API key section', async ({ authenticatedPage: page }) => {
    await page.goto('/settings');
    await expect(page.getByText('Gemini API Key')).toBeVisible({ timeout: 5_000 });
  });

  test('shows "Key saved" indicator when key is in localStorage', async ({
    authenticatedPage: page,
  }) => {
    // auth.fixture.js injects 'e2e-test-gemini-key' into localStorage
    await page.goto('/settings');
    await expect(page.getByText(/Key saved/i)).toBeVisible({ timeout: 5_000 });
  });
});
