import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './api';

const mockJsonResponse = (data: unknown, ok = true, status = 200) => ({
  ok,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
});

describe('api', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('GET endpoints', () => {
    it('listProjects calls /api/projects', async () => {
      const projects = [{ project_id: 'p1' }];
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse(projects) as Response);
      const result = await api.listProjects();
      expect(fetch).toHaveBeenCalledWith('/api/projects');
      expect(result).toEqual(projects);
    });

    it('getProject calls /api/projects/:id', async () => {
      const project = { project_id: 'p1' };
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse(project) as Response);
      const result = await api.getProject('p1');
      expect(fetch).toHaveBeenCalledWith('/api/projects/p1');
      expect(result).toEqual(project);
    });

    it('portfolioSummary calls correct endpoint', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse([]) as Response);
      await api.portfolioSummary();
      expect(fetch).toHaveBeenCalledWith('/api/data/portfolio-summary');
    });

    it('topExposures passes limit parameter', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse([]) as Response);
      await api.topExposures(50);
      expect(fetch).toHaveBeenCalledWith('/api/data/top-exposures?limit=50');
    });

    it('loansByProduct encodes the product name', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse([]) as Response);
      await api.loansByProduct('Home Loans');
      expect(fetch).toHaveBeenCalledWith('/api/data/loans-by-product/Home%20Loans');
    });

    it('jobRuns passes job key and limit', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse([]) as Response);
      await api.jobRuns('satellite', 5);
      expect(fetch).toHaveBeenCalledWith('/api/jobs/runs/satellite?limit=5');
    });
  });

  describe('POST endpoints', () => {
    it('createProject sends POST with body', async () => {
      const data = {
        project_id: 'p1',
        project_name: 'Test',
        project_type: 'IFRS9',
        description: 'desc',
        reporting_date: '2025-12-31',
      };
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({ project_id: 'p1' }) as Response);
      await api.createProject(data);
      expect(fetch).toHaveBeenCalledWith('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    });

    it('advanceStep sends correct payload', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({}) as Response);
      await api.advanceStep('p1', 'complete', 'admin', 'done');
      expect(fetch).toHaveBeenCalledWith('/api/projects/p1/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'complete', user: 'admin', detail: 'done', status: 'completed' }),
      });
    });

    it('saveWeights sends weights payload', async () => {
      const weights = { baseline: 0.4, adverse: 0.3, severely_adverse: 0.3 };
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({}) as Response);
      await api.saveWeights('p1', weights);
      expect(fetch).toHaveBeenCalledWith('/api/projects/p1/scenario-weights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weights }),
      });
    });

    it('signOff sends name', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({}) as Response);
      await api.signOff('p1', 'John Doe');
      expect(fetch).toHaveBeenCalledWith('/api/projects/p1/sign-off', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'John Doe' }),
      });
    });

    it('resetProject sends POST with no body', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({}) as Response);
      await api.resetProject('p1');
      expect(fetch).toHaveBeenCalledWith('/api/projects/p1/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: undefined,
      });
    });

    it('triggerJob sends job_key and enabled_models', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({}) as Response);
      await api.triggerJob('satellite', ['lgd', 'pd']);
      expect(fetch).toHaveBeenCalledWith('/api/jobs/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_key: 'satellite', enabled_models: ['lgd', 'pd'] }),
      });
    });
  });

  describe('error handling', () => {
    it('throws on non-ok GET response', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse('Not Found', false, 404) as Response);
      await expect(api.listProjects()).rejects.toThrow('API 404');
    });

    it('throws on non-ok POST response', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse('Bad Request', false, 400) as Response);
      await expect(api.resetProject('p1')).rejects.toThrow('API 400');
    });
  });

  describe('simulation endpoints', () => {
    it('simulationDefaults calls /api/simulation-defaults', async () => {
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({ defaults: true }) as Response);
      const result = await api.simulationDefaults();
      expect(fetch).toHaveBeenCalledWith('/api/simulation-defaults');
      expect(result).toEqual({ defaults: true });
    });

    it('runSimulation sends POST to /api/simulate', async () => {
      const config = { scenarios: ['baseline'] };
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({ result: 'ok' }) as Response);
      const result = await api.runSimulation(config);
      expect(fetch).toHaveBeenCalledWith('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      expect(result).toEqual({ result: 'ok' });
    });

    it('validateSimulation sends POST to /api/simulate-validate', async () => {
      const config = { scenarios: ['baseline'] };
      vi.mocked(fetch).mockResolvedValue(mockJsonResponse({ valid: true }) as Response);
      const result = await api.validateSimulation(config);
      expect(fetch).toHaveBeenCalledWith('/api/simulate-validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      expect(result).toEqual({ valid: true });
    });
  });
});
