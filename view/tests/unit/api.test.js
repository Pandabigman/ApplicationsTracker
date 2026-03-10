/**
 * Unit tests for src/services/api.js
 *
 * Covers:
 * - safeHref() XSS prevention (security-critical)
 * - authFetch() Bearer token injection
 * - api.scrapeUrl() scraping behaviour
 * - Error propagation on non-OK responses
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// We import the module under test directly.
// Vitest resets modules between files; within a file we manage state manually.
import { safeHref, setAuthTokenGetter, api } from '../../src/services/api.js';

// ---------------------------------------------------------------------------
// safeHref — XSS prevention
// ---------------------------------------------------------------------------

describe('safeHref', () => {
  it('returns an https URL unchanged', () => {
    expect(safeHref('https://jobs.lever.co/stripe/abc123')).toBe('https://jobs.lever.co/stripe/abc123');
  });

  it('returns an http URL unchanged', () => {
    expect(safeHref('http://example.com/careers/job-1')).toBe('http://example.com/careers/job-1');
  });

  it('returns null for a javascript: URL', () => {
    expect(safeHref('javascript:alert(document.cookie)')).toBeNull();
  });

  it('returns null for javascript: with encoded characters', () => {
    expect(safeHref('javascript:void(0)')).toBeNull();
  });

  it('returns null for a data: URL', () => {
    expect(safeHref('data:text/html,<script>alert(1)</script>')).toBeNull();
  });

  it('returns null for a vbscript: URL', () => {
    expect(safeHref('vbscript:msgbox(1)')).toBeNull();
  });

  it('returns null for a file: URL', () => {
    expect(safeHref('file:///etc/passwd')).toBeNull();
  });

  it('returns null for null input', () => {
    expect(safeHref(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(safeHref(undefined)).toBeNull();
  });

  it('returns null for an empty string', () => {
    expect(safeHref('')).toBeNull();
  });

  it('returns null for a relative path (not a full URL)', () => {
    expect(safeHref('/relative/path')).toBeNull();
  });

  it('returns null for a plain string that is not a URL', () => {
    expect(safeHref('not a url at all')).toBeNull();
  });

  it('returns null for a URL with no protocol', () => {
    expect(safeHref('//example.com/job')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// authFetch — Bearer token injection
// ---------------------------------------------------------------------------

describe('authFetch via api.getApplications', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    // Reset the token getter to avoid test bleed
    setAuthTokenGetter(null);
  });

  it('injects Authorization header when token getter is set', async () => {
    setAuthTokenGetter(async () => 'test-bearer-token-xyz');
    await api.getApplications();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers['Authorization']).toBe('Bearer test-bearer-token-xyz');
  });

  it('does not add Authorization header when getter returns null', async () => {
    setAuthTokenGetter(async () => null);
    await api.getApplications();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers['Authorization']).toBeUndefined();
  });

  it('does not add Authorization header when no getter is registered', async () => {
    setAuthTokenGetter(null);
    await api.getApplications();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers?.['Authorization']).toBeUndefined();
  });

  it('throws on non-ok responses', async () => {
    setAuthTokenGetter(async () => 'token');
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Server error' }),
    });

    await expect(api.getApplications()).rejects.toThrow('Failed to fetch applications');
  });
});

// ---------------------------------------------------------------------------
// api.scrapeUrl
// ---------------------------------------------------------------------------

describe('api.scrapeUrl', () => {
  beforeEach(() => {
    setAuthTokenGetter(async () => 'mock-token');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ company_name: 'Corp', position_title: 'Dev' }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthTokenGetter(null);
  });

  it('sends the URL in the request body', async () => {
    await api.scrapeUrl('https://jobs.example.com/456');

    const [, options] = global.fetch.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.url).toBe('https://jobs.example.com/456');
  });

  it('does not send X-Gemini-Api-Key header', async () => {
    await api.scrapeUrl('https://jobs.example.com/123');

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers['X-Gemini-Api-Key']).toBeUndefined();
  });

  it('throws the API error detail on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Rate limit exceeded' }),
    });

    await expect(api.scrapeUrl('https://example.com')).rejects.toThrow('Rate limit exceeded');
  });

  it('falls back to generic message when API error has no detail', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({}),
    });

    await expect(api.scrapeUrl('https://example.com')).rejects.toThrow('Failed to scrape URL');
  });
});

// ---------------------------------------------------------------------------
// api.deleteApplication — no response body
// ---------------------------------------------------------------------------

describe('api.deleteApplication', () => {
  beforeEach(() => {
    setAuthTokenGetter(async () => 'mock-token');
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAuthTokenGetter(null);
  });

  it('does not throw on 204 No Content response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => null,
    });

    await expect(api.deleteApplication(1)).resolves.not.toThrow();
  });

  it('sends DELETE request to correct URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => null });

    await api.deleteApplication(42);

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/applications/42');
    expect(options.method).toBe('DELETE');
  });
});
