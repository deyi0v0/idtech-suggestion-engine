import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SampleChat from "./components/SampleChat"
import AdminLayout from './pages/maintenance/AdminLayout';
import HardwareManager from "./pages/maintenance/HardwareManager";
import AddHardware from "./pages/maintenance/AddHardware";

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
            <Route path="hardware/add" element={<AddHardware />} />
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
