import { useParams } from 'react-router-dom';
import { useCanonicalDatasets } from '../hooks/useApi';
import { updateCanonicalDataset } from '../api/client';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { useQueryClient } from '@tanstack/react-query';
import type { CanonicalDataset } from '../types';

export function Canonical() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { data: datasets, isLoading } = useCanonicalDatasets(projectId!);

  const handleStatusUpdate = async (id: string, status: string) => {
    await updateCanonicalDataset(id, { status });
    queryClient.invalidateQueries({ queryKey: ['canonical', projectId] });
  };

  const columns = [
    { key: 'name', header: 'Dataset Name', className: 'font-medium' },
    {
      key: 'status',
      header: 'Status',
      render: (d: CanonicalDataset) => <StatusBadge status={d.status} />,
    },
    { key: 'grain', header: 'Grain', render: (d: CanonicalDataset) => d.grain || '-' },
    {
      key: 'dimensions',
      header: 'Dimensions',
      render: (d: CanonicalDataset) => (d.dimensions?.length || 0).toString(),
      className: 'text-right',
    },
    {
      key: 'measures_def',
      header: 'Measures',
      render: (d: CanonicalDataset) => (d.measures_def?.length || 0).toString(),
      className: 'text-right',
    },
    {
      key: 'gap_analysis_count',
      header: 'Reports',
      className: 'text-right',
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (d: CanonicalDataset) => (
        <div className="flex gap-1">
          {d.status === 'proposed' && (
            <button
              onClick={(e) => { e.stopPropagation(); handleStatusUpdate(d.id, 'approved'); }}
              className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200"
            >
              Approve
            </button>
          )}
          {d.status === 'approved' && (
            <button
              onClick={(e) => { e.stopPropagation(); handleStatusUpdate(d.id, 'certified'); }}
              className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium hover:bg-green-200"
            >
              Certify
            </button>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading...</div>;
  }

  const proposed = datasets?.filter(d => d.status === 'proposed').length || 0;
  const approved = datasets?.filter(d => d.status === 'approved').length || 0;
  const certified = datasets?.filter(d => d.status === 'certified').length || 0;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Canonical Datasets</h1>
        <p className="text-gray-500 mt-1">
          Standardized dataset recommendations derived from report clusters
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4 text-center">
          <p className="text-2xl font-bold text-yellow-700">{proposed}</p>
          <p className="text-sm text-yellow-600">Proposed</p>
        </div>
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-center">
          <p className="text-2xl font-bold text-blue-700">{approved}</p>
          <p className="text-sm text-blue-600">Approved</p>
        </div>
        <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
          <p className="text-2xl font-bold text-green-700">{certified}</p>
          <p className="text-sm text-green-600">Certified</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={datasets || []}
        emptyMessage="No canonical datasets yet. Run analysis and canonicalization first."
      />
    </div>
  );
}
