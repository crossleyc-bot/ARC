import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Plus, RefreshCw, Plug } from 'lucide-react';
import { useConnections } from '../hooks/useApi';
import { createConnection, syncConnection } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { useQueryClient } from '@tanstack/react-query';

export function Connections() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { data: connections, isLoading } = useConnections(projectId!);
  const [showAdd, setShowAdd] = useState(false);
  const [platform, setPlatform] = useState<'powerbi' | 'cognos'>('powerbi');
  const [connName, setConnName] = useState('');
  const [config, setConfig] = useState('{}');

  const handleCreate = async () => {
    if (!connName.trim()) return;
    try {
      const configObj = JSON.parse(config);
      await createConnection(projectId!, { platform, name: connName.trim(), config: configObj });
      setConnName('');
      setConfig('{}');
      setShowAdd(false);
      queryClient.invalidateQueries({ queryKey: ['connections', projectId] });
    } catch {
      alert('Invalid JSON config');
    }
  };

  const handleSync = async (connectionId: string) => {
    await syncConnection(connectionId);
    queryClient.invalidateQueries({ queryKey: ['connections', projectId] });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Connections</h1>
          <p className="text-gray-500 mt-1">Connect to Power BI and Cognos environments</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-arc-600 text-white rounded-lg hover:bg-arc-700 text-sm font-medium"
        >
          <Plus size={18} /> Add Connection
        </button>
      </div>

      {showAdd && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h3 className="font-semibold mb-3">New Connection</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
              <select
                value={platform}
                onChange={e => setPlatform(e.target.value as 'powerbi' | 'cognos')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-arc-500"
              >
                <option value="powerbi">Power BI</option>
                <option value="cognos">IBM Cognos</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={connName}
                onChange={e => setConnName(e.target.value)}
                placeholder="e.g., Production Power BI"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-arc-500"
              />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Configuration (JSON)
            </label>
            <textarea
              value={config}
              onChange={e => setConfig(e.target.value)}
              placeholder={platform === 'powerbi'
                ? '{"client_id": "...", "client_secret": "...", "tenant_id": "..."}'
                : '{"base_url": "...", "namespace": "...", "username": "...", "password": "..."}'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-arc-500"
              rows={3}
            />
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleCreate}
              disabled={!connName.trim()}
              className="px-4 py-2 bg-arc-600 text-white rounded-lg hover:bg-arc-700 disabled:opacity-50 text-sm font-medium"
            >
              Create
            </button>
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 text-gray-600 text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : !connections?.length ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Plug size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">No connections yet. Add one to start harvesting metadata.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {connections.map(conn => (
            <div key={conn.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm ${
                    conn.platform === 'powerbi' ? 'bg-yellow-500' : 'bg-blue-700'
                  }`}>
                    {conn.platform === 'powerbi' ? 'PBI' : 'COG'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{conn.name}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <StatusBadge status={conn.status} />
                      {conn.last_sync && (
                        <span className="text-xs text-gray-400">
                          Last sync: {new Date(conn.last_sync).toLocaleString()}
                        </span>
                      )}
                    </div>
                    {conn.sync_error && (
                      <p className="text-xs text-red-500 mt-1">{conn.sync_error}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleSync(conn.id)}
                  disabled={conn.status === 'syncing'}
                  className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
                >
                  <RefreshCw size={14} className={conn.status === 'syncing' ? 'animate-spin' : ''} />
                  {conn.status === 'syncing' ? 'Syncing...' : 'Sync'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
