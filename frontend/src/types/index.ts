export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  report_count?: number;
  dataset_count?: number;
  connection_count?: number;
}

export interface Connection {
  id: string;
  project_id: string;
  platform: 'powerbi' | 'cognos';
  name: string;
  status: string;
  last_sync: string | null;
  sync_error: string | null;
  created_at: string;
}

export interface Report {
  id: string;
  project_id: string;
  connection_id: string;
  platform: string;
  external_id: string;
  name: string;
  path: string | null;
  report_type: string | null;
  owner: string | null;
  last_modified: string | null;
  last_accessed: string | null;
  access_count: number;
  content_hash: string | null;
  fields_used: string[] | null;
  rationalization_action: string | null;
  rationalization_score: number | null;
  created_at: string;
}

export interface Dataset {
  id: string;
  project_id: string;
  connection_id: string;
  platform: string;
  external_id: string;
  name: string;
  description: string | null;
  tables: unknown[] | null;
  refresh_schedule: string | null;
  created_at: string;
}

export interface Measure {
  id: string;
  name: string;
  expression: string | null;
  data_type: string | null;
  description: string | null;
  is_kpi: boolean;
  normalized_name: string | null;
}

export interface Cluster {
  id: string;
  project_id: string;
  name: string;
  cluster_type: string;
  similarity_score: number | null;
  member_count: number;
  created_at: string;
}

export interface ClusterDetail extends Cluster {
  members: ClusterMember[];
  metadata: Record<string, unknown> | null;
}

export interface ClusterMember {
  report_id: string;
  report_name: string;
  role: string;
  platform: string;
}

export interface KPIConflict {
  id: string;
  project_id: string;
  measure_name: string;
  conflicting_measures: unknown[] | null;
  severity: string;
  resolution: string | null;
  status: string;
  created_at: string;
}

export interface CanonicalDataset {
  id: string;
  project_id: string;
  cluster_id: string | null;
  name: string;
  description: string | null;
  grain: string | null;
  dimensions: string[] | null;
  measures_def: unknown[] | null;
  status: string;
  created_at: string;
  updated_at: string;
  gap_analysis_count: number;
}

export interface GapAnalysis {
  id: string;
  canonical_id: string;
  report_id: string;
  report_name: string;
  missing_fields: string[] | null;
  extra_fields: string[] | null;
  compatibility_score: number | null;
}

export interface DashboardData {
  total_reports: number;
  total_datasets: number;
  total_measures: number;
  duplicate_clusters: number;
  near_duplicate_clusters: number;
  family_clusters: number;
  kpi_conflicts_open: number;
  kpi_conflicts_resolved: number;
  canonical_datasets_proposed: number;
  canonical_datasets_certified: number;
  reports_to_retire: number;
  reports_to_merge: number;
  reports_to_migrate: number;
  reports_to_keep: number;
  estimated_reduction_pct: number;
  platform_breakdown: Record<string, number>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
