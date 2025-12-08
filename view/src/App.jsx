import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import AllApplications from './pages/AllApplications';
import JobDetail from './pages/JobDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/applications" element={<AllApplications />} />
        <Route path="/job/:id" element={<JobDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
