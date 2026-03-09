/**
 * Integration tests for the AllApplications page.
 *
 * MSW intercepts all API calls. Tests cover initial render, filtering,
 * sorting, empty-state messages, and export.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server, FIXTURE_APP } from './setup/msw-handlers.js';
import { setAuthTokenGetter } from '../../src/services/api.js';
import AllApplications from '../../src/pages/AllApplications.jsx';

// Register a mock auth token getter for all tests in this file
setAuthTokenGetter(async () => 'mock-token');

function renderPage() {
  return render(
    <MemoryRouter>
      <AllApplications />
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// Initial render
// ---------------------------------------------------------------------------

describe('AllApplications — initial render', () => {
  it('shows a loading spinner while data is fetching', () => {
    renderPage();
    // Spinner is present before the fetch resolves
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders the application list after data loads', async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('Staff Engineer')).toBeInTheDocument()
    );
    expect(screen.getByText('Stripe')).toBeInTheDocument();
  });

  it('shows the correct count of applications', async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByText(/Showing 1 of 1/)).toBeInTheDocument()
    );
  });

  it('renders the page heading', async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('All Applications')).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

describe('AllApplications — empty state', () => {
  beforeEach(() => {
    server.use(
      http.get('http://localhost:8000/applications', () => {
        return HttpResponse.json([]);
      })
    );
  });

  it('shows no-applications message when list is empty', async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('No Applications Found')).toBeInTheDocument()
    );
  });

  it('shows add application button in empty state', async () => {
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('Add Application')).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Search filtering
// ---------------------------------------------------------------------------

describe('AllApplications — search filtering', () => {
  it('hides non-matching applications when search query is typed', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    fireEvent.change(
      screen.getByPlaceholderText('Company, position, location...'),
      { target: { value: 'nomatch_xyz' } }
    );

    await waitFor(() =>
      expect(screen.queryByText('Staff Engineer')).not.toBeInTheDocument()
    );
  });

  it('shows no-applications message when search yields no results', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    fireEvent.change(
      screen.getByPlaceholderText('Company, position, location...'),
      { target: { value: 'nomatch_xyz' } }
    );

    await waitFor(() =>
      expect(screen.getByText('No Applications Found')).toBeInTheDocument()
    );
  });

  it('shows "Try adjusting your filters" message on filtered empty state', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    fireEvent.change(
      screen.getByPlaceholderText('Company, position, location...'),
      { target: { value: 'nomatch' } }
    );

    await waitFor(() =>
      expect(screen.getByText(/adjusting your filters/i)).toBeInTheDocument()
    );
  });

  it('shows matching applications case-insensitively', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    // Search in lowercase for an uppercase company name
    fireEvent.change(
      screen.getByPlaceholderText('Company, position, location...'),
      { target: { value: 'stripe' } }
    );

    await waitFor(() =>
      expect(screen.getByText('Staff Engineer')).toBeInTheDocument()
    );
  });

  it('updates the count display when filtering', async () => {
    renderPage();
    await waitFor(() => screen.getByText(/Showing 1 of 1/));

    fireEvent.change(
      screen.getByPlaceholderText('Company, position, location...'),
      { target: { value: 'nomatch' } }
    );

    await waitFor(() =>
      expect(screen.getByText(/Showing 0 of 1/)).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Status filtering
// ---------------------------------------------------------------------------

describe('AllApplications — status filtering', () => {
  it('shows all applications when status filter is "all"', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));
    // The default is "all" — application should be visible
    expect(screen.getByText('Staff Engineer')).toBeInTheDocument();
  });

  it('hides application when status filter does not match', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    const statusSelect = screen.getByDisplayValue('All Statuses');
    fireEvent.change(statusSelect, { target: { value: 'Rejected' } });

    await waitFor(() =>
      expect(screen.queryByText('Staff Engineer')).not.toBeInTheDocument()
    );
  });

  it('shows application when status filter matches', async () => {
    renderPage();
    await waitFor(() => screen.getByText('Staff Engineer'));

    const statusSelect = screen.getByDisplayValue('All Statuses');
    fireEvent.change(statusSelect, { target: { value: 'Applied' } });

    await waitFor(() =>
      expect(screen.getByText('Staff Engineer')).toBeInTheDocument()
    );
  });
});
