import axios from 'axios';
import type {
  CanonicalDataset,
  Cluster,
  Connection,
  DashboardData,
  Dataset,
  KPIConflict,
  Measure,
  PaginatedResponse,
  Project,
  Report,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Projects
export const createProject = (data: { name: string; description?: string }) =>
  api.post<Project>('/projects', data).then(r => r.data);

export const listProjects = () =>
  api.get<Project[]>('/projects').then(r => r.data);

export const getProject = (id: string) =>
  api.get<Project>(`/projects/${id}`).then(r => r.data);

export const deleteProject = (id: string) =>
  api.delete(`/projects/${id}`);

// Connections
export const createConnection = (projectId: string, data: { platform: string; name: string; config: Record<string, string> }) =>
  api.post<Connection>(`/projects/${projectId}/connections`, data).then(r => r.data);

export const listConnections = (projectId: string) =>
  api.get<Connection[]>(`/projects/${projectId}/connections`).then(r => r.data);

export const syncConnection = (connectionId: string) =>
  api.post(`/connections/${connectionId}/sync`).then(r => r.data);

export const getSyncStatus = (connectionId: string) =>
  api.get(`/connections/${connectionId}/sync-status`).then(r => r.data);

// Inventory
export const listReports = (projectId: string, params?: Record<string, string | number>) =>
  api.get<PaginatedResponse<Report>>(`/projects/${projectId}/reports`, { params }).then(r => r.data);

export const listDatasets = (projectId: string, params?: Record<string, string | number>) =>
  api.get<PaginatedResponse<Dataset>>(`/projects/${projectId}/datasets`, { params }).then(r => r.data);

export const listMeasures = (projectId: string, params?: Record<string, string | boolean>) =>
  api.get<Measure[]>(`/projects/${projectId}/measures`, { params }).then(r => r.data);

// Analysis
export const triggerAnalysis = (projectId: string) =>
  api.post(`/projects/${projectId}/analyze`).then(r => r.data);

export const getAnalysisStatus = (projectId: string) =>
  api.get(`/projects/${projectId}/analysis/status`).then(r => r.data);

export const listClusters = (projectId: string, clusterType?: string) =>
  api.get<Cluster[]>(`/projects/${projectId}/clusters`, { params: clusterType ? { cluster_type: clusterType } : {} }).then(r => r.data);

export const listKPIConflicts = (projectId: string) =>
  api.get<KPIConflict[]>(`/projects/${projectId}/kpi-conflicts`).then(r => r.data);

// Canonical
export const triggerCanonicalization = (projectId: string) =>
  api.post(`/projects/${projectId}/canonicalize`).then(r => r.data);

export const listCanonicalDatasets = (projectId: string) =>
  api.get<CanonicalDataset[]>(`/projects/${projectId}/canonical-datasets`).then(r => r.data);

export const updateCanonicalDataset = (id: string, data: { status?: string }) =>
  api.put<CanonicalDataset>(`/canonical-datasets/${id}`, data).then(r => r.data);

// Dashboard
export const getDashboard = (projectId: string) =>
  api.get<DashboardData>(`/projects/${projectId}/dashboard`).then(r => r.data);

// Exports
export const exportExcel = (projectId: string) =>
  api.get(`/projects/${projectId}/export/excel`, { responseType: 'blob' }).then(r => r.data);

export const exportPDF = (projectId: string) =>
  api.get(`/projects/${projectId}/export/pdf`, { responseType: 'blob' }).then(r => r.data);
