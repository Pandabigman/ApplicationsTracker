/**
 * MSW (Mock Service Worker) request handlers.
 *
 * These intercept fetch() calls at the network boundary, so api.js runs for
 * real and components see genuine Response objects (including loading states
 * and error shapes). Individual tests can override specific handlers with
 * server.use(...) for scenario-specific behaviour.
 */
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const API = 'http://localhost:8000';

// Default application fixture
export const FIXTURE_APP = {
  id: 1,
  company_name: 'Stripe',
  position_title: 'Staff Engineer',
  location: 'Remote',
  salary: '$200k',
  status: 'Applied',
  job_url: 'https://stripe.com/jobs/1',
  date_applied: '2026-01-15T10:00:00Z',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  notes: [],
  activities: [
    {
      id: 1,
      application_id: 1,
      activity_type: 'application_created',
      description: 'Applied to Staff Engineer at Stripe',
      old_value: null,
      new_value: 'Applied',
      created_at: '2026-01-15T10:00:00Z',
    },
  ],
  deadlines: [],
  job_details: null,
};

// Default handlers — minimal happy-path responses
export const handlers = [
  // Applications
  http.get(`${API}/applications`, () => {
    return HttpResponse.json([FIXTURE_APP]);
  }),

  http.get(`${API}/applications/:id`, ({ params }) => {
    if (params.id === '1') return HttpResponse.json(FIXTURE_APP);
    return HttpResponse.json({ detail: 'Application not found' }, { status: 404 });
  }),

  http.post(`${API}/applications`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: 99,
        ...body,
        status: body.status || 'Applied',
        date_applied: '2026-02-01T10:00:00Z',
        created_at: '2026-02-01T10:00:00Z',
        updated_at: '2026-02-01T10:00:00Z',
        notes: [],
        activities: [],
        deadlines: [],
        job_details: null,
      },
      { status: 201 }
    );
  }),

  http.put(`${API}/applications/:id`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({ ...FIXTURE_APP, id: Number(params.id), ...body });
  }),

  http.delete(`${API}/applications/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Job details
  http.post(`${API}/applications/:id/job-details`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: 1,
        application_id: Number(params.id),
        ...body,
        created_at: '2026-02-01T10:00:00Z',
        updated_at: '2026-02-01T10:00:00Z',
      },
      { status: 201 }
    );
  }),

  http.put(`${API}/applications/:id/job-details`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: 1,
      application_id: Number(params.id),
      ...body,
      created_at: '2026-02-01T10:00:00Z',
      updated_at: '2026-02-01T10:00:00Z',
    });
  }),

  // Notes
  http.get(`${API}/applications/:id/notes`, () => {
    return HttpResponse.json([]);
  }),

  http.post(`${API}/applications/:id/notes`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: 1,
        application_id: Number(params.id),
        content: body.content,
        created_at: '2026-02-01T10:00:00Z',
        updated_at: '2026-02-01T10:00:00Z',
      },
      { status: 201 }
    );
  }),

  http.put(`${API}/notes/:id`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: Number(params.id),
      application_id: 1,
      content: body.content,
      created_at: '2026-02-01T10:00:00Z',
      updated_at: '2026-02-01T10:00:00Z',
    });
  }),

  http.delete(`${API}/notes/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Deadlines
  http.get(`${API}/applications/:id/deadlines`, () => {
    return HttpResponse.json([]);
  }),

  http.post(`${API}/applications/:id/deadlines`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: 1,
        application_id: Number(params.id),
        ...body,
        is_completed: false,
        created_at: '2026-02-01T10:00:00Z',
        updated_at: '2026-02-01T10:00:00Z',
      },
      { status: 201 }
    );
  }),

  http.put(`${API}/deadlines/:id`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: Number(params.id),
      application_id: 1,
      deadline_type: 'Interview',
      deadline_date: '2026-06-01T10:00:00Z',
      is_completed: false,
      ...body,
      created_at: '2026-02-01T10:00:00Z',
      updated_at: '2026-02-01T10:00:00Z',
    });
  }),

  http.delete(`${API}/deadlines/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Activities
  http.get(`${API}/applications/:id/activities`, () => {
    return HttpResponse.json([]);
  }),

  // Scraping
  http.post(`${API}/scrape`, () => {
    return HttpResponse.json({
      company_name: 'MockedCorp',
      position_title: 'Mocked Engineer',
      location: 'London',
      salary: '£90k',
      description: 'Mocked job description',
      requirements: 'Python, React',
      ai_thoughts: 'Focus on impact metrics',
      application_deadline: null,
      job_url: 'https://jobs.mocked.com/1',
      clean_text_content: 'Mocked clean text',
    });
  }),

  // Key validation
  http.post(`${API}/validate-key`, () => {
    return HttpResponse.json({ valid: true });
  }),

  // Export
  http.get(`${API}/export/excel`, () => {
    return new HttpResponse(new Blob(['fake xlsx content']), {
      headers: {
        'Content-Type':
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=applications.xlsx',
      },
    });
  }),
];

export const server = setupServer(...handlers);
