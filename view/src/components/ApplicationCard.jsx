import { ExternalLink, Trash2, Edit2 } from 'lucide-react';

export const ApplicationCard = ({ application, statusColumns, onEdit, onDelete, onStatusChange }) => {
  const currentStatusColor = statusColumns.find(s => s.id === application.status)?.bgColor || 'bg-secondary';
  
  return (
    <div className="application-card">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <h6 className="card-title mb-0">{application.position_title}</h6>
          <div className="btn-group btn-group-sm">
            <button
              onClick={() => onEdit(application)}
              className="btn btn-outline-primary"
              title="Edit application"
            >
              <Edit2 size={14} />
            </button>
            <button
              onClick={() => onDelete(application.id)}
              className="btn btn-outline-danger"
              title="Delete application"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        <p className="card-text text-muted mb-2">{application.company_name}</p>

        {application.location && (
          <p className="card-text small mb-2">
            <i className="bi bi-geo-alt"></i> {application.location}
          </p>
        )}

        {application.salary && (
          <p className="card-text small fw-bold mb-2" style={{ color: '#4CAF50' }}>{application.salary}</p>
        )}

        <div className="d-flex flex-wrap gap-1 mb-2">
          {statusColumns.map((status) => (
            <button
              key={status.id}
              onClick={() => onStatusChange(application.id, status.id)}
              className={`btn btn-sm btn-status-pill ${
                application.status === status.id
                  ? 'btn-status-active'
                  : 'btn-status-inactive'
              }`}
            >
              {status.id}
            </button>
          ))}
        </div>

        {application.job_url && (
          <a
            href={application.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm btn-link p-0 text-decoration-none"
          >
            <ExternalLink size={12} className="me-1" />
            View Job
          </a>
        )}
      </div>
    </div>
  );
};