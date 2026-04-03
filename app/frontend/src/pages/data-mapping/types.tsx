import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────────────────

export interface MappingStatus {
  table_key: string;
  target_table: string;
  source_uc_table: string;
  required: boolean;
  description: string;
  has_data: boolean;
  row_count: number;
  mandatory_columns: number;
  optional_columns: number;
  mapped_columns: number;
}

export interface ColumnMapping {
  ecl_column: string;
  ecl_type: string;
  source_column: string | null;
  source_type: string | null;
  status: string;
  is_mandatory: boolean;
  type_compatible?: boolean;
  description: string;
  default?: string;
}

export interface SourceColumn {
  name: string;
  type: string;
  comment?: string;
  position?: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────

export const TYPE_BADGES: Record<string, string> = {
  TEXT: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  INT: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  NUMERIC: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  DATE: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  BOOLEAN: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
};

export function TypeBadge({ type }: { type: string }) {
  const cls = TYPE_BADGES[type?.toUpperCase()] || 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${cls}`}>{type}</span>;
}

export function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'ok':
      return <CheckCircle2 size={14} className="text-emerald-500" />;
    case 'type_mismatch':
      return <AlertTriangle size={14} className="text-amber-500" />;
    case 'unmapped':
    case 'source_missing':
      return <XCircle size={14} className="text-red-500" />;
    case 'unmapped_optional':
      return <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 dark:border-slate-600" />;
    default:
      return <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 dark:border-slate-600" />;
  }
}

// ── Stepper ────────────────────────────────────────────────────────────────

export type WizardStep = 'select-table' | 'select-source' | 'map-columns' | 'validate' | 'apply';

export const WIZARD_STEPS: { key: WizardStep; label: string; short: string }[] = [
  { key: 'select-table', label: 'Select ECL Table', short: 'Table' },
  { key: 'select-source', label: 'Choose Source', short: 'Source' },
  { key: 'map-columns', label: 'Map Columns', short: 'Map' },
  { key: 'validate', label: 'Validate', short: 'Validate' },
  { key: 'apply', label: 'Apply', short: 'Apply' },
];
