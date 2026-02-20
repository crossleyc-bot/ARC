import { useParams } from 'react-router-dom';
import { useReports } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import type { Report } from '../types';

export function Roadmap() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: reportsData, isLoading } = useReports(projectId!, { page_size: 200 });

  const reports = reportsData?.items || [];
  const actionReports = reports.filter(r => r.rationalization_action);

  const retireCount = actionReports.filter(r => r.rationalization_action === 'retire').length;
  const mergeCount = actionReports.filter(r => r.rationalization_action === 'merge').length;
  const migrateCount = actionReports.filter(r => r.rationalization_action === 'migrate').length;
  const keepCount = actionReports.filter(r => r.rationalization_action === 'keep').length;

  const totalSavings = actionReports.reduce((sum, r) => sum + (r.rationalization_score || 0), 0);

  const columns = [
    { key: 'name', header: 'Report Name', className: 'font-medium' },
    {
      key: 'rationalization_action',
      header: 'Action',
      render: (r: Report) => r.rationalization_action
        ? <StatusBadge status={r.rationalization_action} size="md" />
        : <span className="text-gray-400">Pending</span>,
    },
    {
      key: 'platform',
      header: 'Platform',
      render: (r: Report) => (
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          r.platform === 'powerbi' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
        }`}>
          {r.platform === 'powerbi' ? 'Power BI' : 'Cognos'}
        </span>
      ),
    },
    { key: 'owner', header: 'Owner', render: (r: Report) => r.owner || '-' },
    { key: 'access_count', header: 'Usage', className: 'text-right' },
    {
      key: 'rationalization_score',
      header: 'Est. Savings (hrs)',
      render: (r: Report) => r.rationalization_score?.toFixed(1) || '-',
      className: 'text-right',
    },
  ];

  // Sort: retire first, then merge, migrate, keep
  const priorityOrder: Record<string, number> = { retire: 0, merge: 1, migrate: 2, keep: 3 };
  const sortedReports = [...actionReports].sort(
    (a, b) =>
      (priorityOrder[a.rationalization_action || ''] ?? 9) -
      (priorityOrder[b.rationalization_action || ''] ?? 9)
  );

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading roadmap...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Rationalization Roadmap</h1>
        <p className="text-gray-500 mt-1">
          Recommended actions for each report with estimated savings
        </p>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-red-50 rounded-xl border border-red-200 p-4 text-center">
          <p className="text-2xl font-bold text-red-700">{retireCount}</p>
          <p className="text-sm text-red-600">Retire</p>
        </div>
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-4 text-center">
          <p className="text-2xl font-bold text-orange-700">{mergeCount}</p>
          <p className="text-sm text-orange-600">Merge</p>
        </div>
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-center">
          <p className="text-2xl font-bold text-blue-700">{migrateCount}</p>
          <p className="text-sm text-blue-600">Migrate</p>
        </div>
        <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
          <p className="text-2xl font-bold text-green-700">{keepCount}</p>
          <p className="text-sm text-green-600">Keep</p>
        </div>
        <div className="bg-purple-50 rounded-xl border border-purple-200 p-4 text-center">
          <p className="text-2xl font-bold text-purple-700">{totalSavings.toFixed(0)}</p>
          <p className="text-sm text-purple-600">Est. Hours Saved</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={sortedReports as unknown as Record<string, unknown>[]}
        emptyMessage="No rationalization actions generated yet. Run analysis first."
      />
    </div>
  );
}
