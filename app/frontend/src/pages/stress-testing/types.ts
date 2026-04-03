import type { ReactNode } from 'react';
import { Dice5, Activity, TrendingUp, AlertTriangle, Shield } from 'lucide-react';
import { createElement } from 'react';

/* ── Shared types ─────────────────────────────────────────────── */

export type SubTabKey = 'montecarlo' | 'sensitivity' | 'vintage' | 'concentration' | 'migration';

export interface SubTab {
  key: SubTabKey;
  label: string;
  icon: ReactNode;
}

export const SUB_TABS: SubTab[] = [
  { key: 'montecarlo', label: 'Monte Carlo Simulation', icon: createElement(Dice5, { size: 14 }) },
  { key: 'sensitivity', label: 'Sensitivity Analysis', icon: createElement(Activity, { size: 14 }) },
  { key: 'vintage', label: 'Vintage Analysis', icon: createElement(TrendingUp, { size: 14 }) },
  { key: 'concentration', label: 'Concentration Risk', icon: createElement(AlertTriangle, { size: 14 }) },
  { key: 'migration', label: 'Stage Migration Sim', icon: createElement(Shield, { size: 14 }) },
];

/** Format a numeric value as a signed percentage string, e.g. "+2.3%" or "-1.0%" */
export const safeFmt = (v: any, decimals = 1): string => {
  const n = Number(v);
  return isFinite(n) ? `${n >= 0 ? '+' : ''}${n.toFixed(decimals)}%` : '\u2014';
};

/* ── Shared prop shapes ───────────────────────────────────────── */

export interface McChartDatum {
  scenario: string;
  scenarioKey: string;
  weight: number;
  mean: number;
  p50: number;
  p75: number;
  p95: number;
  p99: number;
  pd_mult: number;
  lgd_mult: number;
  pd_vol: number;
  lgd_vol: number;
  n_sims: number;
  spread: number;
}

export interface StressedDatum {
  product_type: string;
  loan_count: number;
  base_ecl: number;
  stressed_ecl: number;
  delta: number;
  delta_pct: number;
}

export interface MigrationDatum {
  name: string;
  stage: number;
  base_ecl: number;
  adjusted_ecl: number;
  loan_count: number;
  total_gca: number;
}

export interface WaterfallDatum {
  name: string;
  value: number;
  fill: string;
}
