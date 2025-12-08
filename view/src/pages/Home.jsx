import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Loader2, Calendar, Briefcase, Clock, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

function Home() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [upcomingDeadlines, setUpcomingDeadlines] = useState([]);
  const [loadingDeadlines, setLoadingDeadlines] = useState(true);

  // Fetch applications with upcoming deadlines on mount
  useEffect(() => {
    fetchUpcomingDeadlines();
  }, []);

  const fetchUpcomingDeadlines = async () => {
    try {
      setLoadingDeadlines(true);
      const applications = await api.getApplications();

      // Get all applications with deadlines
      const appsWithDeadlines = applications
        .filter(app => app.deadlines && app.deadlines.length > 0)
        .map(app => {
          // Find the next uncompleted deadline
          const nextDeadline = app.deadlines
            .filter(d => !d.is_completed)
            .sort((a, b) => new Date(a.deadline_date) - new Date(b.deadline_date))[0];

          return nextDeadline ? { ...app, nextDeadline } : null;
        })
        .filter(app => app !== null)
        .sort((a, b) => new Date(a.nextDeadline.deadline_date) - new Date(b.nextDeadline.deadline_date))
        .slice(0, 10); // Top 10

      setUpcomingDeadlines(appsWithDeadlines);
    } catch (err) {
      console.error('Failed to fetch deadlines:', err);
    } finally {
      setLoadingDeadlines(false);
    }
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a job URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const jobData = await api.scrapeUrl(url);

      // Create application with scraped data
      const newApp = await api.createApplication({
        company_name: jobData.company_name,
        position_title: jobData.position_title,
        location: jobData.location,
        salary: jobData.salary,
        job_url: jobData.job_url || url,
        status: 'Applied',
      });

      // Add job details if available
      if (jobData.description || jobData.requirements || jobData.ai_thoughts) {
        await api.createJobDetails(newApp.id, {
          description: jobData.description,
          requirements: jobData.requirements,
          clean_text_content: jobData.clean_text_content,
          ai_thoughts: jobData.ai_thoughts,
        });
      }

      // Add application deadline if found
      if (jobData.application_deadline) {
        try {
          await api.createDeadline(newApp.id, {
            deadline_type: 'application',
            deadline_date: new Date(jobData.application_deadline).toISOString(),
            description: 'Application deadline',
            is_completed: false,
          });
        } catch (err) {
          console.error('Failed to create deadline:', err);
        }
      }

      // Navigate to the job detail page
      navigate(`/job/${newApp.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getDeadlineStatus = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline.deadline_date);
    const daysUntil = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));

    if (daysUntil < 0) return { text: 'Overdue', class: 'danger' };
    if (daysUntil === 0) return { text: 'Today', class: 'warning' };
    if (daysUntil === 1) return { text: 'Tomorrow', class: 'warning' };
    if (daysUntil <= 3) return { text: `${daysUntil} days`, class: 'warning' };
    if (daysUntil <= 7) return { text: `${daysUntil} days`, class: 'info' };
    return { text: `${daysUntil} days`, class: 'success' };
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-vh-100" style={{ backgroundColor: 'var(--dark-primary)' }}>
      {/* Hero Section */}
      <motion.div
        className="container py-5"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        <motion.div className="text-center mb-5" variants={itemVariants}>
          <h1 className="display-4 fw-bold mb-3" style={{ color: 'var(--text-light)' }}>
            <Briefcase className="me-3" size={48} style={{ color: 'var(--dark-accent)' }} />
            Job Application Tracker
          </h1>
          <p className="lead" style={{ color: 'var(--text-muted)' }}>
            Track your job applications, manage deadlines, and never miss an opportunity
          </p>
        </motion.div>

        {/* URL Scraper - Prominent Section */}
        <motion.div variants={itemVariants}>
          <div
            className="card mx-auto shadow-lg"
            style={{
              maxWidth: '800px',
              backgroundColor: 'var(--card-bg)',
              border: '2px solid var(--dark-accent)'
            }}
          >
            <div className="card-body p-4">
              <h3 className="card-title text-center mb-4" style={{ color: 'var(--text-light)' }}>
                <Search className="me-2" size={28} />
                Add New Job Application
              </h3>

              <form onSubmit={handleScrape}>
                <div className="input-group input-group-lg mb-3">
                  <span
                    className="input-group-text"
                    style={{
                      backgroundColor: 'var(--dark-secondary)',
                      borderColor: 'var(--dark-tertiary)',
                      color: 'var(--text-muted)'
                    }}
                  >
                    <Search size={20} />
                  </span>
                  <input
                    type="url"
                    className="form-control"
                    placeholder="Paste job posting URL here..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                    style={{
                      backgroundColor: 'var(--dark-secondary)',
                      borderColor: 'var(--dark-tertiary)',
                      color: 'var(--text-light)'
                    }}
                  />
                  <button
                    type="submit"
                    className="btn btn-lg"
                    disabled={loading}
                    style={{
                      backgroundColor: 'var(--dark-accent)',
                      borderColor: 'var(--dark-accent)',
                      color: 'var(--dark-primary)',
                      fontWeight: 'bold',
                      minWidth: '150px'
                    }}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spinner-border-sm me-2" size={20} />
                        Scraping...
                      </>
                    ) : (
                      <>
                        <Search className="me-2" size={20} />
                        Scrape Job
                      </>
                    )}
                  </button>
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="alert alert-danger"
                  >
                    {error}
                  </motion.div>
                )}
              </form>

              <div className="text-center">
                <small className="text-muted">
                  AI-powered scraping extracts company, position, requirements, and provides strategic advice
                </small>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Upcoming Deadlines Section */}
        <motion.div className="mt-5" variants={itemVariants}>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h3 style={{ color: 'var(--text-light)' }}>
              <Calendar className="me-2" size={28} />
              Upcoming Deadlines
            </h3>
            <button
              className="btn btn-outline-light btn-pill"
              onClick={() => navigate('/applications')}
            >
              View All Applications
              <ArrowRight className="ms-2" size={18} />
            </button>
          </div>

          {loadingDeadlines ? (
            <div className="text-center py-5">
              <Loader2 className="spinner-border" size={48} style={{ color: 'var(--dark-accent)' }} />
              <p className="mt-3" style={{ color: 'var(--text-muted)' }}>Loading deadlines...</p>
            </div>
          ) : upcomingDeadlines.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card shadow-sm"
              style={{ backgroundColor: 'var(--card-bg)' }}
            >
              <div className="card-body text-center py-5">
                <Clock size={64} style={{ color: 'var(--text-muted)' }} />
                <h5 className="mt-3" style={{ color: 'var(--text-light)' }}>No Upcoming Deadlines</h5>
                <p style={{ color: 'var(--text-muted)' }}>
                  Add job applications with deadlines to track them here
                </p>
              </div>
            </motion.div>
          ) : (
            <div className="row g-3">
              {upcomingDeadlines.map((app, index) => {
                const deadlineStatus = getDeadlineStatus(app.nextDeadline);
                return (
                  <motion.div
                    key={app.id}
                    className="col-12"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div
                      className="card shadow-sm h-100 cursor-pointer"
                      style={{ backgroundColor: 'var(--card-bg)', cursor: 'pointer' }}
                      onClick={() => navigate(`/job/${app.id}`)}
                    >
                      <div className="card-body">
                        <div className="row align-items-center">
                          <div className="col-md-6">
                            <h5 className="mb-1" style={{ color: 'var(--text-light)' }}>
                              {app.position_title}
                            </h5>
                            <p className="mb-1" style={{ color: 'var(--dark-accent)' }}>
                              <Briefcase size={16} className="me-1" />
                              {app.company_name}
                            </p>
                            {app.location && (
                              <small style={{ color: 'var(--text-muted)' }}>
                                {app.location}
                              </small>
                            )}
                          </div>
                          <div className="col-md-3 text-md-center mt-2 mt-md-0">
                            <span className={`badge bg-${app.status === 'Applied' ? 'info' : app.status === 'Interview' ? 'warning' : app.status === 'Offer' ? 'success' : 'secondary'} px-3 py-2`}>
                              {app.status}
                            </span>
                          </div>
                          <div className="col-md-3 text-md-end mt-2 mt-md-0">
                            <div className={`badge bg-${deadlineStatus.class} px-3 py-2 mb-1`}>
                              <Clock size={14} className="me-1" />
                              {deadlineStatus.text}
                            </div>
                            <div>
                              <small style={{ color: 'var(--text-muted)' }}>
                                {app.nextDeadline.deadline_type}
                              </small>
                              <br />
                              <small style={{ color: 'var(--text-light)' }}>
                                {formatDate(app.nextDeadline.deadline_date)}
                              </small>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Quick Stats */}
        <motion.div className="mt-5" variants={itemVariants}>
          <div className="row g-4">
            <div className="col-md-4">
              <div className="card shadow-sm h-100 text-center" style={{ backgroundColor: 'var(--card-bg)' }}>
                <div className="card-body">
                  <Search size={48} style={{ color: 'var(--dark-accent)' }} />
                  <h5 className="mt-3" style={{ color: 'var(--text-light)' }}>Smart Scraping</h5>
                  <p style={{ color: 'var(--text-muted)' }}>
                    AI extracts job details and provides strategic application advice
                  </p>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card shadow-sm h-100 text-center" style={{ backgroundColor: 'var(--card-bg)' }}>
                <div className="card-body">
                  <Calendar size={48} style={{ color: 'var(--dark-accent)' }} />
                  <h5 className="mt-3" style={{ color: 'var(--text-light)' }}>Track Deadlines</h5>
                  <p style={{ color: 'var(--text-muted)' }}>
                    Manage multiple deadlines for applications, interviews, and assessments
                  </p>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card shadow-sm h-100 text-center" style={{ backgroundColor: 'var(--card-bg)' }}>
                <div className="card-body">
                  <Briefcase size={48} style={{ color: 'var(--dark-accent)' }} />
                  <h5 className="mt-3" style={{ color: 'var(--text-light)' }}>Stay Organized</h5>
                  <p style={{ color: 'var(--text-muted)' }}>
                    Notes, activity tracking, and status management all in one place
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}

export default Home;
