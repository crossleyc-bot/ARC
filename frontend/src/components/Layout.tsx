import { Outlet, useParams } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  const { projectId } = useParams();

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar projectId={projectId} />
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
