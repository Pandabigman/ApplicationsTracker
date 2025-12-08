import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Briefcase,
  MapPin,
  DollarSign,
  Calendar,
  Clock,
  ExternalLink,
  Edit,
  Trash2,
  Plus,
  CheckCircle,
  Circle,
  Lightbulb,
  FileText,
  Activity,
  Save,
  X
} from 'lucide-react';
import { api } from '../services/api';

function JobDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Edit states
  const [isEditingStatus, setIsEditingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState('');

  // Note states
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [editingNote, setEditingNote] = useState(null);

  // Deadline states
  const [showDeadlineForm, setShowDeadlineForm] = useState(false);
  const [newDeadline, setNewDeadline] = useState({
    deadline_type: 'application',
    deadline_date: '',
    description: '',
  });
  const [editingDeadline, setEditingDeadline] = useState(null);

  useEffect(() => {
    fetchApplication();
  }, [id]);

  const fetchApplication = async () => {
    try {
      setLoading(true);
      const data = await api.getApplication(id);
      setApplication(data);
      setNewStatus(data.status);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async () => {
    try {
      await api.updateApplication(id, { status: newStatus });
      setIsEditingStatus(false);
      fetchApplication();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleDeleteApplication = async () => {
    if (!confirm('Are you sure you want to delete this application?')) return;

    try {
      await api.deleteApplication(id);
      navigate('/applications');
    } catch (err) {
      console.error('Failed to delete application:', err);
    }
  };

  // Note handlers
  const handleAddNote = async () => {
    if (!noteContent.trim()) return;

    try {
      await api.createNote(id, noteContent);
      setNoteContent('');
      setShowNoteForm(false);
      fetchApplication();
    } catch (err) {
      console.error('Failed to add note:', err);
    }
  };

  const handleUpdateNote = async (noteId) => {
    if (!noteContent.trim()) return;

    try {
      await api.updateNote(noteId, noteContent);
      setNoteContent('');
      setEditingNote(null);
      fetchApplication();
    } catch (err) {
      console.error('Failed to update note:', err);
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!confirm('Delete this note?')) return;

    try {
      await api.deleteNote(noteId);
      fetchApplication();
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  };

  // Deadline handlers
  const handleAddDeadline = async () => {
    if (!newDeadline.deadline_date) return;

    try {
      await api.createDeadline(id, {
        ...newDeadline,
        deadline_date: new Date(newDeadline.deadline_date).toISOString(),
        is_completed: false,
      });
      setNewDeadline({ deadline_type: 'application', deadline_date: '', description: '' });
      setShowDeadlineForm(false);
      fetchApplication();
    } catch (err) {
      console.error('Failed to add deadline:', err);
    }
  };

  const handleToggleDeadline = async (deadline) => {
    try {
      await api.updateDeadline(deadline.id, { is_completed: !deadline.is_completed });
      fetchApplication();
    } catch (err) {
      console.error('Failed to toggle deadline:', err);
    }
  };

  const handleDeleteDeadline = async (deadlineId) => {
    if (!confirm('Delete this deadline?')) return;

    try {
      await api.deleteDeadline(deadlineId);
      fetchApplication();
    } catch (err) {
      console.error('Failed to delete deadline:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadgeClass = (status) => {
    const statusMap = {
      Applied: 'info',
      'Pending Interview': 'warning',
      Interview: 'warning',
      'Interview Scheduled': 'primary',
      Offer: 'success',
      'Offer Received': 'success',
      Rejected: 'danger',
    };
    return statusMap[status] || 'secondary';
  };

  const getDaysUntilDeadline = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline.deadline_date);
    return Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
  };

  if (loading) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center" style={{ backgroundColor: 'var(--dark-primary)' }}>
        <div className="text-center">
          <div className="spinner-border" style={{ color: 'var(--dark-accent)' }} role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3" style={{ color: 'var(--text-muted)' }}>Loading application...</p>
        </div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center" style={{ backgroundColor: 'var(--dark-primary)' }}>
        <div className="text-center">
          <h3 style={{ color: 'var(--text-light)' }}>Application Not Found</h3>
          <button className="btn btn-outline-light mt-3" onClick={() => navigate('/applications')}>
            Back to Applications
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-vh-100" style={{ backgroundColor: 'var(--dark-primary)' }}>
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={{ backgroundColor: 'var(--header-bg)', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}
      >
        <div className="container-fluid py-3">
          <div className="d-flex justify-content-between align-items-center">
            <button className="btn btn-outline-light" onClick={() => navigate('/applications')}>
              <ArrowLeft size={18} className="me-1" />
              Back to Applications
            </button>
            <button className="btn btn-outline-danger" onClick={handleDeleteApplication}>
              <Trash2 size={18} className="me-1" />
              Delete
            </button>
          </div>
        </div>
      </motion.div>

      <div className="container py-4">
        <div className="row g-4">
          {/* Left Column - Main Info */}
          <div className="col-lg-8">
            {/* Application Header */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="card mb-4"
              style={{ backgroundColor: 'var(--card-bg)' }}
            >
              <div className="card-body">
                <h1 className="mb-3" style={{ color: 'var(--text-light)' }}>
                  {application.position_title}
                </h1>
                <h4 className="mb-3" style={{ color: 'var(--dark-accent)' }}>
                  <Briefcase size={20} className="me-2" />
                  {application.company_name}
                </h4>

                <div className="d-flex flex-wrap gap-3 mb-3">
                  {application.location && (
                    <div style={{ color: 'var(--text-muted)' }}>
                      <MapPin size={16} className="me-1" />
                      {application.location}
                    </div>
                  )}
                  {application.salary && (
                    <div style={{ color: 'var(--text-muted)' }}>
                      <DollarSign size={16} className="me-1" />
                      {application.salary}
                    </div>
                  )}
                  <div style={{ color: 'var(--text-muted)' }}>
                    <Calendar size={16} className="me-1" />
                    Applied: {formatDate(application.date_applied)}
                  </div>
                </div>

                {/* Status */}
                <div className="mb-3">
                  {isEditingStatus ? (
                    <div className="d-flex gap-2">
                      <select
                        className="form-select form-select-sm"
                        style={{ maxWidth: '200px', backgroundColor: 'var(--dark-secondary)', borderColor: 'var(--dark-tertiary)', color: 'var(--text-light)' }}
                        value={newStatus}
                        onChange={(e) => setNewStatus(e.target.value)}
                      >
                        <option value="Applied">Applied</option>
                        <option value="Pending Interview">Pending Interview</option>
                        <option value="Interview">Interview</option>
                        <option value="Interview Scheduled">Interview Scheduled</option>
                        <option value="Offer">Offer</option>
                        <option value="Offer Received">Offer Received</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                      <button className="btn btn-sm btn-success" onClick={handleUpdateStatus}>
                        <Save size={16} />
                      </button>
                      <button className="btn btn-sm btn-secondary" onClick={() => setIsEditingStatus(false)}>
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <div className="d-flex align-items-center gap-2">
                      <span className={`badge bg-${getStatusBadgeClass(application.status)} px-3 py-2`}>
                        {application.status}
                      </span>
                      <button className="btn btn-sm btn-outline-light" onClick={() => setIsEditingStatus(true)}>
                        <Edit size={14} className="me-1" />
                        Change Status
                      </button>
                    </div>
                  )}
                </div>

                {application.job_url && (
                  <a
                    href={application.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-sm btn-outline-light"
                  >
                    <ExternalLink size={16} className="me-1" />
                    View Original Posting
                  </a>
                )}
              </div>
            </motion.div>

            {/* AI Thoughts */}
            {application.job_details?.ai_thoughts && (
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="card mb-4"
                style={{ backgroundColor: 'var(--card-bg)', borderLeft: '4px solid var(--dark-accent)' }}
              >
                <div className="card-body">
                  <h5 className="card-title" style={{ color: 'var(--text-light)' }}>
                    <Lightbulb size={20} className="me-2" style={{ color: 'var(--dark-accent)' }} />
                    AI Strategic Advice
                  </h5>
                  <p style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>
                    {application.job_details.ai_thoughts}
                  </p>
                </div>
              </motion.div>
            )}

            {/* Job Description */}
            {application.job_details?.description && (
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="card mb-4"
                style={{ backgroundColor: 'var(--card-bg)' }}
              >
                <div className="card-body">
                  <h5 className="card-title" style={{ color: 'var(--text-light)' }}>
                    <FileText size={20} className="me-2" />
                    Description
                  </h5>
                  <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                    {application.job_details.description}
                  </p>
                </div>
              </motion.div>
            )}

            {/* Requirements */}
            {application.job_details?.requirements && (
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="card mb-4"
                style={{ backgroundColor: 'var(--card-bg)' }}
              >
                <div className="card-body">
                  <h5 className="card-title" style={{ color: 'var(--text-light)' }}>
                    <CheckCircle size={20} className="me-2" />
                    Requirements
                  </h5>
                  <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                    {application.job_details.requirements}
                  </p>
                </div>
              </motion.div>
            )}

            {/* Activity Log */}
            {application.activities && application.activities.length > 0 && (
              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="card mb-4"
                style={{ backgroundColor: 'var(--card-bg)' }}
              >
                <div className="card-body">
                  <h5 className="card-title" style={{ color: 'var(--text-light)' }}>
                    <Activity size={20} className="me-2" />
                    Activity Log
                  </h5>
                  <div className="mt-3">
                    {application.activities.map((activity, index) => (
                      <div
                        key={activity.id}
                        className="d-flex gap-3 mb-3"
                        style={{ borderLeft: '2px solid var(--dark-tertiary)', paddingLeft: '1rem' }}
                      >
                        <div className="flex-grow-1">
                          <div style={{ color: 'var(--text-light)' }}>{activity.description}</div>
                          <small style={{ color: 'var(--text-muted)' }}>
                            {formatDate(activity.created_at)}
                          </small>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Right Column - Deadlines & Notes */}
          <div className="col-lg-4">
            {/* Deadlines */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="card mb-4"
              style={{ backgroundColor: 'var(--card-bg)' }}
            >
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h5 className="card-title mb-0" style={{ color: 'var(--text-light)' }}>
                    <Clock size={20} className="me-2" />
                    Deadlines
                  </h5>
                  <button
                    className="btn btn-sm btn-outline-light"
                    onClick={() => setShowDeadlineForm(!showDeadlineForm)}
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {showDeadlineForm && (
                  <div className="mb-3 p-3" style={{ backgroundColor: 'var(--dark-secondary)', borderRadius: '8px' }}>
                    <select
                      className="form-select form-select-sm mb-2"
                      value={newDeadline.deadline_type}
                      onChange={(e) => setNewDeadline({ ...newDeadline, deadline_type: e.target.value })}
                      style={{ backgroundColor: 'var(--dark-tertiary)', borderColor: 'var(--dark-tertiary)', color: 'var(--text-light)' }}
                    >
                      <option value="application">Application</option>
                      <option value="interview">Interview</option>
                      <option value="assessment">Assessment</option>
                      <option value="follow_up">Follow Up</option>
                      <option value="decision">Decision</option>
                      <option value="offer_response">Offer Response</option>
                    </select>
                    <input
                      type="datetime-local"
                      className="form-control form-control-sm mb-2"
                      value={newDeadline.deadline_date}
                      onChange={(e) => setNewDeadline({ ...newDeadline, deadline_date: e.target.value })}
                      style={{ backgroundColor: 'var(--dark-tertiary)', borderColor: 'var(--dark-tertiary)', color: 'var(--text-light)' }}
                    />
                    <input
                      type="text"
                      className="form-control form-control-sm mb-2"
                      placeholder="Description (optional)"
                      value={newDeadline.description}
                      onChange={(e) => setNewDeadline({ ...newDeadline, description: e.target.value })}
                      style={{ backgroundColor: 'var(--dark-tertiary)', borderColor: 'var(--dark-tertiary)', color: 'var(--text-light)' }}
                    />
                    <div className="d-flex gap-2">
                      <button className="btn btn-sm btn-success" onClick={handleAddDeadline}>Add</button>
                      <button className="btn btn-sm btn-secondary" onClick={() => setShowDeadlineForm(false)}>Cancel</button>
                    </div>
                  </div>
                )}

                {application.deadlines && application.deadlines.length > 0 ? (
                  <div className="d-flex flex-column gap-2">
                    {application.deadlines
                      .sort((a, b) => new Date(a.deadline_date) - new Date(b.deadline_date))
                      .map((deadline) => {
                        const daysUntil = getDaysUntilDeadline(deadline);
                        return (
                          <div
                            key={deadline.id}
                            className="p-3"
                            style={{
                              backgroundColor: deadline.is_completed
                                ? 'var(--dark-secondary)'
                                : 'var(--dark-tertiary)',
                              borderRadius: '8px',
                              opacity: deadline.is_completed ? 0.6 : 1,
                            }}
                          >
                            <div className="d-flex justify-content-between align-items-start mb-2">
                              <div className="d-flex align-items-center gap-2">
                                <button
                                  className="btn btn-sm p-0"
                                  onClick={() => handleToggleDeadline(deadline)}
                                  style={{ background: 'none', border: 'none', color: 'var(--dark-accent)' }}
                                >
                                  {deadline.is_completed ? (
                                    <CheckCircle size={20} />
                                  ) : (
                                    <Circle size={20} />
                                  )}
                                </button>
                                <div>
                                  <div style={{ color: 'var(--text-light)', textDecoration: deadline.is_completed ? 'line-through' : 'none' }}>
                                    {deadline.deadline_type}
                                  </div>
                                  {!deadline.is_completed && (
                                    <small className={`badge bg-${daysUntil < 0 ? 'danger' : daysUntil <= 3 ? 'warning' : 'info'}`}>
                                      {daysUntil < 0 ? 'Overdue' : daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil} days`}
                                    </small>
                                  )}
                                </div>
                              </div>
                              <button
                                className="btn btn-sm p-0"
                                onClick={() => handleDeleteDeadline(deadline.id)}
                                style={{ background: 'none', border: 'none', color: 'var(--text-muted)' }}
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                            <small style={{ color: 'var(--text-muted)' }}>
                              {new Date(deadline.deadline_date).toLocaleString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </small>
                            {deadline.description && (
                              <div className="mt-1">
                                <small style={{ color: 'var(--text-muted)' }}>{deadline.description}</small>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-muted)' }}>No deadlines set</p>
                )}
              </div>
            </motion.div>

            {/* Notes */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="card"
              style={{ backgroundColor: 'var(--card-bg)' }}
            >
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h5 className="card-title mb-0" style={{ color: 'var(--text-light)' }}>
                    <FileText size={20} className="me-2" />
                    Notes
                  </h5>
                  <button
                    className="btn btn-sm btn-outline-light"
                    onClick={() => {
                      setShowNoteForm(!showNoteForm);
                      setEditingNote(null);
                      setNoteContent('');
                    }}
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {(showNoteForm || editingNote) && (
                  <div className="mb-3">
                    <textarea
                      className="form-control mb-2"
                      rows="3"
                      placeholder="Add a note..."
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      style={{ backgroundColor: 'var(--dark-secondary)', borderColor: 'var(--dark-tertiary)', color: 'var(--text-light)' }}
                    />
                    <div className="d-flex gap-2">
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => (editingNote ? handleUpdateNote(editingNote.id) : handleAddNote())}
                      >
                        {editingNote ? 'Update' : 'Add'}
                      </button>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => {
                          setShowNoteForm(false);
                          setEditingNote(null);
                          setNoteContent('');
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {application.notes && application.notes.length > 0 ? (
                  <div className="d-flex flex-column gap-2">
                    {application.notes.map((note) => (
                      <div
                        key={note.id}
                        className="p-3"
                        style={{ backgroundColor: 'var(--dark-secondary)', borderRadius: '8px' }}
                      >
                        <p style={{ color: 'var(--text-light)', marginBottom: '0.5rem', whiteSpace: 'pre-wrap' }}>
                          {note.content}
                        </p>
                        <div className="d-flex justify-content-between align-items-center">
                          <small style={{ color: 'var(--text-muted)' }}>
                            {new Date(note.created_at).toLocaleString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </small>
                          <div className="d-flex gap-2">
                            <button
                              className="btn btn-sm p-0"
                              onClick={() => {
                                setEditingNote(note);
                                setNoteContent(note.content);
                                setShowNoteForm(false);
                              }}
                              style={{ background: 'none', border: 'none', color: 'var(--text-muted)' }}
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              className="btn btn-sm p-0"
                              onClick={() => handleDeleteNote(note.id)}
                              style={{ background: 'none', border: 'none', color: 'var(--text-muted)' }}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-muted)' }}>No notes yet</p>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JobDetail;
