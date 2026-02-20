import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  Link2,
  FileText,
  GitBranch,
  Target,
  AlertTriangle,
  Map,
  Database,
} from 'lucide-react';

interface SidebarProps {
  projectId?: string;
}

export function Sidebar({ projectId }: SidebarProps) {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-arc-600 text-white'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
    }`;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-5 border-b border-gray-200">
        <h1 className="text-xl font-bold text-arc-800">ARC</h1>
        <p className="text-xs text-gray-500 mt-1">Analytics Rationalization & Canonicalization</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <NavLink to="/" className={navClass}>
          <FolderOpen size={18} />
          Projects
        </NavLink>

        {projectId && (
          <>
            <div className="pt-3 pb-1 px-4">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Project
              </span>
            </div>

            <NavLink to={`/projects/${projectId}`} end className={navClass}>
              <LayoutDashboard size={18} />
              Dashboard
            </NavLink>

            <NavLink to={`/projects/${projectId}/connections`} className={navClass}>
              <Link2 size={18} />
              Connections
            </NavLink>

            <NavLink to={`/projects/${projectId}/inventory`} className={navClass}>
              <FileText size={18} />
              Inventory
            </NavLink>

            <NavLink to={`/projects/${projectId}/clusters`} className={navClass}>
              <GitBranch size={18} />
              Clusters
            </NavLink>

            <NavLink to={`/projects/${projectId}/canonical`} className={navClass}>
              <Database size={18} />
              Canonical Datasets
            </NavLink>

            <NavLink to={`/projects/${projectId}/kpi-conflicts`} className={navClass}>
              <AlertTriangle size={18} />
              KPI Register
            </NavLink>

            <NavLink to={`/projects/${projectId}/roadmap`} className={navClass}>
              <Map size={18} />
              Roadmap
            </NavLink>
          </>
        )}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-arc-600" />
          <span className="text-xs text-gray-500">v0.1.0</span>
        </div>
      </div>
    </aside>
  );
}
