import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Filter,
  SortAsc,
  Briefcase,
  MapPin,
  DollarSign,
  Calendar,
  Clock,
  Home,
  Plus,
  Download
} from 'lucide-react';
import { api } from '../services/api';

function AllApplications() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [filteredApps, setFilteredApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date_applied');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    fetchApplications();
  }, []);

  useEffect(() => {
    filterAndSortApplications();
  }, [applications, searchQuery, statusFilter, sortBy, sortOrder]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const data = await api.getApplications();
      setApplications(data);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortApplications = () => {
    let filtered = [...applications];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (app) =>
          app.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          app.position_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (app.location && app.location.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((app) => app.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'company':
          aValue = a.company_name.toLowerCase();
          bValue = b.company_name.toLowerCase();
          break;
        case 'position':
          aValue = a.position_title.toLowerCase();
          bValue = b.position_title.toLowerCase();
          break;
        case 'date_applied':
          aValue = new Date(a.date_applied);
          bValue = new Date(b.date_applied);
          break;
        case 'deadline':
          // Get next deadline
          const aDeadline = a.deadlines?.find((d) => !d.is_completed);
          const bDeadline = b.deadlines?.find((d) => !d.is_completed);
          aValue = aDeadline ? new Date(aDeadline.deadline_date) : new Date('2100-01-01');
          bValue = bDeadline ? new Date(bDeadline.deadline_date) : new Date('2100-01-01');
          break;
        default:
          aValue = a.date_applied;
          bValue = b.date_applied;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredApps(filtered);
  };

  const handleExport = async () => {
    try {
      const blob = await api.exportToExcel();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'applications.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export:', error);
    }
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

  const getNextDeadline = (app) => {
    if (!app.deadlines || app.deadlines.length === 0) return null;
    const upcoming = app.deadlines
      .filter((d) => !d.is_completed)
      .sort((a, b) => new Date(a.deadline_date) - new Date(b.deadline_date))[0];
    return upcoming;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getDaysUntilDeadline = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline.deadline_date);
    return Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
  };

  return (
    <div className="min-vh-100" style={{ backgroundColor: 'var(--dark-primary)' }}>
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky-top"
        style={{ backgroundColor: 'var(--header-bg)', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}
      >
        <div className="container-fluid py-3">
          <div className="row align-items-center">
            <div className="col-md-4">
              <h2 className="mb-0" style={{ color: 'var(--text-light)' }}>
                <Briefcase className="me-2" size={28} />
                All Applications
              </h2>
            </div>
            <div className="col-md-8 d-flex justify-content-end gap-2 mt-2 mt-md-0">
              <button className="btn btn-outline-light btn-sm" onClick={() => navigate('/')}>
                <Home size={18} className="me-1" />
                Home
              </button>
              <button className="btn btn-outline-light btn-sm" onClick={handleExport}>
                <Download size={18} className="me-1" />
                Export
              </button>
              <button
                className="btn btn-sm"
                style={{
                  backgroundColor: 'var(--dark-accent)',
                  color: 'var(--dark-primary)',
                  fontWeight: 'bold',
                }}
                onClick={() => navigate('/')}
              >
                <Plus size={18} className="me-1" />
                Add New
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="container-fluid py-4">
        {/* Filters and Search */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="card mb-4"
          style={{ backgroundColor: 'var(--card-bg)' }}
        >
          <div className="card-body">
            <div className="row g-3">
              {/* Search */}
              <div className="col-md-4">
                <label className="form-label" style={{ color: 'var(--text-light)' }}>
                  <Search size={16} className="me-1" />
                  Search
                </label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Company, position, location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    backgroundColor: 'var(--dark-secondary)',
                    borderColor: 'var(--dark-tertiary)',
                    color: 'var(--text-light)',
                  }}
                />
              </div>

              {/* Status Filter */}
              <div className="col-md-3">
                <label className="form-label" style={{ color: 'var(--text-light)' }}>
                  <Filter size={16} className="me-1" />
                  Status
                </label>
                <select
                  className="form-select"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    backgroundColor: 'var(--dark-secondary)',
                    borderColor: 'var(--dark-tertiary)',
                    color: 'var(--text-light)',
                  }}
                >
                  <option value="all">All Statuses</option>
                  <option value="Applied">Applied</option>
                  <option value="Pending Interview">Pending Interview</option>
                  <option value="Interview">Interview</option>
                  <option value="Interview Scheduled">Interview Scheduled</option>
                  <option value="Offer">Offer</option>
                  <option value="Offer Received">Offer Received</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>

              {/* Sort By */}
              <div className="col-md-3">
                <label className="form-label" style={{ color: 'var(--text-light)' }}>
                  <SortAsc size={16} className="me-1" />
                  Sort By
                </label>
                <select
                  className="form-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  style={{
                    backgroundColor: 'var(--dark-secondary)',
                    borderColor: 'var(--dark-tertiary)',
                    color: 'var(--text-light)',
                  }}
                >
                  <option value="date_applied">Date Applied</option>
                  <option value="company">Company</option>
                  <option value="position">Position</option>
                  <option value="deadline">Next Deadline</option>
                </select>
              </div>

              {/* Sort Order */}
              <div className="col-md-2">
                <label className="form-label" style={{ color: 'var(--text-light)' }}>
                  Order
                </label>
                <select
                  className="form-select"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                  style={{
                    backgroundColor: 'var(--dark-secondary)',
                    borderColor: 'var(--dark-tertiary)',
                    color: 'var(--text-light)',
                  }}
                >
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>
              </div>
            </div>

            <div className="mt-3">
              <small style={{ color: 'var(--text-muted)' }}>
                Showing {filteredApps.length} of {applications.length} applications
              </small>
            </div>
          </div>
        </motion.div>

        {/* Applications List */}
        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border" style={{ color: 'var(--dark-accent)' }} role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-3" style={{ color: 'var(--text-muted)' }}>
              Loading applications...
            </p>
          </div>
        ) : filteredApps.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card"
            style={{ backgroundColor: 'var(--card-bg)' }}
          >
            <div className="card-body text-center py-5">
              <Briefcase size={64} style={{ color: 'var(--text-muted)' }} />
              <h5 className="mt-3" style={{ color: 'var(--text-light)' }}>
                No Applications Found
              </h5>
              <p style={{ color: 'var(--text-muted)' }}>
                {searchQuery || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Start by adding your first job application'}
              </p>
              {!searchQuery && statusFilter === 'all' && (
                <button
                  className="btn btn-pill mt-3"
                  style={{
                    backgroundColor: 'var(--dark-accent)',
                    color: 'var(--dark-primary)',
                  }}
                  onClick={() => navigate('/')}
                >
                  <Plus size={18} className="me-1" />
                  Add Application
                </button>
              )}
            </div>
          </motion.div>
        ) : (
          <AnimatePresence>
            {filteredApps.map((app, index) => {
              const nextDeadline = getNextDeadline(app);
              const daysUntil = nextDeadline ? getDaysUntilDeadline(nextDeadline) : null;

              return (
                <motion.div
                  key={app.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.02 }}
                  className="card mb-3"
                  style={{
                    backgroundColor: 'var(--card-bg)',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                  }}
                  onClick={() => navigate(`/job/${app.id}`)}
                  whileHover={{
                    scale: 1.01,
                    boxShadow: '0 8px 16px rgba(0,0,0,0.3)',
                  }}
                >
                  <div className="card-body">
                    <div className="row align-items-center">
                      {/* Company & Position */}
                      <div className="col-md-4">
                        <h5 className="mb-1" style={{ color: 'var(--text-light)' }}>
                          {app.position_title}
                        </h5>
                        <p className="mb-1" style={{ color: 'var(--dark-accent)' }}>
                          <Briefcase size={16} className="me-1" />
                          {app.company_name}
                        </p>
                        <div className="d-flex flex-wrap gap-2 mt-2">
                          {app.location && (
                            <small style={{ color: 'var(--text-muted)' }}>
                              <MapPin size={14} className="me-1" />
                              {app.location}
                            </small>
                          )}
                          {app.salary && (
                            <small style={{ color: 'var(--text-muted)' }}>
                              <DollarSign size={14} className="me-1" />
                              {app.salary}
                            </small>
                          )}
                        </div>
                      </div>

                      {/* Status & Date */}
                      <div className="col-md-3 mt-2 mt-md-0">
                        <span
                          className={`badge bg-${getStatusBadgeClass(app.status)} px-3 py-2 mb-2`}
                        >
                          {app.status}
                        </span>
                        <div>
                          <small style={{ color: 'var(--text-muted)' }}>
                            <Calendar size={14} className="me-1" />
                            Applied: {formatDate(app.date_applied)}
                          </small>
                        </div>
                      </div>

                      {/* Deadline */}
                      <div className="col-md-3 mt-2 mt-md-0">
                        {nextDeadline ? (
                          <div>
                            <div
                              className={`badge ${
                                daysUntil < 0
                                  ? 'bg-danger'
                                  : daysUntil <= 3
                                  ? 'bg-warning'
                                  : 'bg-info'
                              } px-3 py-2 mb-2`}
                            >
                              <Clock size={14} className="me-1" />
                              {daysUntil < 0
                                ? 'Overdue'
                                : daysUntil === 0
                                ? 'Today'
                                : daysUntil === 1
                                ? 'Tomorrow'
                                : `${daysUntil} days`}
                            </div>
                            <div>
                              <small style={{ color: 'var(--text-muted)' }}>
                                {nextDeadline.deadline_type}
                              </small>
                              <br />
                              <small style={{ color: 'var(--text-light)' }}>
                                {formatDate(nextDeadline.deadline_date)}
                              </small>
                            </div>
                          </div>
                        ) : (
                          <small style={{ color: 'var(--text-muted)' }}>No deadlines set</small>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="col-md-2 text-md-end mt-2 mt-md-0">
                        <div className="d-flex flex-column gap-1">
                          {app.notes && app.notes.length > 0 && (
                            <small style={{ color: 'var(--text-muted)' }}>
                              📝 {app.notes.length} note{app.notes.length > 1 ? 's' : ''}
                            </small>
                          )}
                          {app.deadlines && app.deadlines.length > 0 && (
                            <small style={{ color: 'var(--text-muted)' }}>
                              📅 {app.deadlines.length} deadline{app.deadlines.length > 1 ? 's' : ''}
                            </small>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}

export default AllApplications;
