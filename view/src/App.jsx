import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SignedIn, SignedOut, SignIn, SignUp, useAuth, useClerk } from '@clerk/clerk-react';
import Home from './pages/Home';
import AllApplications from './pages/AllApplications';
import JobDetail from './pages/JobDetail';
import Settings from './pages/Settings';
import { setAuthTokenGetter } from './services/api';

function AuthSetup({ children }) {
  const { getToken } = useAuth();
  const clerk = useClerk();

  useEffect(() => {
    setAuthTokenGetter(getToken);
  }, [getToken]);

  useEffect(() => {
    return clerk.addListener(({ user }) => {
      if (!user) localStorage.removeItem('gemini_api_key');
    });
  }, [clerk]);

  return children;
}

function ProtectedRoute({ children }) {
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <div
          className="min-vh-100 d-flex align-items-center justify-content-center"
          style={{ backgroundColor: 'var(--dark-primary)' }}
        >
          <SignIn routing="hash" />
        </div>
      </SignedOut>
    </>
  );
}

function App() {
  return (
    <AuthSetup>
    <Router>
      <Routes>
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/applications" element={<ProtectedRoute><AllApplications /></ProtectedRoute>} />
        <Route path="/job/:id" element={<ProtectedRoute><JobDetail /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route
          path="/sign-in"
          element={
            <div
              className="min-vh-100 d-flex align-items-center justify-content-center"
              style={{ backgroundColor: 'var(--dark-primary)' }}
            >
              <SignIn routing="path" path="/sign-in" />
            </div>
          }
        />
        <Route
          path="/sign-up"
          element={
            <div
              className="min-vh-100 d-flex align-items-center justify-content-center"
              style={{ backgroundColor: 'var(--dark-primary)' }}
            >
              <SignUp routing="path" path="/sign-up" />
            </div>
          }
        />
      </Routes>
    </Router>
    </AuthSetup>
  );
}

export default App;
