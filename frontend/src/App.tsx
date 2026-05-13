import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SampleChat from "./components/SampleChat"
import AdminLayout from './pages/maintenance/AdminLayout';
import HardwareManager from "./pages/maintenance/HardwareManager";
import AddHardware from "./pages/maintenance/AddHardware";
import SoftwareManager from "./pages/maintenance/SoftwareManager";
import AddSoftware from './pages/maintenance/AddSoftware';
import EditHardware from './pages/maintenance/EditHardware';
import EditSoftware from './pages/maintenance/EditSoftware';

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
            <Route path="hardware" element={<HardwareManager />} />
            <Route path="hardware/add" element={<AddHardware />} />
            <Route path="hardware/edit/:name" element={<EditHardware />} />
            <Route path="software" element={<SoftwareManager />} />
            <Route path="software/add" element={<AddSoftware />} />
            <Route path="software/edit/:name" element={<EditSoftware />} />
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
