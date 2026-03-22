import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import PinGate from "./components/PinGate";
import Home from "./pages/Home";
import WorkflowRun from "./pages/WorkflowRun";
import Findings from "./pages/Findings";
import ExecutiveSummary from "./pages/ExecutiveSummary";
import AuditTrail from "./pages/AuditTrail";

export default function App() {
  return (
    <PinGate>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/workflow-run" element={<WorkflowRun />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/summary" element={<ExecutiveSummary />} />
            <Route path="/audit" element={<AuditTrail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </PinGate>
  );
}
