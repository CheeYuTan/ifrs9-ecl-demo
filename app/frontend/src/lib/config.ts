export interface ScenarioConfig {
  label: string;
  color: string;
  gdp: number;
  unemployment: number;
  inflation: number;
  policy_rate: number;
  narrative: string;
}

interface GovernanceConfig {
  cfoName: string;
  cfoTitle: string;
  croName: string;
  croTitle: string;
  headCreditRiskName: string;
  headCreditRiskTitle: string;
  modelValidatorName: string;
  modelValidatorTitle: string;
  externalAuditorFirm: string;
  externalAuditorPartner: string;
  boardCommittee: string;
  approvalWorkflow: string;
  glReconciliationTolerancePct: number;
  dqScoreThresholdPct: number;
}

interface AppConfig {
  bankName: string;
  bankLegalName: string;
  logoUrl: string;
  currency: string;
  currencySymbol: string;
  currencyLocale: string;
  country: string;
  logoPath: string;
  defaultProjectId: string;
  defaultReportingDate: string;
  reportingPeriod: string;
  framework: string;
  regulatoryFramework: string;
  localRegulator: string;
  localCircular: string;
  appTitle: string;
  appSubtitle: string;
  poweredBy: string;
  modelVersion: string;
  lastValidation: string;
  governance: GovernanceConfig;
  scenarios: Record<string, ScenarioConfig>;
}

const DEFAULTS: AppConfig = {
  bankName: 'Horizon Bank',
  bankLegalName: 'Horizon Bank, Ltd.',
  logoUrl: '',
  currency: 'USD',
  currencySymbol: '$',
  currencyLocale: 'en-US',
  country: 'United States',
  logoPath: '/logo.svg',
  defaultProjectId: 'Q4-2025-IFRS9',
  defaultReportingDate: '2025-12-31',
  reportingPeriod: 'Q4 2025',
  framework: 'IFRS 9',
  regulatoryFramework: 'IFRS 9 Financial Instruments (2014, amended 2022)',
  localRegulator: 'Central Bank',
  localCircular: 'Regulatory Circular on Credit Risk Provisioning',
  appTitle: 'IFRS 9 ECL Workspace',
  appSubtitle: 'Forward-Looking Credit Loss Management',
  poweredBy: 'Databricks Lakebase',
  modelVersion: 'v4.0',
  lastValidation: 'December 2025',
  governance: {
    cfoName: '',
    cfoTitle: 'Chief Financial Officer',
    croName: '',
    croTitle: 'Chief Risk Officer',
    headCreditRiskName: '',
    headCreditRiskTitle: 'Head of Credit Risk',
    modelValidatorName: '',
    modelValidatorTitle: 'Independent Model Validator',
    externalAuditorFirm: '',
    externalAuditorPartner: '',
    boardCommittee: 'Board Risk Committee',
    approvalWorkflow: 'Maker → Checker → Approver → Sign-Off',
    glReconciliationTolerancePct: 0.50,
    dqScoreThresholdPct: 90.0,
  },
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

export const config: AppConfig = { ...DEFAULTS };

function applyRemoteConfig(remote: any): void {
  const s = remote?.app_settings;
  if (!s) return;

  if (s.organization_name) config.bankName = s.organization_name;
  if (s.organization_legal_name) config.bankLegalName = s.organization_legal_name;
  if (s.logo_url) config.logoUrl = s.logo_url;
  if (s.currency_code) config.currency = s.currency_code;
  if (s.currency_symbol) config.currencySymbol = s.currency_symbol;
  if (s.currency_locale) config.currencyLocale = s.currency_locale;
  if (s.country) config.country = s.country;
  if (s.reporting_period) config.reportingPeriod = s.reporting_period;
  if (s.reporting_date) config.defaultReportingDate = s.reporting_date;
  if (s.framework) config.framework = s.framework;
  if (s.regulatory_framework) config.regulatoryFramework = s.regulatory_framework;
  if (s.local_regulator) config.localRegulator = s.local_regulator;
  if (s.local_circular) config.localCircular = s.local_circular;
  if (s.app_title) config.appTitle = s.app_title;
  if (s.app_subtitle) config.appSubtitle = s.app_subtitle;
  if (s.model_version) config.modelVersion = s.model_version;
  if (s.last_validation) config.lastValidation = s.last_validation;

  if (s.governance) {
    const g = s.governance;
    const cg = config.governance;
    if (g.cfo_name) cg.cfoName = g.cfo_name;
    if (g.cfo_title) cg.cfoTitle = g.cfo_title;
    if (g.cro_name) cg.croName = g.cro_name;
    if (g.cro_title) cg.croTitle = g.cro_title;
    if (g.head_credit_risk_name) cg.headCreditRiskName = g.head_credit_risk_name;
    if (g.head_credit_risk_title) cg.headCreditRiskTitle = g.head_credit_risk_title;
    if (g.model_validator_name) cg.modelValidatorName = g.model_validator_name;
    if (g.model_validator_title) cg.modelValidatorTitle = g.model_validator_title;
    if (g.external_auditor_firm) cg.externalAuditorFirm = g.external_auditor_firm;
    if (g.external_auditor_partner) cg.externalAuditorPartner = g.external_auditor_partner;
    if (g.board_committee) cg.boardCommittee = g.board_committee;
    if (g.approval_workflow) cg.approvalWorkflow = g.approval_workflow;
    if (g.gl_reconciliation_tolerance_pct != null) cg.glReconciliationTolerancePct = Number(g.gl_reconciliation_tolerance_pct);
    if (g.dq_score_threshold_pct != null) cg.dqScoreThresholdPct = Number(g.dq_score_threshold_pct);
  }

  if (Array.isArray(s.scenarios)) {
    const mapped: Record<string, ScenarioConfig> = {};
    for (const sc of s.scenarios) {
      const base = DEFAULTS.scenarios[sc.key] || {
        gdp: 0, unemployment: 0, inflation: 0, policy_rate: 0, narrative: '',
      };
      mapped[sc.key] = {
        ...base,
        label: sc.name || base.label || sc.key,
        color: sc.color || base.color || '#6B7280',
      };
    }
    if (Object.keys(mapped).length > 0) {
      Object.assign(config.scenarios, mapped);
    }
  }
}

let _loaded = false;

export async function loadConfig(): Promise<AppConfig> {
  if (_loaded) return config;
  try {
    const res = await fetch('/api/admin/config');
    if (res.ok) {
      const remote = await res.json();
      applyRemoteConfig(remote);
    }
  } catch {
    // Fall back to defaults silently
  }
  _loaded = true;
  return config;
}
