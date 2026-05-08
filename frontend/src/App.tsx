import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SampleChat from "./components/SampleChat"
import Dashboard from "./pages/maintenance/Dashboard"
// import HardwareManager from "./pages/maintenance/HardwareManager"
// import SoftwareManager from "./pages/maintenance/SoftwareManager"
// import PromptManager from "./pages/maintenance/PromptManager"
// import DocManager from "./pages/maintenance/DocManager"
import AdminLayout from './pages/maintenance/AdminLayout';
import HardwareManager from "./pages/maintenance/HardwareManager";

function App() {
  return (
    <Router>
      <Routes>
        {/* Customer Suggestion Engine */}
        <Route path="/" element={
          <div className="flex flex-col items-center">
            <h1 className="text-white text-center">IDTECH Suggestion Engine</h1>
            <SampleChat />
          </div>
        } />

        {/* Maintenance Portal */}
        <Route path="/admin" element={<AdminLayout />}> 
            <Route index element={<HardwareManager />} />
        </Route>
        {/* <Route path="/admin/hardware" element={<HardwareManager />} />
        <Route path="/admin/software" element={<SoftwareManager />} />
        <Route path="/admin/prompts" element={<PromptManager />} />
        <Route path="/admin/docs" element={<DocManager />} /> */}
      </Routes>
    </Router>
  );
}

export default App;
