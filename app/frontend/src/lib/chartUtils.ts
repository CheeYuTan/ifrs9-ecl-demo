import { config } from './config';
import { api } from './api';

// ─── Axis helpers ────────────────────────────────────────────────────────────

export function chartAxisProps(itemCount: number): {
  angle: number;
  textAnchor: 'end';
  height: number;
  fontSize: number;
  tickMargin: number;
} {
  if (itemCount > 10) return { angle: -60, textAnchor: 'end', height: 100, fontSize: 8, tickMargin: 8 };
  if (itemCount > 6) return { angle: -45, textAnchor: 'end', height: 80, fontSize: 9, tickMargin: 10 };
  return { angle: -10, textAnchor: 'end', height: 50, fontSize: 10, tickMargin: 12 };
}

export const CHART_MARGIN = { left: 10, right: 10, bottom: 20, top: 5 } as const;

export const X_AXIS_DEFAULTS = {
  axisLine: false,
  tickLine: false,
  tickMargin: 12,
  tick: { fontSize: 11, fill: '#475569' },
} as const;

// ─── Color constants ─────────────────────────────────────────────────────────

export const STAGE_COLORS: Record<number, string> = { 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' };
export const STAGE_COLORS_ARRAY = ['#10B981', '#F59E0B', '#EF4444'];
export const FALLBACK_COLORS = ['#6B7280', '#9CA3AF', '#F59E0B', '#8B5CF6', '#EC4899'];

// ─── Scenario helpers ────────────────────────────────────────────────────────

export function buildScenarioColorMap(scenarioData: any[]): Record<string, string> {
  const fromConfig = Object.fromEntries(
    Object.entries(config.scenarios).map(([k, v]) => [k, v.color])
  );
  const fromData = Object.fromEntries(
    scenarioData
      .filter(s => !fromConfig[s.scenario])
      .map((s, i) => [s.scenario, FALLBACK_COLORS[i % FALLBACK_COLORS.length]])
  );
  return { ...fromConfig, ...fromData, base: '#10B981' };
}

export function getScenarioLabels(): Record<string, string> {
  return Object.fromEntries(
    Object.entries(config.scenarios).map(([k, v]) => [k, v.label])
  );
}

export function scenarioGridClass(count: number): string {
  if (count <= 3) return 'grid-cols-1 md:grid-cols-3';
  if (count <= 6) return 'grid-cols-2 md:grid-cols-3';
  if (count <= 8) return 'grid-cols-2 md:grid-cols-4';
  return 'grid-cols-2 md:grid-cols-4 lg:grid-cols-5';
}

export function pivotScenarioByProduct(
  scenByProduct: any[],
): any[] {
  const products = [...new Set(scenByProduct.map(r => r.product_type))];
  const scenarios = [...new Set(scenByProduct.map(r => r.scenario))];
  return products.map(p => {
    const row: any = {
      product: String(p).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      _rawProduct: p,
    };
    scenarios.forEach(s => {
      const match = scenByProduct.find(r => r.product_type === p && r.scenario === s);
      row[s] = Number(match?.total_ecl) || 0;
    });
    return row;
  });
}

// ─── Categorical axis sorting ────────────────────────────────────────────────

/** Canonical order for credit grades (best to worst). */
const CREDIT_GRADE_ORDER: Record<string, number> = {
  'AAA': 0, 'AA+': 1, 'AA': 2, 'AA-': 3,
  'A+': 4, 'A': 5, 'A-': 6,
  'BBB+': 7, 'BBB': 8, 'BBB-': 9,
  'BB+': 10, 'BB': 11, 'BB-': 12,
  'B+': 13, 'B': 14, 'B-': 15,
  'CCC+': 16, 'CCC': 17, 'CCC-': 18,
  'CC': 19, 'C': 20, 'D': 21, 'NR': 22,
};

function leadingNumber(s: string): number | null {
  const m = s.match(/^(\d+)/);
  return m ? Number(m[1]) : null;
}

/**
 * Sort chart data by `name` using domain-aware ordering:
 *  - Credit grades: AAA, AA, A, BBB, BB, B, CCC (best to worst)
 *  - Numeric-prefixed labels (age groups, DPD buckets, vintage years): ascending
 *    Items without numeric prefixes (e.g. "Unknown", "Other") are placed at the end.
 *  - Stage labels: Stage 1, 2, 3
 *  - Fallback: alphabetical
 */
export function sortChartData<T extends { name: string }>(data: T[]): T[] {
  if (data.length <= 1) return data;

  // 1. Credit grades: if ANY item matches a known grade, use credit-grade ordering
  const isCreditGrade = data.some(d => {
    const upper = String(d.name).toUpperCase().trim();
    return upper in CREDIT_GRADE_ORDER;
  });
  if (isCreditGrade) {
    return [...data].sort((a, b) => {
      const aO = CREDIT_GRADE_ORDER[String(a.name).toUpperCase().trim()] ?? 99;
      const bO = CREDIT_GRADE_ORDER[String(b.name).toUpperCase().trim()] ?? 99;
      return aO - bO;
    });
  }

  // 2. Stage labels: Stage 1, Stage 2, Stage 3
  const stageRe = /^stage\s*(\d+)/i;
  if (data.every(d => stageRe.test(String(d.name)))) {
    return [...data].sort((a, b) => {
      return Number(String(a.name).match(stageRe)?.[1] ?? 0) - Number(String(b.name).match(stageRe)?.[1] ?? 0);
    });
  }

  // 3. Range/band labels: "< 60%", "60-80%", "80-100%", "> 100%"
  const rangeRe = /^([<>≤≥]?\s*)(\d+)/;
  const rangeCount = data.filter(d => rangeRe.test(String(d.name))).length;
  if (rangeCount >= data.length * 0.8) {
    const prefixOrder = (p: string) => p.startsWith('<') || p.startsWith('≤') ? -1 : p.startsWith('>') || p.startsWith('≥') ? 1 : 0;
    return [...data].sort((a, b) => {
      const aMatch = String(a.name).match(rangeRe);
      const bMatch = String(b.name).match(rangeRe);
      if (!aMatch && !bMatch) return String(a.name).localeCompare(String(b.name));
      if (!aMatch) return 1;
      if (!bMatch) return -1;
      const aPO = prefixOrder((aMatch[1] || '').trim());
      const bPO = prefixOrder((bMatch[1] || '').trim());
      if (aPO !== bPO) return aPO - bPO;
      return Number(aMatch[2]) - Number(bMatch[2]);
    });
  }

  // 4. Numeric-prefixed labels: if MOST items start with a number, sort numerically.
  //    Items without a leading number ("Unknown", "Other", "N/A") go at the end.
  const nums = data.map(d => leadingNumber(String(d.name)));
  const numericCount = nums.filter(n => n !== null).length;
  if (numericCount > 0 && numericCount >= data.length * 0.5) {
    return [...data].sort((a, b) => {
      const aNum = leadingNumber(String(a.name));
      const bNum = leadingNumber(String(b.name));
      // Both numeric: sort ascending
      if (aNum !== null && bNum !== null) return aNum - bNum;
      // Non-numeric items go to the end
      if (aNum === null && bNum !== null) return 1;
      if (aNum !== null && bNum === null) return -1;
      // Both non-numeric: alphabetical
      return String(a.name).localeCompare(String(b.name));
    });
  }

  // 5. Fallback: alphabetical
  return [...data].sort((a, b) => String(a.name).localeCompare(String(b.name)));
}

// ─── DrillDown data builders ─────────────────────────────────────────────────

export function buildDrillDownData(
  products: any[],
  cohortMap: Record<string, any[]>,
  nameKey = 'product_type',
) {
  return {
    totalData: products.map(r => ({ ...r, name: r[nameKey], product_type: r[nameKey] })),
    productData: cohortMap,
    cohortData: {},
  };
}

// ─── ThreeLevelDrillDown callback factories ──────────────────────────────────

export const stageProductFetcher = async (stage: string | number) => {
  const data = await api.eclByStageProduct(Number(stage));
  return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0, name: r.product_type }));
};

export const scenarioProductFetcher = async (scenario: string | number) => {
  const data = await api.eclByScenarioProductDetail(String(scenario));
  return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0, name: r.product_type }));
};

export const cohortFetcher = async (product: string, dimension = 'risk_band') => {
  const data = await api.eclByCohort(product, dimension);
  return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0 }));
};

// ─── Shared column definitions ───────────────────────────────────────────────

export function lossAllowanceColumns(currencySymbol: string) {
  return [
    { key: 'assessed_stage', label: 'Stage', format: (v: any) => `Stage ${v}` },
    { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => Number(v).toLocaleString() },
    { key: 'total_gca', label: `GCA (${currencySymbol})`, align: 'right' as const, format: (v: any) => v },
    { key: 'total_ecl', label: `ECL (${currencySymbol})`, align: 'right' as const, format: (v: any) => v },
    { key: 'coverage_pct', label: 'Coverage %', align: 'right' as const, format: (v: any) => `${Number(v).toFixed(2)}%` },
  ];
}
