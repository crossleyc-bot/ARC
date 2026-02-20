import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useReports, useDatasets } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import type { Report, Dataset } from '../types';

export function Inventory() {
  const { projectId } = useParams<{ projectId: string }>();
  const [tab, setTab] = useState<'reports' | 'datasets'>('reports');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data: reportsData, isLoading: reportsLoading } = useReports(projectId!, {
    page,
    page_size: 50,
    ...(search ? { search } : {}),
  });

  const { data: datasetsData, isLoading: datasetsLoading } = useDatasets(projectId!);

  const reportColumns = [
    { key: 'name', header: 'Report Name', className: 'font-medium' },
    { key: 'platform', header: 'Platform', render: (r: Report) => (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
        r.platform === 'powerbi' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
      }`}>
        {r.platform === 'powerbi' ? 'Power BI' : 'Cognos'}
      </span>
    )},
    { key: 'report_type', header: 'Type' },
    { key: 'owner', header: 'Owner' },
    { key: 'access_count', header: 'Usage', className: 'text-right' },
    { key: 'rationalization_action', header: 'Action', render: (r: Report) =>
      r.rationalization_action ? <StatusBadge status={r.rationalization_action} /> : <span className="text-gray-400">-</span>
    },
  ];

  const datasetColumns = [
    { key: 'name', header: 'Dataset Name', className: 'font-medium' },
    { key: 'platform', header: 'Platform', render: (d: Dataset) => (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
        d.platform === 'powerbi' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
      }`}>
        {d.platform === 'powerbi' ? 'Power BI' : 'Cognos'}
      </span>
    )},
    { key: 'description', header: 'Description' },
    { key: 'refresh_schedule', header: 'Refresh' },
  ];

  const tabClass = (active: boolean) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
      active ? 'bg-arc-600 text-white' : 'text-gray-600 hover:bg-gray-100'
    }`;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-gray-500 mt-1">Browse harvested reports and datasets</p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button onClick={() => setTab('reports')} className={tabClass(tab === 'reports')}>
            Reports {reportsData ? `(${reportsData.total})` : ''}
          </button>
          <button onClick={() => setTab('datasets')} className={tabClass(tab === 'datasets')}>
            Datasets {datasetsData ? `(${datasetsData.total})` : ''}
          </button>
        </div>

        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-arc-500 focus:outline-none w-64"
          />
        </div>
      </div>

      {tab === 'reports' ? (
        <>
          {reportsLoading ? (
            <div className="text-center py-12 text-gray-500">Loading reports...</div>
          ) : (
            <>
              <DataTable
                columns={reportColumns}
                data={(reportsData?.items || []) as unknown as Record<string, unknown>[]}
                emptyMessage="No reports found. Connect a BI platform and run a sync."
              />
              {reportsData && reportsData.total > 50 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 border border-gray-300 rounded text-sm disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {page} of {Math.ceil(reportsData.total / 50)}
                  </span>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= Math.ceil(reportsData.total / 50)}
                    className="px-3 py-1.5 border border-gray-300 rounded text-sm disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </>
      ) : (
        <>
          {datasetsLoading ? (
            <div className="text-center py-12 text-gray-500">Loading datasets...</div>
          ) : (
            <DataTable
              columns={datasetColumns}
              data={(datasetsData?.items || []) as unknown as Record<string, unknown>[]}
              emptyMessage="No datasets found."
            />
          )}
        </>
      )}
    </div>
  );
}
