# Deadlines and AI Thoughts Feature Documentation

## Overview

Enhanced the Job Tracker with two major features:
1. **Multiple Deadlines per Application** - Track different stages (application, interview, assessment, etc.)
2. **AI Strategic Advice** - GPT-4 generates personalized advice on how to stand out

## New Features

### 1. Multiple Deadlines

Instead of a single deadline per application, you can now track multiple deadlines for different stages:

**Deadline Types:**
- `application` - Application submission deadline
- `interview` - Interview scheduled date
- `assessment` - Technical assessment or test deadline
- `follow_up` - Follow-up or callback deadline
- `decision` - Expected decision date
- `offer_response` - Offer acceptance deadline
- Custom types as needed

**Deadline Properties:**
- Type (category)
- Date/time
- Description (optional notes)
- Completion status (mark as done)
- Automatic activity logging

### 2. AI Thoughts (Strategic Advice)

GPT-4 now generates strategic advice for each job, including:
- What makes a strong candidate stand out
- Key skills or experiences to emphasize
- How to tailor your application/CV
- Red flags or challenges to be aware of

This is automatically generated during scraping and stored with job details.

## Database Schema Changes

### New Table: `deadlines`

```sql
CREATE TABLE deadlines (
    id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL,
    deadline_type VARCHAR(50) NOT NULL,
    deadline_date DATETIME NOT NULL,
    description TEXT,
    is_completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);
```

### Updated Table: `job_details`

Added field:
- `ai_thoughts TEXT` - AI-generated strategic advice

## API Endpoints

### Deadline Management

#### Get All Deadlines for Application
```http
GET /applications/{application_id}/deadlines
```

Response:
```json
[
  {
    "id": 1,
    "application_id": 1,
    "deadline_type": "application",
    "deadline_date": "2025-01-15T23:59:59",
    "description": "Submit application online",
    "is_completed": false,
    "created_at": "2025-01-01T10:00:00",
    "updated_at": "2025-01-01T10:00:00"
  },
  {
    "id": 2,
    "application_id": 1,
    "deadline_type": "interview",
    "deadline_date": "2025-01-20T14:00:00",
    "description": "Technical interview with team lead",
    "is_completed": false,
    "created_at": "2025-01-10T15:30:00",
    "updated_at": "2025-01-10T15:30:00"
  }
]
```

#### Create Deadline
```http
POST /applications/{application_id}/deadlines
Content-Type: application/json

{
  "deadline_type": "interview",
  "deadline_date": "2025-01-20T14:00:00",
  "description": "Technical interview with team lead",
  "is_completed": false
}
```

#### Update Deadline
```http
PUT /deadlines/{deadline_id}
Content-Type: application/json

{
  "is_completed": true,
  "description": "Interview completed - went well!"
}
```

#### Delete Deadline
```http
DELETE /deadlines/{deadline_id}
```

### Enhanced Scraping Response

The `/scrape` endpoint now returns additional fields:

```http
POST /scrape
Content-Type: application/json

{
  "url": "https://example.com/job-posting"
}
```

Response includes:
```json
{
  "company_name": "TechCorp",
  "position_title": "Senior Software Engineer",
  "location": "London, UK",
  "salary": "£70,000 - £90,000",
  "description": "...",
  "requirements": "...",
  "clean_text_content": "...",
  "application_deadline": "2025-02-01",
  "ai_thoughts": "To stand out for this role, emphasize your experience with distributed systems and cloud architecture. The company values candidates who can demonstrate both technical depth and leadership skills. Tailor your CV to highlight specific projects where you've scaled systems or mentored junior developers. Be aware that the role requires on-call availability, so consider how to address your flexibility during interviews."
}
```

### Enhanced Application Response

Applications now include deadlines:
```json
{
  "id": 1,
  "company_name": "TechCorp",
  "position_title": "Software Engineer",
  "status": "Interview",
  "deadlines": [
    {
      "deadline_type": "application",
      "deadline_date": "2025-01-15T23:59:59",
      "is_completed": true
    },
    {
      "deadline_type": "interview",
      "deadline_date": "2025-01-20T14:00:00",
      "is_completed": false
    }
  ],
  "job_details": {
    "description": "...",
    "requirements": "...",
    "ai_thoughts": "Strategic advice from GPT-4..."
  },
  "notes": [...],
  "activities": [...]
}
```

## Frontend Integration

### Deadlines UI Components

**Deadline List:**
```jsx
// Display deadlines sorted by date
{application.deadlines.map(deadline => (
  <DeadlineCard
    key={deadline.id}
    type={deadline.deadline_type}
    date={deadline.deadline_date}
    description={deadline.description}
    isCompleted={deadline.is_completed}
    onToggleComplete={() => toggleDeadline(deadline.id)}
    onDelete={() => deleteDeadline(deadline.id)}
  />
))}
```

**Add Deadline Form:**
```jsx
<DeadlineForm
  applicationId={application.id}
  onSubmit={async (data) => {
    await api.post(`/applications/${application.id}/deadlines`, data);
  }}
/>
```

### AI Thoughts Display

**Strategic Advice Section:**
```jsx
{application.job_details?.ai_thoughts && (
  <AIThoughtsCard>
    <h3>Strategic Advice</h3>
    <p>{application.job_details.ai_thoughts}</p>
  </AIThoughtsCard>
)}
```

## Usage Examples

### Example 1: Application with Multiple Deadlines

```javascript
// User applies to a job
POST /applications
{
  "company_name": "Google",
  "position_title": "SWE",
  "status": "Applied"
}
// Returns: { id: 1, ... }

// Add application deadline
POST /applications/1/deadlines
{
  "deadline_type": "application",
  "deadline_date": "2025-01-31T23:59:59",
  "description": "Submit via careers portal"
}

// Later: Interview scheduled
POST /applications/1/deadlines
{
  "deadline_type": "interview",
  "deadline_date": "2025-02-10T10:00:00",
  "description": "Phone screen with recruiter"
}

// Mark application deadline as completed
PUT /deadlines/1
{
  "is_completed": true
}

// Technical assessment received
POST /applications/1/deadlines
{
  "deadline_type": "assessment",
  "deadline_date": "2025-02-15T17:00:00",
  "description": "Complete coding challenge"
}
```

### Example 2: Using AI Thoughts

```javascript
// Scrape a job posting
POST /scrape
{
  "url": "https://company.com/jobs/123"
}

// Response includes ai_thoughts
{
  "company_name": "Startup Inc",
  "position_title": "Full Stack Developer",
  "ai_thoughts": "This startup values speed and ownership. Highlight projects where you've built features end-to-end. They use React and Node.js heavily, so emphasize experience with modern JavaScript. The job mentions 'fast-paced environment' - be prepared to discuss handling ambiguity and rapid iteration. Consider mentioning any startup or small team experience."
}

// Create application with job details
POST /applications
{ ... }
// Then add job details with AI thoughts
POST /applications/{id}/job-details
{
  "description": "...",
  "requirements": "...",
  "ai_thoughts": "..." // from scrape response
}
```

## Activity Logging

All deadline actions are automatically logged:

**Activity Types:**
- `deadline_added` - New deadline created
- `deadline_completed` - Deadline marked as done
- `deadline_reopened` - Completed deadline unmarked
- `deadline_deleted` - Deadline removed

View activity log:
```http
GET /applications/{id}/activities
```

## Deadline Types Reference

Suggested deadline types and their use cases:

| Type | Use Case | Example |
|------|----------|---------|
| `application` | Application submission | "Submit online application by Feb 1st" |
| `interview` | Any interview stage | "Phone screen on Feb 10th at 2pm" |
| `assessment` | Technical tests, assignments | "Complete coding challenge by Feb 15th" |
| `follow_up` | Follow-up reminders | "Send thank you email by Feb 11th" |
| `decision` | Expected decision date | "Should hear back by Feb 20th" |
| `offer_response` | Offer acceptance deadline | "Accept/decline offer by Feb 28th" |
| `custom` | Other important dates | Any other milestone |

## Migration Notes

### Existing Applications

Old applications will continue to work:
- Legacy single `deadline` field still exists in `applications` table
- New `deadlines` table provides multiple deadline support
- Frontend can display both for backward compatibility

### Upgrading Workflow

1. Database will automatically create `deadlines` table on startup
2. `ai_thoughts` column added to `job_details` table
3. Old applications won't have AI thoughts (field will be null)
4. Can manually add AI thoughts by updating job details

## Best Practices

### Deadline Management

1. **Be Specific** - Include time and description
2. **Mark as Complete** - Helps track progress
3. **Set Reminders** - Add follow-up deadlines
4. **Don't Duplicate** - Use activity log for notes instead

### AI Thoughts Usage

1. **Read Carefully** - AI advice is based on job posting analysis
2. **Customize** - Use as a starting point, adapt to your situation
3. **Update If Needed** - Can manually edit via job details update
4. **Re-scrape** - If posting updated, scrape again for fresh insights

## Frontend TODO

To fully integrate these features:

1. **Deadline Components**
   - [ ] Deadline list component
   - [ ] Add deadline form/modal
   - [ ] Edit deadline dialog
   - [ ] Deadline completion toggle
   - [ ] Upcoming deadlines dashboard widget

2. **AI Thoughts Display**
   - [ ] Expandable AI advice card
   - [ ] Show/hide toggle
   - [ ] Copy to clipboard button
   - [ ] Markdown formatting support

3. **Timeline View**
   - [ ] Visual timeline of all deadlines
   - [ ] Color-coded by type
   - [ ] Overdue indicator
   - [ ] Calendar integration

4. **Notifications**
   - [ ] Upcoming deadline alerts
   - [ ] Browser notifications
   - [ ] Email reminders (future)

## Testing

### Test Deadline CRUD

```bash
# Get application deadlines
curl http://localhost:8000/applications/1/deadlines

# Create deadline
curl -X POST http://localhost:8000/applications/1/deadlines \
  -H "Content-Type: application/json" \
  -d '{
    "deadline_type": "interview",
    "deadline_date": "2025-02-01T14:00:00",
    "description": "Technical interview"
  }'

# Update deadline
curl -X PUT http://localhost:8000/deadlines/1 \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'

# Delete deadline
curl -X DELETE http://localhost:8000/deadlines/1
```

### Test Scraping with AI Thoughts

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/job"}'
```

Check response includes `ai_thoughts` and `application_deadline` fields.

## FAQ

**Q: Can I have multiple deadlines of the same type?**
A: Yes! You can have multiple interviews, assessments, etc.

**Q: What if the scraper doesn't find a deadline?**
A: `application_deadline` will be null. You can manually add deadlines anytime.

**Q: Can I edit AI thoughts?**
A: Yes, via the job details update endpoint. AI thoughts are just a text field.

**Q: Do deadlines send notifications?**
A: Not yet - that's a frontend feature to implement.

**Q: What happens to deadlines when I delete an application?**
A: They're automatically deleted (cascade delete).

## Summary

These features provide:
- ✅ Multiple deadline tracking per application
- ✅ Different deadline types for various stages
- ✅ Completion status tracking
- ✅ AI-generated strategic advice
- ✅ Automatic activity logging
- ✅ Full CRUD API for deadline management
- ✅ Enhanced scraping with deadline extraction

All backend work is complete and ready for frontend integration!
