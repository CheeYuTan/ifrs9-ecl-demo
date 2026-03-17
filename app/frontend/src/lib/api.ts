const BASE = '/api';

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
  signOff: (pid: string, name: string) =>
    post<Project>(`/projects/${pid}/sign-off`, { name }),
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

  simulationDefaults: async () => {
    const res = await fetch('/api/simulation-defaults');
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },
  runSimulation: async (config: any) => {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },

  simulateStream: (config: any, onProgress: (event: any) => void, signal?: AbortSignal): Promise<any> => {
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

  validateSimulation: async (config: any) => {
    const res = await fetch('/api/simulate-validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },
};
