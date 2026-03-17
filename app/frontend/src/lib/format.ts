import { config } from './config';

export function fmtCurrency(v: number | null | undefined, decimals = 0): string {
  if (v == null) return '—';
  return new Intl.NumberFormat(config.currencyLocale, { style: 'currency', currency: config.currency, minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(v);
}

export function fmtNumber(v: number | null | undefined, decimals = 0): string {
  if (v == null) return '—';
  return new Intl.NumberFormat(config.currencyLocale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(v);
}

export function fmtPct(v: number | null | undefined, decimals = 2): string {
  if (v == null) return '—';
  return `${v.toFixed(decimals)}%`;
}

export function fmtDate(v: string | null | undefined): string {
  if (!v) return '—';
  return new Date(v).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function fmtDateTime(v: string | null | undefined): string {
  if (!v) return '—';
  return new Date(v).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
