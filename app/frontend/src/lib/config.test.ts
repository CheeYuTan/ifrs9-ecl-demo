import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('config', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('exports default config values', async () => {
    const { config } = await import('./config');
    expect(config.bankName).toBe('Horizon Bank');
    expect(config.currency).toBe('USD');
    expect(config.currencySymbol).toBe('$');
    expect(config.currencyLocale).toBe('en-US');
    expect(config.framework).toBe('IFRS 9');
    expect(config.appTitle).toBe('IFRS 9 ECL Workspace');
  });

  it('has default scenarios', async () => {
    const { config } = await import('./config');
    expect(config.scenarios).toBeDefined();
    expect(config.scenarios.baseline).toBeDefined();
    expect(config.scenarios.baseline.label).toBe('Baseline');
    expect(config.scenarios.adverse).toBeDefined();
    expect(config.scenarios.adverse.label).toBe('Adverse');
  });

  it('scenario configs have required fields', async () => {
    const { config } = await import('./config');
    for (const [, scenario] of Object.entries(config.scenarios)) {
      expect(scenario).toHaveProperty('label');
      expect(scenario).toHaveProperty('color');
      expect(scenario).toHaveProperty('gdp');
      expect(scenario).toHaveProperty('unemployment');
      expect(scenario).toHaveProperty('inflation');
      expect(scenario).toHaveProperty('policy_rate');
      expect(scenario).toHaveProperty('narrative');
    }
  });

  it('has all expected scenario keys', async () => {
    const { config } = await import('./config');
    const expectedKeys = [
      'baseline', 'mild_recovery', 'strong_growth', 'mild_downturn',
      'adverse', 'stagflation', 'severely_adverse', 'tail_risk',
    ];
    for (const key of expectedKeys) {
      expect(config.scenarios[key]).toBeDefined();
    }
  });

  it('loadConfig returns config on fetch failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')));
    const { loadConfig } = await import('./config');
    const result = await loadConfig();
    expect(result).toBeDefined();
    expect(result.bankName).toBe('Horizon Bank');
    vi.unstubAllGlobals();
  });

  it('loadConfig applies remote config when fetch succeeds', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        app_settings: {
          organization_name: 'Test Bank',
          currency_code: 'EUR',
          currency_symbol: '€',
        },
      }),
    }));
    const { loadConfig, config } = await import('./config');
    await loadConfig();
    expect(config.bankName).toBe('Test Bank');
    expect(config.currency).toBe('EUR');
    expect(config.currencySymbol).toBe('€');
    vi.unstubAllGlobals();
  });

  it('has default governance config', async () => {
    const { config } = await import('./config');
    expect(config.governance).toBeDefined();
    expect(config.governance.cfoTitle).toBe('Chief Financial Officer');
    expect(config.governance.croTitle).toBe('Chief Risk Officer');
    expect(config.governance.boardCommittee).toBe('Board Risk Committee');
  });

  it('loadConfig applies remote governance config', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        app_settings: {
          governance: {
            cfo_name: 'Jane Doe',
            cro_name: 'John Smith',
            external_auditor_firm: 'PwC',
          },
        },
      }),
    }));
    const { loadConfig, config } = await import('./config');
    await loadConfig();
    expect(config.governance.cfoName).toBe('Jane Doe');
    expect(config.governance.croName).toBe('John Smith');
    expect(config.governance.externalAuditorFirm).toBe('PwC');
    vi.unstubAllGlobals();
  });

  it('loadConfig only fetches once', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ app_settings: {} }),
    });
    vi.stubGlobal('fetch', mockFetch);
    const { loadConfig } = await import('./config');
    await loadConfig();
    await loadConfig();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    vi.unstubAllGlobals();
  });
});
