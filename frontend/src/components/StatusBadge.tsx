interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

const statusStyles: Record<string, string> = {
  // Connection status
  pending: 'bg-gray-100 text-gray-700',
  syncing: 'bg-blue-100 text-blue-700',
  synced: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',

  // Cluster types
  exact_duplicate: 'bg-red-100 text-red-700',
  near_duplicate: 'bg-orange-100 text-orange-700',
  family: 'bg-blue-100 text-blue-700',

  // KPI severity
  critical: 'bg-red-100 text-red-700',
  warning: 'bg-yellow-100 text-yellow-700',
  info: 'bg-blue-100 text-blue-700',

  // Canonical status
  proposed: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-blue-100 text-blue-700',
  certified: 'bg-green-100 text-green-700',

  // Rationalization actions
  retire: 'bg-red-100 text-red-700',
  merge: 'bg-orange-100 text-orange-700',
  migrate: 'bg-blue-100 text-blue-700',
  keep: 'bg-green-100 text-green-700',

  // KPI conflict status
  open: 'bg-yellow-100 text-yellow-700',
  resolved: 'bg-green-100 text-green-700',
};

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const style = statusStyles[status] || 'bg-gray-100 text-gray-700';
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${style} ${sizeClass}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}
