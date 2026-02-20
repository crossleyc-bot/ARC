import { useParams } from 'react-router-dom';
import { useKPIConflicts } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import type { KPIConflict } from '../types';

export function KPIRegister() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: conflicts, isLoading } = useKPIConflicts(projectId!);

  const columns = [
    { key: 'measure_name', header: 'Measure Name', className: 'font-medium' },
    {
      key: 'severity',
      header: 'Severity',
      render: (c: KPIConflict) => <StatusBadge status={c.severity} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (c: KPIConflict) => <StatusBadge status={c.status} />,
    },
    {
      key: 'conflicting_measures',
      header: 'Definitions',
      render: (c: KPIConflict) => `${(c.conflicting_measures as unknown[])?.length || 0} conflicting`,
    },
    {
      key: 'resolution',
      header: 'Resolution',
      render: (c: KPIConflict) => c.resolution || '-',
    },
    {
      key: 'created_at',
      header: 'Detected',
      render: (c: KPIConflict) => new Date(c.created_at).toLocaleDateString(),
    },
  ];

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading...</div>;
  }

  const critical = conflicts?.filter(c => c.severity === 'critical').length || 0;
  const warning = conflicts?.filter(c => c.severity === 'warning').length || 0;
  const open = conflicts?.filter(c => c.status === 'open').length || 0;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">KPI Conflict Register</h1>
        <p className="text-gray-500 mt-1">
          Track and resolve conflicting KPI definitions across reports
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-red-50 rounded-xl border border-red-200 p-4 text-center">
          <p className="text-2xl font-bold text-red-700">{critical}</p>
          <p className="text-sm text-red-600">Critical</p>
        </div>
        <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4 text-center">
          <p className="text-2xl font-bold text-yellow-700">{warning}</p>
          <p className="text-sm text-yellow-600">Warning</p>
        </div>
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-4 text-center">
          <p className="text-2xl font-bold text-orange-700">{open}</p>
          <p className="text-sm text-orange-600">Open</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={(conflicts || []) as unknown as Record<string, unknown>[]}
        emptyMessage="No KPI conflicts found. Run analysis to detect conflicts."
      />
    </div>
  );
}
