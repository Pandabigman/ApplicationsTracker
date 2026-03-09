/**
 * Integration tests for the Settings page.
 *
 * Tests the Gemini API key BYOK workflow:
 * save key → key stored in localStorage
 * test key → shows valid/invalid status
 * clear key → removes from localStorage
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from './setup/msw-handlers.js';
import { setAuthTokenGetter } from '../../src/services/api.js';
import Settings from '../../src/pages/Settings.jsx';

setAuthTokenGetter(async () => 'mock-token');

function renderSettings() {
  return render(
    <MemoryRouter>
      <Settings />
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

describe('Settings — initial state', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the settings heading', () => {
    renderSettings();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('does not show "Key saved" banner when localStorage is empty', () => {
    renderSettings();
    expect(screen.queryByText(/Key saved/)).not.toBeInTheDocument();
  });

  it('shows a placeholder for entering a new key', () => {
    renderSettings();
    expect(screen.getByPlaceholderText(/Enter your Gemini API key/)).toBeInTheDocument();
  });

  it('Save Key button is disabled when input is empty', () => {
    renderSettings();
    expect(screen.getByText('Save Key')).toBeDisabled();
  });

  it('Test Key button is disabled when input is empty and no saved key', () => {
    renderSettings();
    expect(screen.getByText('Test Key')).toBeDisabled();
  });

  it('does not show Clear Key button when no key is saved', () => {
    renderSettings();
    expect(screen.queryByText('Clear Key')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// With existing saved key
// ---------------------------------------------------------------------------

describe('Settings — with a saved key', () => {
  beforeEach(() => {
    localStorage.setItem('gemini_api_key', 'AIzaSy-existing-key-5678');
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('shows the "Key saved" banner with masked key', () => {
    renderSettings();
    expect(screen.getByText(/Key saved/)).toBeInTheDocument();
    expect(screen.getByText(/AIza/)).toBeInTheDocument(); // first 4 chars
  });

  it('shows Clear Key button when a key is saved', () => {
    renderSettings();
    expect(screen.getByText('Clear Key')).toBeInTheDocument();
  });

  it('shows placeholder for replacing the key', () => {
    renderSettings();
    expect(screen.getByPlaceholderText(/Enter new key/)).toBeInTheDocument();
  });

  it('Test Key button is enabled when a saved key exists', () => {
    renderSettings();
    expect(screen.getByText('Test Key')).not.toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// Save key flow
// ---------------------------------------------------------------------------

describe('Settings — save key flow', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('saves key to localStorage and clears the input on Save Key click', async () => {
    const user = userEvent.setup();
    renderSettings();

    await user.type(
      screen.getByPlaceholderText(/Enter your Gemini API key/),
      'AIzaSy-new-key-12345'
    );
    fireEvent.click(screen.getByText('Save Key'));

    expect(localStorage.getItem('gemini_api_key')).toBe('AIzaSy-new-key-12345');
    // Input should be cleared after save
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Enter new key/)).toHaveValue('')
    );
  });
});

// ---------------------------------------------------------------------------
// Test key flow
// ---------------------------------------------------------------------------

describe('Settings — test key flow', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('shows "API key is valid!" after successful validation', async () => {
    const user = userEvent.setup();
    // Default MSW handler returns { valid: true }
    renderSettings();

    await user.type(
      screen.getByPlaceholderText(/Enter your Gemini API key/),
      'AIzaSy-valid-key'
    );
    fireEvent.click(screen.getByText('Test Key'));

    await waitFor(() =>
      expect(screen.getByText(/API key is valid!/)).toBeInTheDocument()
    );
  });

  it('shows "API key is invalid" after failed validation', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('http://localhost:8000/validate-key', () => {
        return HttpResponse.json({ detail: 'Invalid API key.' }, { status: 401 });
      })
    );
    renderSettings();

    await user.type(
      screen.getByPlaceholderText(/Enter your Gemini API key/),
      'AIzaSy-bad-key'
    );
    fireEvent.click(screen.getByText('Test Key'));

    await waitFor(() =>
      expect(screen.getByText(/API key is invalid/)).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Clear key flow
// ---------------------------------------------------------------------------

describe('Settings — clear key flow', () => {
  beforeEach(() => {
    localStorage.setItem('gemini_api_key', 'AIzaSy-to-be-cleared');
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('removes key from localStorage when Clear Key is clicked', () => {
    renderSettings();
    fireEvent.click(screen.getByText('Clear Key'));
    expect(localStorage.getItem('gemini_api_key')).toBeNull();
  });

  it('hides the "Key saved" banner after clearing', async () => {
    renderSettings();
    fireEvent.click(screen.getByText('Clear Key'));
    // After clear, the component re-renders without the savedKey banner
    await waitFor(() =>
      expect(screen.queryByText(/Key saved/)).not.toBeInTheDocument()
    );
  });
});
