import { useParams } from 'react-router-dom';
import {
  FileText,
  Database,
  GitBranch,
  AlertTriangle,
  TrendingDown,
  CheckCircle,
  Download,
} from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useDashboard, useProject } from '../hooks/useApi';
import { MetricCard } from '../components/MetricCard';
import { exportExcel, exportPDF } from '../api/client';
import { triggerAnalysis, triggerCanonicalization } from '../api/client';

export function Dashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project } = useProject(projectId!);
  const { data: dashboard, isLoading } = useDashboard(projectId!);

  const handleExport = async (format: 'excel' | 'pdf') => {
    const blob = format === 'excel'
      ? await exportExcel(projectId!)
      : await exportPDF(projectId!);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ARC_${project?.name || 'Report'}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading || !dashboard) {
    return <div className="text-center py-12 text-gray-500">Loading dashboard...</div>;
  }

  const actionData = [
    { name: 'Retire', value: dashboard.reports_to_retire, color: '#ef4444' },
    { name: 'Merge', value: dashboard.reports_to_merge, color: '#f97316' },
    { name: 'Migrate', value: dashboard.reports_to_migrate, color: '#3b82f6' },
    { name: 'Keep', value: dashboard.reports_to_keep, color: '#22c55e' },
  ].filter(d => d.value > 0);

  const clusterData = [
    { name: 'Exact Dups', count: dashboard.duplicate_clusters },
    { name: 'Near Dups', count: dashboard.near_duplicate_clusters },
    { name: 'Families', count: dashboard.family_clusters },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project?.name || 'Dashboard'}</h1>
          <p className="text-gray-500 mt-1">Analytics rationalization overview</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => triggerAnalysis(projectId!)}
            className="px-4 py-2 bg-arc-600 text-white rounded-lg hover:bg-arc-700 text-sm font-medium"
          >
            Run Analysis
          </button>
          <button
            onClick={() => triggerCanonicalization(projectId!)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
          >
            Canonicalize
          </button>
          <button
            onClick={() => handleExport('excel')}
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            <Download size={14} /> Excel
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            <Download size={14} /> PDF
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Total Reports"
          value={dashboard.total_reports}
          icon={<FileText size={20} />}
        />
        <MetricCard
          title="Total Datasets"
          value={dashboard.total_datasets}
          icon={<Database size={20} />}
        />
        <MetricCard
          title="Est. Reduction"
          value={`${dashboard.estimated_reduction_pct}%`}
          icon={<TrendingDown size={20} />}
          color="green-600"
        />
        <MetricCard
          title="KPI Conflicts"
          value={dashboard.kpi_conflicts_open}
          icon={<AlertTriangle size={20} />}
          subtitle={`${dashboard.kpi_conflicts_resolved} resolved`}
          color="yellow-600"
        />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <MetricCard
          title="Report Clusters"
          value={dashboard.duplicate_clusters + dashboard.near_duplicate_clusters + dashboard.family_clusters}
          icon={<GitBranch size={20} />}
        />
        <MetricCard
          title="Canonical Datasets"
          value={dashboard.canonical_datasets_proposed + dashboard.canonical_datasets_certified}
          icon={<CheckCircle size={20} />}
          subtitle={`${dashboard.canonical_datasets_certified} certified`}
          color="green-600"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-800 mb-4">Rationalization Actions</h3>
          {actionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={actionData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {actionData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">Run analysis to see actions</p>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-800 mb-4">Cluster Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={clusterData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
