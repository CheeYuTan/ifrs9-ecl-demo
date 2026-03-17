export interface ScenarioConfig {
  label: string;
  color: string;
  gdp: number;
  unemployment: number;
  inflation: number;
  policy_rate: number;
  narrative: string;
}

export const config = {
  bankName: 'Horizon Bank',
  bankLegalName: 'Horizon Bank, Ltd.',
  currency: 'USD',
  currencySymbol: '$',
  currencyLocale: 'en-US',
  country: 'United States',
  logoPath: '/logo.svg',
  defaultProjectId: 'Q4-2025-IFRS9',
  defaultReportingDate: '2025-12-31',
  framework: 'IFRS 9',
  regulatoryFramework: 'IFRS 9 Financial Instruments (2014, amended 2022)',
  localRegulator: 'Central Bank',
  localCircular: 'Regulatory Circular on Credit Risk Provisioning',
  appTitle: 'IFRS 9 ECL Workspace',
  appSubtitle: 'Forward-Looking Credit Loss Management',
  poweredBy: 'Databricks Lakebase',
  modelVersion: 'v4.0',
  lastValidation: 'December 2025',
  scenarios: {
    baseline: {
      label: 'Baseline', color: '#10B981',
      gdp: 6.2, unemployment: 4.8, inflation: 3.5, policy_rate: 5.50,
      narrative: 'Central bank baseline projection with steady growth momentum',
    },
    mild_recovery: {
      label: 'Mild Recovery', color: '#34D399',
      gdp: 6.8, unemployment: 4.3, inflation: 3.2, policy_rate: 5.25,
      narrative: 'Post-pandemic recovery with improving labor market',
    },
    strong_growth: {
      label: 'Strong Growth', color: '#059669',
      gdp: 7.5, unemployment: 3.8, inflation: 3.0, policy_rate: 5.00,
      narrative: 'Infrastructure boom and FDI surge',
    },
    mild_downturn: {
      label: 'Mild Downturn', color: '#F59E0B',
      gdp: 4.5, unemployment: 5.5, inflation: 4.2, policy_rate: 6.00,
      narrative: 'Global trade slowdown with moderate domestic impact',
    },
    adverse: {
      label: 'Adverse', color: '#EF4444',
      gdp: 2.0, unemployment: 7.0, inflation: 5.5, policy_rate: 6.75,
      narrative: 'Regional financial stress with capital outflows',
    },
    stagflation: {
      label: 'Stagflation', color: '#F97316',
      gdp: 1.5, unemployment: 7.5, inflation: 7.0, policy_rate: 7.50,
      narrative: 'Supply-side shock with persistent inflation',
    },
    severely_adverse: {
      label: 'Severely Adverse', color: '#DC2626',
      gdp: -1.0, unemployment: 9.0, inflation: 8.5, policy_rate: 8.00,
      narrative: 'Deep recession with banking sector stress',
    },
    tail_risk: {
      label: 'Tail Risk', color: '#991B1B',
      gdp: -3.5, unemployment: 12.0, inflation: 10.0, policy_rate: 9.00,
      narrative: 'Systemic crisis with sovereign risk contagion',
    },
  } as Record<string, ScenarioConfig>,
};
