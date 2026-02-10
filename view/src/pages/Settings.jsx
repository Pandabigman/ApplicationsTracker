import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Key, Check, X, Loader2, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { api } from '../services/api';

function Settings() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState(null); // 'valid', 'invalid', null

  const savedKey = localStorage.getItem('gemini_api_key');
  const maskedKey = savedKey
    ? savedKey.slice(0, 4) + '...' + savedKey.slice(-4)
    : null;

  const handleSave = () => {
    if (!apiKey.trim()) return;
    localStorage.setItem('gemini_api_key', apiKey.trim());
    setApiKey('');
    setStatus(null);
  };

  const handleClear = () => {
    localStorage.removeItem('gemini_api_key');
    setApiKey('');
    setStatus(null);
  };

  const handleTest = async () => {
    const keyToTest = apiKey.trim() || savedKey;
    if (!keyToTest) return;

    setTesting(true);
    setStatus(null);
    try {
      await api.validateGeminiKey(keyToTest);
      setStatus('valid');
    } catch {
      setStatus('invalid');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="container py-4" style={{ maxWidth: '700px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <button
          className="btn btn-link text-decoration-none ps-0 mb-3"
          onClick={() => navigate('/')}
        >
          <ArrowLeft size={18} className="me-1" /> Back
        </button>

        <h2 className="mb-4">
          <Key size={24} className="me-2" />
          Settings
        </h2>

        <div className="card border-0 shadow-sm">
          <div className="card-body p-4">
            <h5 className="card-title mb-1">Gemini API Key</h5>
            <p className="text-muted small mb-3">
              Required for the job scraping feature. Your key is stored locally in your browser and sent directly to the Gemini API. Get one free at{' '}
              <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">
                Google AI Studio
              </a>.
            </p>

            {savedKey && (
              <div className="alert alert-success d-flex align-items-center py-2 mb-3">
                <Check size={16} className="me-2" />
                Key saved: <code className="ms-1">{maskedKey}</code>
              </div>
            )}

            <div className="input-group mb-3">
              <input
                type={showKey ? 'text' : 'password'}
                className="form-control"
                placeholder={savedKey ? 'Enter new key to replace...' : 'Enter your Gemini API key...'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button
                className="btn btn-outline-secondary"
                type="button"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {status === 'valid' && (
              <div className="alert alert-success py-2 mb-3">
                <Check size={16} className="me-2" />
                API key is valid!
              </div>
            )}
            {status === 'invalid' && (
              <div className="alert alert-danger py-2 mb-3">
                <X size={16} className="me-2" />
                API key is invalid. Please check and try again.
              </div>
            )}

            <div className="d-flex gap-2">
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={!apiKey.trim()}
              >
                Save Key
              </button>
              <button
                className="btn btn-outline-secondary"
                onClick={handleTest}
                disabled={testing || (!apiKey.trim() && !savedKey)}
              >
                {testing ? (
                  <>
                    <Loader2 size={16} className="me-1 spinner-border spinner-border-sm" />
                    Testing...
                  </>
                ) : (
                  'Test Key'
                )}
              </button>
              {savedKey && (
                <button
                  className="btn btn-outline-danger"
                  onClick={handleClear}
                >
                  Clear Key
                </button>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default Settings;
