import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Download, Home } from 'lucide-react';
import { ApplicationCard } from '../components/ApplicationCard';
import { ApplicationModal } from '../components/ApplicationModal';
import { api } from '../services/api';

const statusColumns = [
  { id: 'Applied', bgColor: 'bg-primary', btnColor: 'btn-primary' },
  { id: 'Pending Interview', bgColor: 'bg-warning', btnColor: 'btn-warning' },
  { id: 'Interview Scheduled', bgColor: 'bg-info', btnColor: 'btn-info' },
  { id: 'Offer Received', bgColor: 'bg-success', btnColor: 'btn-success' },
  { id: 'Rejected', bgColor: 'bg-danger', btnColor: 'btn-danger' },
];

export const Dashboard = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingApp, setEditingApp] = useState(null);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const data = await api.getApplications();
      setApplications(data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    }
  };

  const handleSaveApplication = async (data) => {
    try {
      if (editingApp) {
        const updated = await api.updateApplication(editingApp.id, data);
        setApplications(applications.map((app) => (app.id === editingApp.id ? updated : app)));
      } else {
        const newApp = await api.createApplication({
          ...data,
          date_applied: new Date().toISOString(),
        });
        setApplications([...applications, newApp]);
      }
    } catch (error) {
      console.error('Error saving application:', error);
    }
  };

  const handleUpdateStatus = async (appId, newStatus) => {
    try {
      const app = applications.find((a) => a.id === appId);
      if (!app) return;

      const updated = await api.updateApplication(appId, { ...app, status: newStatus });
      setApplications(applications.map((a) => (a.id === appId ? updated : a)));
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const handleDeleteApplication = async (appId) => {
    if (!confirm('Are you sure you want to delete this application?')) return;

    try {
      await api.deleteApplication(appId);
      setApplications(applications.filter((app) => app.id !== appId));
    } catch (error) {
      console.error('Error deleting application:', error);
    }
  };

  const handleExportToExcel = async () => {
    try {
      const blob = await api.exportToExcel();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `applications_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting to Excel:', error);
    }
  };

  const handleEditApplication = (app) => {
    setEditingApp(app);
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingApp(null);
  };

  const getApplicationsByStatus = (status) => {
    return applications.filter((app) => app.status === status);
  };

  return (
    <div className="min-vh-100">
      <header className="header-dark">
        <div className="container-fluid py-4">
          <div className="header-center mb-3">
            <h1 className="h2 mb-2">Application Tracker</h1>
            <p className="mb-0">Track your job applications in one place</p>
          </div>
          <div className="d-flex justify-content-center gap-3">
            <button onClick={() => navigate('/')} className="btn btn-pill btn-outline-secondary">
              <Home size={18} className="me-2" />
              Home
            </button>
            <button onClick={handleExportToExcel} className="btn btn-pill btn-pill-success">
              <Download size={18} className="me-2" />
              Export to Excel
            </button>
            <button onClick={() => setShowAddModal(true)} className="btn btn-pill btn-pill-primary">
              <Plus size={18} className="me-2" />
              Add Application
            </button>
          </div>
        </div>
      </header>

      <main className="container-fluid py-4">
        <div className="status-categories">
          {statusColumns.map((column) => (
            <div key={column.id} className="status-category-card">
              <div className="status-category-header">
                <h5 className="mb-0">
                  {column.id}
                  <span className="badge ms-2">
                    {getApplicationsByStatus(column.id).length}
                  </span>
                </h5>
              </div>
              <div className="status-category-body">
                {getApplicationsByStatus(column.id).map((app) => (
                  <ApplicationCard
                    key={app.id}
                    application={app}
                    statusColumns={statusColumns}
                    onEdit={handleEditApplication}
                    onDelete={handleDeleteApplication}
                    onStatusChange={handleUpdateStatus}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>

      <ApplicationModal
        isOpen={showAddModal}
        editingApp={editingApp}
        onClose={handleCloseModal}
        onSave={handleSaveApplication}
      />
    </div>
  );
};
export default Dashboard;