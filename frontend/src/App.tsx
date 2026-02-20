import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { Projects } from './pages/Projects';
import { Dashboard } from './pages/Dashboard';
import { Connections } from './pages/Connections';
import { Inventory } from './pages/Inventory';
import { Clusters } from './pages/Clusters';
import { Canonical } from './pages/Canonical';
import { KPIRegister } from './pages/KPIRegister';
import { Roadmap } from './pages/Roadmap';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Projects />} />
            <Route path="/projects/:projectId" element={<Dashboard />} />
            <Route path="/projects/:projectId/connections" element={<Connections />} />
            <Route path="/projects/:projectId/inventory" element={<Inventory />} />
            <Route path="/projects/:projectId/clusters" element={<Clusters />} />
            <Route path="/projects/:projectId/canonical" element={<Canonical />} />
            <Route path="/projects/:projectId/kpi-conflicts" element={<KPIRegister />} />
            <Route path="/projects/:projectId/roadmap" element={<Roadmap />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
