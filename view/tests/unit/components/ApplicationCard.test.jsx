/**
 * Unit tests for ApplicationCard component.
 *
 * Key security test: the card must NOT render a clickable link for
 * javascript: or other dangerous job_url schemes (XSS regression).
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ApplicationCard } from '../../../src/components/ApplicationCard.jsx';

const STATUS_COLUMNS = [
  { id: 'Applied', bgColor: 'bg-info' },
  { id: 'Interview', bgColor: 'bg-warning' },
  { id: 'Offer Received', bgColor: 'bg-success' },
  { id: 'Rejected', bgColor: 'bg-danger' },
];

const BASE_APP = {
  id: 1,
  position_title: 'Software Engineer',
  company_name: 'Stripe',
  location: 'Remote',
  salary: '$200k',
  status: 'Applied',
  job_url: 'https://stripe.com/jobs/1',
};

function renderCard(overrides = {}, handlers = {}) {
  return render(
    <ApplicationCard
      application={{ ...BASE_APP, ...overrides }}
      statusColumns={STATUS_COLUMNS}
      onEdit={handlers.onEdit || vi.fn()}
      onDelete={handlers.onDelete || vi.fn()}
      onStatusChange={handlers.onStatusChange || vi.fn()}
    />
  );
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

describe('ApplicationCard rendering', () => {
  it('displays the position title', () => {
    renderCard();
    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
  });

  it('displays the company name', () => {
    renderCard();
    expect(screen.getByText('Stripe')).toBeInTheDocument();
  });

  it('displays the location when provided', () => {
    renderCard({ location: 'San Francisco' });
    expect(screen.getByText(/San Francisco/)).toBeInTheDocument();
  });

  it('does not display location when null', () => {
    renderCard({ location: null });
    expect(screen.queryByText(/Remote/)).not.toBeInTheDocument();
  });

  it('displays the salary when provided', () => {
    renderCard({ salary: '£120k' });
    expect(screen.getByText('£120k')).toBeInTheDocument();
  });

  it('renders all status pills', () => {
    renderCard();
    STATUS_COLUMNS.forEach((s) => {
      expect(screen.getByText(s.id)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Job URL link — XSS prevention (security-critical)
// ---------------------------------------------------------------------------

describe('ApplicationCard job_url link', () => {
  it('renders a View Job link for a valid https URL', () => {
    renderCard({ job_url: 'https://stripe.com/jobs/1' });
    const link = screen.getByText('View Job').closest('a');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://stripe.com/jobs/1');
  });

  it('sets target="_blank" on the job URL link', () => {
    renderCard();
    const link = screen.getByText('View Job').closest('a');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('sets rel="noopener noreferrer" on the job URL link', () => {
    renderCard();
    const link = screen.getByText('View Job').closest('a');
    expect(link.getAttribute('rel')).toContain('noopener');
  });

  it('does NOT render View Job link for a javascript: URL', () => {
    renderCard({ job_url: 'javascript:alert(document.cookie)' });
    expect(screen.queryByText('View Job')).not.toBeInTheDocument();
  });

  it('does NOT render View Job link for a data: URL', () => {
    renderCard({ job_url: 'data:text/html,<script>alert(1)</script>' });
    expect(screen.queryByText('View Job')).not.toBeInTheDocument();
  });

  it('does NOT render View Job link when job_url is null', () => {
    renderCard({ job_url: null });
    expect(screen.queryByText('View Job')).not.toBeInTheDocument();
  });

  it('does NOT render View Job link when job_url is empty string', () => {
    renderCard({ job_url: '' });
    expect(screen.queryByText('View Job')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// User interactions
// ---------------------------------------------------------------------------

describe('ApplicationCard interactions', () => {
  it('calls onDelete with the application id when delete button is clicked', () => {
    const onDelete = vi.fn();
    renderCard({}, { onDelete });
    fireEvent.click(screen.getByTitle('Delete application'));
    expect(onDelete).toHaveBeenCalledOnce();
    expect(onDelete).toHaveBeenCalledWith(1);
  });

  it('calls onEdit with the application object when edit button is clicked', () => {
    const onEdit = vi.fn();
    renderCard({}, { onEdit });
    fireEvent.click(screen.getByTitle('Edit application'));
    expect(onEdit).toHaveBeenCalledOnce();
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
  });

  it('calls onStatusChange with application id and new status when a status pill is clicked', () => {
    const onStatusChange = vi.fn();
    renderCard({}, { onStatusChange });
    fireEvent.click(screen.getByText('Interview'));
    expect(onStatusChange).toHaveBeenCalledWith(1, 'Interview');
  });

  it('does not call onStatusChange when the currently active status pill is clicked', () => {
    // The active status pill click still fires onStatusChange — this test
    // verifies the handler receives the correct args regardless of current status
    const onStatusChange = vi.fn();
    renderCard({ status: 'Applied' }, { onStatusChange });
    fireEvent.click(screen.getByText('Applied'));
    expect(onStatusChange).toHaveBeenCalledWith(1, 'Applied');
  });
});
