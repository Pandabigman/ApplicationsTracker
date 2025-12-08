import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { api } from '../services/api';

export const ApplicationModal = ({ isOpen, editingApp, onClose, onSave }) => {
  const [jobUrl, setJobUrl] = useState(editingApp?.job_url || '');
  const [isScrapingUrl, setIsScrapingUrl] = useState(false);
  const [scrapedData, setScrapedData] = useState(
    editingApp ? {
      company_name: editingApp.company_name,
      position_title: editingApp.position_title,
      job_url: editingApp.job_url,
      location: editingApp.location,
      salary: editingApp.salary,
      description: editingApp.description,
      requirements: editingApp.requirements,
      notes: editingApp.notes,
    } : null
  );
  const [error, setError] = useState('');

  const handleScrapeUrl = async () => {
    if (!jobUrl.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    setIsScrapingUrl(true);
    setError('');

    try {
      const data = await api.scrapeUrl(jobUrl);
      setScrapedData(data);
      setError('');
    } catch (err) {
      setError(`${err.message}. You can still add manually.`);
      setScrapedData({
        company_name: '',
        position_title: '',
        location: '',
        salary: '',
        description: '',
        requirements: '',
        notes: '',
        job_url: jobUrl,
      });
    } finally {
      setIsScrapingUrl(false);
    }
  };

  const handleSave = () => {
    if (!scrapedData?.company_name || !scrapedData?.position_title) {
      setError('Company name and position title are required');
      return;
    }

    const dataToSave = {
      ...scrapedData,
      status: scrapedData.status || 'Applied',
    };

    onSave(dataToSave);
    handleClose();
  };

  const handleClose = () => {
    setJobUrl('');
    setScrapedData(null);
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg modal-dialog-scrollable">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {editingApp ? 'Edit Application' : 'Add New Application'}
            </h5>
            <button type="button" className="btn-close" onClick={handleClose}></button>
          </div>

          <div className="modal-body">
            {!scrapedData && (
              <div className="mb-3">
                <label className="form-label">Job Posting URL</label>
                <div className="input-group">
                  <input
                    type="url"
                    className="form-control"
                    value={jobUrl}
                    onChange={(e) => setJobUrl(e.target.value)}
                    placeholder="https://www.gradcracker.com/search/..."
                  />
                  <button
                    className="btn btn-pill btn-pill-primary"
                    onClick={handleScrapeUrl}
                    disabled={isScrapingUrl}
                  >
                    {isScrapingUrl ? (
                      <>
                        <Loader2 size={18} className="spinner-border spinner-border-sm me-2" />
                        Scraping...
                      </>
                    ) : (
                      'Scrape Job'
                    )}
                  </button>
                </div>
                <div className="form-text">
                  Paste a job URL and we'll try to extract the details automatically
                </div>
              </div>
            )}

            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            {scrapedData && (
              <>
                <div className="mb-3">
                  <label className="form-label">Company Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={scrapedData.company_name || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, company_name: e.target.value })}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Position Title *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={scrapedData.position_title || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, position_title: e.target.value })}
                    required
                  />
                </div>

                <div className="row mb-3">
                  <div className="col-md-6">
                    <label className="form-label">Location</label>
                    <input
                      type="text"
                      className="form-control"
                      value={scrapedData.location || ''}
                      onChange={(e) => setScrapedData({ ...scrapedData, location: e.target.value })}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Salary</label>
                    <input
                      type="text"
                      className="form-control"
                      value={scrapedData.salary || ''}
                      onChange={(e) => setScrapedData({ ...scrapedData, salary: e.target.value })}
                    />
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label">Job URL</label>
                  <input
                    type="url"
                    className="form-control"
                    value={scrapedData.job_url || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, job_url: e.target.value })}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={scrapedData.description || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, description: e.target.value })}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Requirements</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={scrapedData.requirements || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, requirements: e.target.value })}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Notes</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    value={scrapedData.notes || ''}
                    onChange={(e) => setScrapedData({ ...scrapedData, notes: e.target.value })}
                    placeholder="Add any personal notes about this application..."
                  />
                </div>
              </>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-pill btn-secondary" onClick={handleClose}>
              Cancel
            </button>
            {scrapedData && (
              <button type="button" className="btn btn-pill btn-pill-primary" onClick={handleSave}>
                {editingApp ? 'Update Application' : 'Save Application'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
