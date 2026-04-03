// Shared types for Admin page components

export interface ColumnDef {
  name: string;
  type: string;
  description?: string;
  default?: string;
  example?: string;
  constraints?: string;
}

export interface TableConfig {
  source_table: string;
  required?: boolean;
  description?: string;
  mandatory_columns: ColumnDef[];
  optional_columns: ColumnDef[];
  column_mappings: Record<string, string>;
}

export interface SatelliteModel {
  enabled: boolean;
  label: string;
}

export interface LgdAssumption {
  lgd: number;
  cure_rate: number;
}

export interface ScenarioRow {
  key: string;
  name: string;
  weight: number;
  pd_multiplier: number;
  lgd_multiplier: number;
  color: string;
}

export interface AdminConfig {
  data_sources: {
    catalog: string;
    schema: string;
    lakebase_schema: string;
    lakebase_prefix: string;
    tables: Record<string, TableConfig>;
  };
  model: {
    satellite_models: Record<string, SatelliteModel>;
    default_parameters: Record<string, number>;
    sicr_thresholds: Record<string, number>;
    lgd_assumptions: Record<string, LgdAssumption>;
  };
  jobs: {
    workspace_url: string;
    workspace_id: string;
    job_ids: Record<string, number>;
    default_job_params: Record<string, string>;
    compute: { use_serverless: boolean; cluster_spec: string };
  };
  app_settings: {
    organization_name: string;
    organization_legal_name: string;
    logo_url: string;
    currency_code: string;
    currency_symbol: string;
    currency_locale: string;
    country: string;
    reporting_date_format: string;
    reporting_period: string;
    reporting_date: string;
    framework: string;
    framework_mode: string;
    regulatory_framework: string;
    local_regulator: string;
    local_circular: string;
    app_title: string;
    app_subtitle: string;
    model_version: string;
    last_validation: string;
    governance: {
      cfo_name: string;
      cfo_title: string;
      cro_name: string;
      cro_title: string;
      head_credit_risk_name: string;
      head_credit_risk_title: string;
      model_validator_name: string;
      model_validator_title: string;
      external_auditor_firm: string;
      external_auditor_partner: string;
      board_committee: string;
      approval_workflow: string;
      gl_reconciliation_tolerance_pct?: number;
      dq_score_threshold_pct?: number;
    };
    scenarios: ScenarioRow[];
  };
}

// Shared helpers
export const inputCls = 'form-input';
export const labelCls = 'form-label text-slate-600';

export async function fetchJson<T>(url: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`);
  return r.json();
}

export const TYPE_COMPAT: Record<string, string[]> = {
  TEXT: ['text', 'character varying', 'varchar', 'char', 'character', 'name', 'uuid'],
  INT: ['integer', 'bigint', 'smallint', 'numeric', 'int4', 'int8', 'int2'],
  NUMERIC: ['numeric', 'decimal', 'real', 'double precision', 'float4', 'float8', 'integer', 'bigint', 'money'],
  DATE: ['date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone', 'timestamptz'],
  BOOLEAN: ['boolean', 'bool'],
};

export function isTypeCompatible(expectedType: string, actualType: string): boolean {
  const expected = expectedType.toUpperCase();
  const actual = actualType.toLowerCase();
  const compatList = TYPE_COMPAT[expected];
  if (!compatList) return true;
  return compatList.includes(actual);
}

export const CURRENCIES = [
  { code: 'USD', symbol: '$', locale: 'en-US', label: 'US Dollar' },
  { code: 'EUR', symbol: '€', locale: 'de-DE', label: 'Euro' },
  { code: 'GBP', symbol: '£', locale: 'en-GB', label: 'British Pound' },
  { code: 'SGD', symbol: 'S$', locale: 'en-SG', label: 'Singapore Dollar' },
  { code: 'MYR', symbol: 'RM', locale: 'ms-MY', label: 'Malaysian Ringgit' },
  { code: 'JPY', symbol: '¥', locale: 'ja-JP', label: 'Japanese Yen' },
  { code: 'AUD', symbol: 'A$', locale: 'en-AU', label: 'Australian Dollar' },
  { code: 'CAD', symbol: 'C$', locale: 'en-CA', label: 'Canadian Dollar' },
  { code: 'CHF', symbol: 'CHF', locale: 'de-CH', label: 'Swiss Franc' },
  { code: 'HKD', symbol: 'HK$', locale: 'zh-HK', label: 'Hong Kong Dollar' },
  { code: 'INR', symbol: '₹', locale: 'en-IN', label: 'Indian Rupee' },
  { code: 'IDR', symbol: 'Rp', locale: 'id-ID', label: 'Indonesian Rupiah' },
  { code: 'THB', symbol: '฿', locale: 'th-TH', label: 'Thai Baht' },
  { code: 'PHP', symbol: '₱', locale: 'en-PH', label: 'Philippine Peso' },
  { code: 'ZAR', symbol: 'R', locale: 'en-ZA', label: 'South African Rand' },
  { code: 'BRL', symbol: 'R$', locale: 'pt-BR', label: 'Brazilian Real' },
  { code: 'KRW', symbol: '₩', locale: 'ko-KR', label: 'South Korean Won' },
  { code: 'SAR', symbol: 'SAR', locale: 'ar-SA', label: 'Saudi Riyal' },
  { code: 'AED', symbol: 'AED', locale: 'ar-AE', label: 'UAE Dirham' },
];

export const PARAM_LABELS: Record<string, { label: string; help: string }> = {
  n_simulations: { label: 'Monte Carlo Simulations', help: 'Number of random draws per scenario. Higher = more stable but slower.' },
  pd_lgd_correlation: { label: 'PD-LGD Correlation', help: 'Correlation between PD and LGD. Higher values model procyclical LGD.' },
  aging_factor: { label: 'Aging Factor', help: 'Quarterly PD increase for Stage 2/3 loans.' },
  pd_floor: { label: 'PD Floor', help: 'Minimum PD value.' },
  pd_cap: { label: 'PD Cap', help: 'Maximum PD value.' },
  lgd_floor: { label: 'LGD Floor', help: 'Minimum LGD value.' },
  lgd_cap: { label: 'LGD Cap', help: 'Maximum LGD value.' },
};

export const SICR_LABELS: Record<string, { label: string; help: string }> = {
  stage_1_max_dpd: { label: 'Stage 1 Max DPD', help: 'Max days past due to remain in Stage 1. Default: 30.' },
  stage_2_max_dpd: { label: 'Stage 2 Max DPD', help: 'Max days past due for Stage 2. Default: 90.' },
  stage_3_min_dpd: { label: 'Stage 3 Min DPD', help: 'Min days past due for Stage 3. Default: 90.' },
  pd_relative_threshold: { label: 'PD Relative Threshold', help: 'If current PD / origination PD exceeds this, trigger SICR.' },
  pd_absolute_threshold: { label: 'PD Absolute Threshold', help: 'Absolute PD increase that triggers SICR.' },
};
