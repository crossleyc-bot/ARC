import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/client';

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: api.listProjects });
}

export function useProject(id: string) {
  return useQuery({ queryKey: ['project', id], queryFn: () => api.getProject(id), enabled: !!id });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createProject,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });
}

export function useConnections(projectId: string) {
  return useQuery({
    queryKey: ['connections', projectId],
    queryFn: () => api.listConnections(projectId),
    enabled: !!projectId,
  });
}

export function useReports(projectId: string, params?: Record<string, string | number>) {
  return useQuery({
    queryKey: ['reports', projectId, params],
    queryFn: () => api.listReports(projectId, params),
    enabled: !!projectId,
  });
}

export function useDatasets(projectId: string) {
  return useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => api.listDatasets(projectId),
    enabled: !!projectId,
  });
}

export function useMeasures(projectId: string) {
  return useQuery({
    queryKey: ['measures', projectId],
    queryFn: () => api.listMeasures(projectId),
    enabled: !!projectId,
  });
}

export function useClusters(projectId: string) {
  return useQuery({
    queryKey: ['clusters', projectId],
    queryFn: () => api.listClusters(projectId),
    enabled: !!projectId,
  });
}

export function useKPIConflicts(projectId: string) {
  return useQuery({
    queryKey: ['kpi-conflicts', projectId],
    queryFn: () => api.listKPIConflicts(projectId),
    enabled: !!projectId,
  });
}

export function useCanonicalDatasets(projectId: string) {
  return useQuery({
    queryKey: ['canonical', projectId],
    queryFn: () => api.listCanonicalDatasets(projectId),
    enabled: !!projectId,
  });
}

export function useDashboard(projectId: string) {
  return useQuery({
    queryKey: ['dashboard', projectId],
    queryFn: () => api.getDashboard(projectId),
    enabled: !!projectId,
  });
}
