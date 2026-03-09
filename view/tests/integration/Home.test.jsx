/**
 * Integration tests for the Home page.
 *
 * Tests: initial render, URL scraper form validation, error states,
 * upcoming deadlines display.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from './setup/msw-handlers.js';
import { setAuthTokenGetter } from '../../src/services/api.js';
import Home from '../../src/pages/Home.jsx';

setAuthTokenGetter(async () => 'mock-token');

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// Initial render
// ---------------------------------------------------------------------------

describe('Home — initial render', () => {
  it('renders the URL input field', async () => {
    renderHome();
    await waitFor(() =>
      expect(
        screen.getByPlaceholderText(/Paste job posting URL here/i)
      ).toBeInTheDocument()
    );
  });

  it('renders the Scrape Job submit button', async () => {
    renderHome();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Scrape Job/i })).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Form validation
// ---------------------------------------------------------------------------

describe('Home — scraper form validation', () => {
  beforeEach(() => {
    localStorage.setItem('gemini_api_key', 'AIzaSy-test-key');
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('shows an error when submitting an empty URL', async () => {
    renderHome();
    await waitFor(() => screen.getByRole('button', { name: /Scrape Job/i }));

    fireEvent.click(screen.getByRole('button', { name: /Scrape Job/i }));

    await waitFor(() =>
      expect(screen.getByText(/Please enter a job URL/i)).toBeInTheDocument()
    );
  });

  it('clears the error when user types a URL', async () => {
    renderHome();
    await waitFor(() => screen.getByRole('button', { name: /Scrape Job/i }));

    // Trigger validation error first
    fireEvent.click(screen.getByRole('button', { name: /Scrape Job/i }));
    await waitFor(() => screen.getByText(/Please enter a job URL/i));

    // Now type a URL — error should disappear on next submit attempt
    fireEvent.change(
      screen.getByPlaceholderText(/Paste job posting URL here/i),
      { target: { value: 'https://example.com/job' } }
    );

    // Error message should still be gone after successful input
    expect(screen.queryByText(/Please enter a job URL/i)).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Upcoming deadlines
// ---------------------------------------------------------------------------

describe('Home — upcoming deadlines section', () => {
  it('shows no upcoming deadlines when applications have none', async () => {
    // Default MSW handler returns app with no deadlines
    renderHome();
    await waitFor(() =>
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    );
    // Should not show any deadline cards (app has empty deadlines array)
  });

  it('shows upcoming deadline when application has one', async () => {
    const appWithDeadline = {
      id: 2,
      company_name: 'Anthropic',
      position_title: 'Research Engineer',
      status: 'Applied',
      location: 'SF',
      salary: '$250k',
      job_url: null,
      date_applied: '2026-01-20T10:00:00Z',
      created_at: '2026-01-20T10:00:00Z',
      updated_at: '2026-01-20T10:00:00Z',
      notes: [],
      activities: [],
      job_details: null,
      deadlines: [
        {
          id: 1,
          application_id: 2,
          deadline_type: 'Application Deadline',
          deadline_date: '2026-12-31T23:59:00Z',
          is_completed: false,
          description: null,
          created_at: '2026-01-20T10:00:00Z',
          updated_at: '2026-01-20T10:00:00Z',
        },
      ],
    };

    server.use(
      http.get('http://localhost:8000/applications', () => {
        return HttpResponse.json([appWithDeadline]);
      })
    );

    renderHome();
    await waitFor(() =>
      expect(screen.getByText('Anthropic')).toBeInTheDocument()
    );
  });
});
