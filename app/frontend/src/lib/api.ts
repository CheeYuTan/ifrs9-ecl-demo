import type { ProjectRole, RbacRole } from './permissions';

const BASE = '/api';

async function del<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`);
  return r.json();
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`);
  return r.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`);
  return r.json();
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`);
  return r.json();
}

export interface Project {
  project_id: string;
  project_name: string;
  project_type: string;
  description: string;
  reporting_date: string;
  current_step: number;
  step_status: Record<string, string>;
  overlays: Overlay[];
  scenario_weights: Record<string, number>;
  audit_log: AuditEntry[];
  created_at: string;
  updated_at: string;
  signed_off_by: string | null;
  signed_off_at: string | null;
}

export interface AuditEntry {
  ts: string;
  user: string;
  action: string;
  detail: string;
  step: string;
}

export interface Overlay {
  id: string;
  product: string;
  type: string;
  amount: number;
  reason: string;
  ifrs9: string;
  approved_by?: string;
  expiry?: string;
  classification?: 'temporary' | 'permanent';
}

export interface ModelRegistryEntry {
  model_id: string;
  model_name: string;
  model_type: string;
  algorithm: string;
  version: number;
  description: string;
  status: 'draft' | 'pending_review' | 'approved' | 'active' | 'retired';
  product_type: string;
  cohort: string;
  parameters: Record<string, unknown>;
  performance_metrics: Record<string, unknown>;
  training_data_info: Record<string, unknown>;
  is_champion: boolean;
  created_by: string;
  created_at: string;
  approved_by: string | null;
  approved_at: string | null;
  promoted_by: string | null;
  promoted_at: string | null;
  retired_by: string | null;
  retired_at: string | null;
  notes: string;
  parent_model_id: string | null;
}

export interface GLAccount {
  account_code: string;
  account_name: string;
  account_type: string;
  parent_account: string | null;
  is_ecl_related: boolean;
}

export interface GLJournalLine {
  line_id: string;
  journal_id: string;
  account_code: string;
  account_name?: string;
  account_type?: string;
  debit: number;
  credit: number;
  product_type: string;
  stage: string;
  description: string;
}

export interface GLJournal {
  journal_id: string;
  project_id: string;
  journal_date: string;
  journal_type: string;
  status: 'draft' | 'posted' | 'reversed';
  created_by: string;
  posted_by: string | null;
  posted_at: string | null;
  description: string;
  reference: string;
  created_at: string;
  total_debit: number;
  total_credit: number;
  line_count: number;
  balanced: boolean;
  lines?: GLJournalLine[];
}

export interface GLTrialBalanceRow {
  account_code: string;
  account_name: string;
  account_type: string;
  total_debit: number;
  total_credit: number;
  balance: number;
}

export interface ModelAuditEntry {
  audit_id: string;
  model_id: string;
  action: string;
  old_status: string | null;
  new_status: string | null;
  performed_by: string;
  performed_at: string;
  comment: string;
}

export interface BacktestMetric {
  metric_id: string;
  metric_name: string;
  metric_value: number;
  threshold_green: number;
  threshold_amber: number;
  pass_fail: 'Green' | 'Amber' | 'Red';
}

export interface BacktestCohort {
  cohort_id: string;
  cohort_name: string;
  predicted_rate: number;
  actual_rate: number;
  count: number;
  abs_diff: number;
}

export interface BacktestResult {
  backtest_id: string;
  model_id: string | null;
  model_type: string;
  backtest_date: string;
  observation_window: string;
  outcome_window: string;
  overall_traffic_light: 'Green' | 'Amber' | 'Red';
  pass_count: number;
  amber_count: number;
  fail_count: number;
  total_loans: number;
  config: Record<string, unknown>;
  created_by: string;
  metrics?: BacktestMetric[];
  cohort_results?: BacktestCohort[];
}

export interface BacktestTrendPoint {
  backtest_id: string;
  backtest_date: string;
  overall_traffic_light: string;
  AUC?: number;
  Gini?: number;
  KS?: number;
  PSI?: number;
  Brier?: number;
  [key: string]: string | number | undefined;
}

export interface RbacUser {
  user_id: string;
  email: string;
  display_name: string;
  role: 'analyst' | 'reviewer' | 'approver' | 'admin';
  department: string;
  is_active: boolean;
  created_at: string;
  permissions?: string[];
}

export interface ApprovalRequest {
  request_id: string;
  request_type: 'model_approval' | 'overlay_approval' | 'journal_posting' | 'sign_off';
  entity_id: string;
  entity_type: string;
  status: 'pending' | 'approved' | 'rejected' | 'escalated';
  requested_by: string;
  requested_by_name?: string;
  assigned_to: string | null;
  assigned_to_name?: string;
  approved_by: string | null;
  approved_by_name?: string;
  approved_at: string | null;
  rejection_reason: string;
  comments: string;
  priority: 'normal' | 'urgent';
  due_date: string | null;
  created_at: string;
}

export interface ProjectMember {
  project_id: string;
  user_id: string;
  role: ProjectRole;
  granted_by: string;
  granted_at: string;
  display_name?: string;
  email?: string;
}

export interface ProjectMembersResponse {
  project_id: string;
  owner: { user_id: string; display_name: string; email: string } | null;
  members: ProjectMember[];
}

export interface MyProjectRoleResponse {
  user_id: string;
  project_role: ProjectRole;
  rbac_role: RbacRole;
}

export interface AuthMeResponse {
  user_id: string;
  email: string;
  display_name: string;
  role: RbacRole;
  permissions: string[];
}

export interface SetupStepStatus {
  complete: boolean;
  detail: string;
  tables?: Record<string, unknown>;
}

export interface SetupStatus {
  is_configured: boolean;
  steps: {
    data_connection: SetupStepStatus;
    data_tables: SetupStepStatus;
    organization: SetupStepStatus;
    first_project: SetupStepStatus;
  };
}

export const api = {
  listProjects: () => get<Project[]>('/projects'),
  getProject: (id: string) => get<Project>(`/projects/${id}`),
  createProject: (data: { project_id: string; project_name: string; project_type: string; description: string; reporting_date: string }) =>
    post<Project>('/projects', data),
  advanceStep: (pid: string, action: string, user: string, detail: string, status = 'completed') =>
    post<Project>(`/projects/${pid}/advance`, { action, user, detail, status }),
  saveOverlays: (pid: string, overlays: Overlay[], comment: string) =>
    post<Project>(`/projects/${pid}/overlays`, { overlays, comment }),
  saveWeights: (pid: string, weights: Record<string, number>) =>
    post<Project>(`/projects/${pid}/scenario-weights`, { weights }),
  signOff: (pid: string, name: string, attestation_data?: Record<string, any>) =>
    post<Project>(`/projects/${pid}/sign-off`, { name, attestation_data }),
  verifyHash: (pid: string) =>
    get<{ status: string; stored_hash: string; computed_hash: string; match: boolean; signed_off_by: string; signed_off_at: string }>(`/projects/${pid}/verify-hash`),
  approvalHistory: (pid: string) =>
    get<any[]>(`/projects/${pid}/approval-history`),
  resetProject: (pid: string) =>
    post<Project>(`/projects/${pid}/reset`),

  portfolioSummary: () => get<any[]>('/data/portfolio-summary'),
  stageDistribution: () => get<any[]>('/data/stage-distribution'),
  borrowerSegments: () => get<any[]>('/data/borrower-segments'),
  dpdDistribution: () => get<any[]>('/data/dpd-distribution'),
  pdDistribution: () => get<any[]>('/data/pd-distribution'),
  stageByProduct: () => get<any[]>('/data/stage-by-product'),
  dqResults: () => get<any[]>('/data/dq-results'),
  dqSummary: () => get<any[]>('/data/dq-summary'),
  glReconciliation: () => get<any[]>('/data/gl-reconciliation'),
  eclByProduct: () => get<any[]>('/data/ecl-by-product'),
  scenarioSummary: () => get<any[]>('/data/scenario-summary'),
  eclByScenarioProduct: () => get<any[]>('/data/ecl-by-scenario-product'),
  lossAllowanceByStage: () => get<any[]>('/data/loss-allowance-by-stage'),
  topExposures: (limit = 20) => get<any[]>(`/data/top-exposures?limit=${limit}`),
  stageMigration: () => get<any[]>('/data/stage-migration'),
  creditRiskExposure: () => get<any[]>('/data/credit-risk-exposure'),
  sensitivityData: () => get<any[]>('/data/sensitivity'),
  scenarioComparison: () => get<any[]>('/data/scenario-comparison'),
  mcDistribution: () => get<any[]>('/data/mc-distribution'),
  stressByStage: () => get<any[]>('/data/stress-by-stage'),
  vintagePerformance: () => get<any[]>('/data/vintage-performance'),
  vintageByProduct: () => get<any[]>('/data/vintage-by-product'),
  concentrationBySegment: () => get<any[]>('/data/concentration-by-segment'),
  concentrationByProductStage: () => get<any[]>('/data/concentration-by-product-stage'),
  topConcentrationRisk: () => get<any[]>('/data/top-concentration-risk'),
  loansByProduct: (product: string) => get<any[]>(`/data/loans-by-product/${encodeURIComponent(product)}`),
  loansByStage: (stage: number) => get<any[]>(`/data/loans-by-stage/${stage}`),

  satelliteModelComparison: (runId?: string) => get<any[]>(`/data/satellite-model-comparison${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`),
  satelliteModelSelected: (runId?: string) => get<any[]>(`/data/satellite-model-selected${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`),
  modelRuns: (runType?: string) => get<any[]>(`/model-runs${runType ? `?run_type=${encodeURIComponent(runType)}` : ''}`),
  modelRun: (runId: string) => get<any>(`/model-runs/${encodeURIComponent(runId)}`),
  saveModelRun: (data: any) => post<any>('/model-runs', data),
  cohortSummary: () => get<any[]>('/data/cohort-summary'),
  cohortSummaryByProduct: (product: string) => get<any[]>(`/data/cohort-summary/${encodeURIComponent(product)}`),
  drillDownDimensions: () => get<{ key: string; label: string }[]>('/data/drill-down-dimensions'),
  eclByCohort: (product: string, dimension = 'risk_band') =>
    get<any[]>(`/data/ecl-by-cohort?product=${encodeURIComponent(product)}&dimension=${encodeURIComponent(dimension)}`),
  stageByCohort: (product: string) => get<any[]>(`/data/stage-by-cohort?product=${encodeURIComponent(product)}`),
  portfolioByCohort: (product: string, dimension = 'risk_band') =>
    get<any[]>(`/data/portfolio-by-cohort?product=${encodeURIComponent(product)}&dimension=${encodeURIComponent(dimension)}`),
  eclByProductDrilldown: () => get<any[]>('/data/ecl-by-product-drilldown'),
  eclByStageProduct: (stage: number) => get<any[]>(`/data/ecl-by-stage-product/${stage}`),
  eclByScenarioProductDetail: (scenario: string) => get<any[]>(`/data/ecl-by-scenario-product-detail?scenario=${encodeURIComponent(scenario)}`),

  getAttribution: (projectId: string) => get<any>(`/data/attribution/${encodeURIComponent(projectId)}`),
  computeAttribution: (projectId: string) => post<any>(`/data/attribution/${encodeURIComponent(projectId)}/compute`),
  getAttributionHistory: (projectId: string) => get<any[]>(`/data/attribution/${encodeURIComponent(projectId)}/history`),

  triggerJob: (jobKey: string, enabledModels?: string[]) =>
    post<any>('/jobs/trigger', { job_key: jobKey, enabled_models: enabledModels }),
  jobRunStatus: (runId: number) => get<any>(`/jobs/run/${runId}`),
  jobRuns: (jobKey: string, limit = 10) => get<any[]>(`/jobs/runs/${jobKey}?limit=${limit}`),
  jobsConfig: () => get<any>('/jobs/config'),

  // Model Registry
  listModels: (modelType?: string, status?: string) => {
    const params = new URLSearchParams();
    if (modelType) params.set('model_type', modelType);
    if (status) params.set('status', status);
    const qs = params.toString();
    return get<ModelRegistryEntry[]>(`/models${qs ? `?${qs}` : ''}`);
  },
  getModel: (modelId: string) => get<ModelRegistryEntry>(`/models/${encodeURIComponent(modelId)}`),
  registerModel: (data: Partial<ModelRegistryEntry>) => post<ModelRegistryEntry>('/models', data),
  updateModelStatus: (modelId: string, status: string, user: string, comment = '') =>
    put<ModelRegistryEntry>(`/models/${encodeURIComponent(modelId)}/status`, { status, user, comment }),
  promoteChampion: (modelId: string, user: string) =>
    post<ModelRegistryEntry>(`/models/${encodeURIComponent(modelId)}/promote`, { user }),
  compareModels: (modelIds: string[]) => post<ModelRegistryEntry[]>('/models/compare', { model_ids: modelIds }),
  getModelAudit: (modelId: string) => get<ModelAuditEntry[]>(`/models/${encodeURIComponent(modelId)}/audit`),

  // GL Journal Entries
  glGenerateJournals: (projectId: string, user = 'system') =>
    post<GLJournal>(`/gl/generate/${encodeURIComponent(projectId)}`, { user }),
  glListJournals: (projectId: string) =>
    get<GLJournal[]>(`/gl/journals/${encodeURIComponent(projectId)}`),
  glGetJournal: (journalId: string) =>
    get<GLJournal>(`/gl/journal/${encodeURIComponent(journalId)}`),
  glPostJournal: (journalId: string, user: string) =>
    post<GLJournal>(`/gl/journal/${encodeURIComponent(journalId)}/post`, { user }),
  glReverseJournal: (journalId: string, user: string, reason = '') =>
    post<GLJournal>(`/gl/journal/${encodeURIComponent(journalId)}/reverse`, { user, reason }),
  glTrialBalance: (projectId: string) =>
    get<GLTrialBalanceRow[]>(`/gl/trial-balance/${encodeURIComponent(projectId)}`),
  glChartOfAccounts: () =>
    get<GLAccount[]>('/gl/chart-of-accounts'),

  // Markov Chain
  markovEstimate: (productType?: string, segment?: string) =>
    post<any>('/markov/estimate', { product_type: productType || null, segment: segment || null }),
  markovListMatrices: (productType?: string) =>
    get<any[]>(`/markov/matrices${productType ? `?product_type=${encodeURIComponent(productType)}` : ''}`),
  markovGetMatrix: (matrixId: string) =>
    get<any>(`/markov/matrix/${encodeURIComponent(matrixId)}`),
  markovForecast: (matrixId: string, initialDistribution: number[], horizonMonths: number) =>
    post<any>('/markov/forecast', { matrix_id: matrixId, initial_distribution: initialDistribution, horizon_months: horizonMonths }),
  markovLifetimePd: (matrixId: string, maxMonths = 60) =>
    get<any>(`/markov/lifetime-pd/${encodeURIComponent(matrixId)}?max_months=${maxMonths}`),
  markovCompare: (matrixIds: string[]) =>
    post<any[]>('/markov/compare', { matrix_ids: matrixIds }),

  // Backtesting
  runBacktest: (modelType: string, config: Record<string, any> = {}) =>
    post<BacktestResult>('/backtest/run', { model_type: modelType, config }),
  listBacktests: (modelType?: string) => {
    const qs = modelType ? `?model_type=${encodeURIComponent(modelType)}` : '';
    return get<BacktestResult[]>(`/backtest/results${qs}`);
  },
  getBacktest: (backtestId: string) =>
    get<BacktestResult>(`/backtest/${encodeURIComponent(backtestId)}`),
  backtestTrend: (modelType: string) =>
    get<BacktestTrendPoint[]>(`/backtest/trend/${encodeURIComponent(modelType)}`),

  // Hazard Models
  hazardEstimate: (modelType: string, productType?: string, segment?: string) =>
    post<any>('/hazard/estimate', { model_type: modelType, product_type: productType, segment }),
  hazardListModels: (modelType?: string, productType?: string) => {
    const params = new URLSearchParams();
    if (modelType) params.set('model_type', modelType);
    if (productType) params.set('product_type', productType);
    const qs = params.toString();
    return get<any[]>(`/hazard/models${qs ? `?${qs}` : ''}`);
  },
  hazardGetModel: (modelId: string) => get<any>(`/hazard/model/${encodeURIComponent(modelId)}`),
  hazardSurvivalCurve: (modelId: string, covariates?: Record<string, number>) =>
    post<any>('/hazard/survival-curve', { model_id: modelId, covariates }),
  hazardTermStructure: (modelId: string, maxMonths = 60) =>
    get<any>(`/hazard/term-structure/${encodeURIComponent(modelId)}?max_months=${maxMonths}`),
  hazardCompare: (modelIds: string[]) =>
    post<any>('/hazard/compare', { model_ids: modelIds }),

  simulationDefaults: async () => {
    const res = await fetch('/api/simulation-defaults');
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },
  runSimulation: async (config: Record<string, any>) => {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },

  simulateStream: (config: Record<string, any>, onProgress: (event: Record<string, any>) => void, signal?: AbortSignal): Promise<Record<string, any>> => {
    return new Promise((resolve, reject) => {
      fetch('/api/simulate-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
        signal,
      }).then(response => {
        if (!response.ok) {
          response.text().then(t => reject(new Error(`API ${response.status}: ${t}`))).catch(() => reject(new Error(`API ${response.status}`)));
          return;
        }
        const reader = response.body?.getReader();
        if (!reader) { reject(new Error('No response body')); return; }
        const decoder = new TextDecoder();
        let buffer = '';

        function read() {
          reader!.read().then(({ done, value }) => {
            if (done) return;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const event = JSON.parse(line.slice(6));
                  if (event.type === 'progress') {
                    onProgress(event);
                  } else if (event.type === 'result') {
                    resolve(event.data);
                  } else if (event.type === 'error') {
                    reject(new Error(event.message));
                  }
                } catch { /* skip malformed SSE lines */ }
              }
            }
            read();
          }).catch(reject);
        }
        read();
      }).catch(reject);
    });
  },

  // Regulatory Reports
  generateReport: (projectId: string, reportType: string, user = 'system') =>
    post<any>(`/reports/generate/${encodeURIComponent(projectId)}`, { report_type: reportType, user }),
  listReports: (projectId?: string, reportType?: string) => {
    const params = new URLSearchParams();
    if (projectId) params.set('project_id', projectId);
    if (reportType) params.set('report_type', reportType);
    const qs = params.toString();
    return get<any[]>(`/reports${qs ? `?${qs}` : ''}`);
  },
  getReport: (reportId: string) => get<any>(`/reports/${encodeURIComponent(reportId)}`),
  exportReportCsv: (reportId: string) =>
    fetch(`/api/reports/${encodeURIComponent(reportId)}/export`).then(r => {
      if (!r.ok) throw new Error(`Export failed: ${r.status}`);
      return r.blob();
    }),
  finalizeReport: (reportId: string) =>
    post<any>(`/reports/${encodeURIComponent(reportId)}/finalize`),

  simulateJob: async (config: any) => {
    const res = await fetch('/api/simulate-job', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },

  validateSimulation: async (config: any) => {
    const res = await fetch('/api/simulate-validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },

  // RBAC & Approval Workflow
  rbacListUsers: (role?: string) => {
    const qs = role ? `?role=${encodeURIComponent(role)}` : '';
    return get<RbacUser[]>(`/rbac/users${qs}`);
  },
  rbacGetUser: (userId: string) => get<RbacUser>(`/rbac/users/${encodeURIComponent(userId)}`),
  rbacListApprovals: (status?: string, assignedTo?: string, type?: string) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (assignedTo) params.set('assigned_to', assignedTo);
    if (type) params.set('type', type);
    const qs = params.toString();
    return get<ApprovalRequest[]>(`/rbac/approvals${qs ? `?${qs}` : ''}`);
  },
  rbacCreateApproval: (data: {
    request_type: string; entity_id: string; entity_type?: string;
    requested_by: string; assigned_to?: string; priority?: string;
    due_date?: string; comments?: string;
  }) => post<ApprovalRequest>('/rbac/approvals', data),
  rbacApprove: (requestId: string, userId: string, comment = '') =>
    post<ApprovalRequest>(`/rbac/approvals/${encodeURIComponent(requestId)}/approve`, { user_id: userId, comment }),
  rbacReject: (requestId: string, userId: string, comment = '') =>
    post<ApprovalRequest>(`/rbac/approvals/${encodeURIComponent(requestId)}/reject`, { user_id: userId, comment }),
  rbacApprovalHistory: (entityId: string) =>
    get<ApprovalRequest[]>(`/rbac/approvals/history/${encodeURIComponent(entityId)}`),
  rbacPermissions: (userId: string) =>
    get<{ user_id: string; role: string; permissions: string[] }>(`/rbac/permissions/${encodeURIComponent(userId)}`),

  // Advanced ECL Features
  computeCureRates: (productType?: string) =>
    post<any>('/advanced/cure-rates/compute', { product_type: productType || null }),
  listCureAnalyses: () => get<any[]>('/advanced/cure-rates'),
  getCureAnalysis: (analysisId: string) => get<any>(`/advanced/cure-rates/${encodeURIComponent(analysisId)}`),

  computeCCF: (productType?: string) =>
    post<any>('/advanced/ccf/compute', { product_type: productType || null }),
  listCCFAnalyses: () => get<any[]>('/advanced/ccf'),
  getCCFAnalysis: (analysisId: string) => get<any>(`/advanced/ccf/${encodeURIComponent(analysisId)}`),

  computeCollateral: (productType?: string) =>
    post<any>('/advanced/collateral/compute', { product_type: productType || null }),
  listCollateralAnalyses: () => get<any[]>('/advanced/collateral'),
  getCollateralAnalysis: (analysisId: string) => get<any>(`/advanced/collateral/${encodeURIComponent(analysisId)}`),

  // Setup Wizard
  setupStatus: () => get<SetupStatus>('/setup/status'),
  setupValidateTables: () => post<any>('/setup/validate-tables'),
  setupSeedSampleData: () => post<any>('/setup/seed-sample-data'),
  setupComplete: (user = 'admin') => post<SetupStatus>('/setup/complete', { user }),
  setupReset: () => post<SetupStatus>('/setup/reset'),

  // Data Mapping
  dataMappingCatalogs: () => get<any[]>('/data-mapping/catalogs'),
  dataMappingSchemas: (catalog: string) => get<any[]>(`/data-mapping/schemas/${encodeURIComponent(catalog)}`),
  dataMappingTables: (catalog: string, schema: string) =>
    get<any[]>(`/data-mapping/tables/${encodeURIComponent(catalog)}/${encodeURIComponent(schema)}`),
  dataMappingColumns: (catalog: string, schema: string, table: string) =>
    get<any[]>(`/data-mapping/columns/${encodeURIComponent(catalog)}/${encodeURIComponent(schema)}/${encodeURIComponent(table)}`),
  dataMappingPreview: (sourceTable: string, limit = 10) =>
    post<any>('/data-mapping/preview', { source_table: sourceTable, limit }),
  dataMappingValidate: (tableKey: string, sourceTable: string, mappings: Record<string, string>) =>
    post<any>('/data-mapping/validate', { table_key: tableKey, source_table: sourceTable, mappings }),
  dataMappingSuggest: (tableKey: string, sourceTable: string) =>
    post<any>('/data-mapping/suggest', { table_key: tableKey, source_table: sourceTable }),
  dataMappingApply: (tableKey: string, sourceTable: string, mappings: Record<string, string>, mode = 'overwrite') =>
    post<any>('/data-mapping/apply', { table_key: tableKey, source_table: sourceTable, mappings, mode }),
  dataMappingStatus: () => get<Record<string, any>>('/data-mapping/status'),

  // Admin helpers used by wizard
  healthCheck: () => get<{ status: string; lakebase: string }>('/health'),
  adminAvailableTables: () => get<any[]>('/admin/available-tables'),
  adminAutoDetect: () => get<any>('/admin/auto-detect-workspace'),
  adminConfig: () => get<any>('/admin/config'),
  adminSaveConfig: (data: any) => put<any>('/admin/config', data),
  adminTestConnection: () => post<any>('/admin/test-connection'),

  // Auth & Permissions
  authMe: () => get<AuthMeResponse>('/auth/me'),
  getMyProjectRole: (projectId: string) =>
    get<MyProjectRoleResponse>(`/auth/projects/${encodeURIComponent(projectId)}/my-role`),
  getProjectMembers: (projectId: string) =>
    get<ProjectMembersResponse>(`/projects/${encodeURIComponent(projectId)}/members`),
  addProjectMember: (projectId: string, userId: string, role: string) =>
    post<ProjectMember>(`/projects/${encodeURIComponent(projectId)}/members`, { user_id: userId, role }),
  removeProjectMember: (projectId: string, userId: string) =>
    del<{ removed: boolean; user_id: string; project_id: string }>(`/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(userId)}`),
  transferOwnership: (projectId: string, newOwnerId: string) =>
    post<Project>(`/projects/${encodeURIComponent(projectId)}/transfer-ownership`, { new_owner_id: newOwnerId }),
};
