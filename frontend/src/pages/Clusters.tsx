import { useParams } from 'react-router-dom';
import { useClusters } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { SimilarityGraph } from '../components/SimilarityGraph';
import type { Cluster } from '../types';

export function Clusters() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: clusters, isLoading } = useClusters(projectId!);

  const columns = [
    { key: 'name', header: 'Cluster Name', className: 'font-medium' },
    {
      key: 'cluster_type',
      header: 'Type',
      render: (c: Cluster) => <StatusBadge status={c.cluster_type} />,
    },
    {
      key: 'similarity_score',
      header: 'Similarity',
      render: (c: Cluster) => c.similarity_score != null ? `${(c.similarity_score * 100).toFixed(0)}%` : '-',
      className: 'text-right',
    },
    { key: 'member_count', header: 'Members', className: 'text-right' },
    {
      key: 'created_at',
      header: 'Created',
      render: (c: Cluster) => new Date(c.created_at).toLocaleDateString(),
    },
  ];

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading clusters...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Report Clusters</h1>
        <p className="text-gray-500 mt-1">
          Duplicate groups, near-duplicate clusters, and report families
        </p>
      </div>

      <div className="mb-6">
        <SimilarityGraph clusters={clusters || []} />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {['exact_duplicate', 'near_duplicate', 'family'].map(type => {
          const count = clusters?.filter(c => c.cluster_type === type).length || 0;
          const label = type === 'exact_duplicate' ? 'Exact Duplicates' : type === 'near_duplicate' ? 'Near Duplicates' : 'Report Families';
          return (
            <div key={type} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{count}</p>
              <p className="text-sm text-gray-500">{label}</p>
            </div>
          );
        })}
      </div>

      <DataTable
        columns={columns}
        data={clusters || []}
        emptyMessage="No clusters found. Run analysis to detect report clusters."
      />
    </div>
  );
}
