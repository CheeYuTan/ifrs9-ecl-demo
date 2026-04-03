import { describe, it, expect } from 'vitest';
import { fmtCurrency, fmtNumber, fmtPct, fmtDate, fmtDateTime } from './format';

describe('fmtCurrency', () => {
  it('formats a positive number as USD', () => {
    expect(fmtCurrency(1234567)).toBe('$1,234,567');
  });

  it('formats with decimal places', () => {
    expect(fmtCurrency(1234.5, 2)).toBe('$1,234.50');
  });

  it('returns em-dash for null', () => {
    expect(fmtCurrency(null)).toBe('—');
  });

  it('returns em-dash for undefined', () => {
    expect(fmtCurrency(undefined)).toBe('—');
  });

  it('formats zero', () => {
    expect(fmtCurrency(0)).toBe('$0');
  });

  it('formats negative numbers', () => {
    const result = fmtCurrency(-500);
    expect(result).toContain('500');
  });
});

describe('fmtNumber', () => {
  it('formats a number with thousand separators', () => {
    expect(fmtNumber(1234567)).toBe('1,234,567');
  });

  it('formats with decimal places', () => {
    expect(fmtNumber(1234.5, 2)).toBe('1,234.50');
  });

  it('returns em-dash for null', () => {
    expect(fmtNumber(null)).toBe('—');
  });

  it('returns em-dash for undefined', () => {
    expect(fmtNumber(undefined)).toBe('—');
  });
});

describe('fmtPct', () => {
  it('formats a percentage with default 2 decimals', () => {
    expect(fmtPct(12.345)).toBe('12.35%');
  });

  it('formats with custom decimal places', () => {
    expect(fmtPct(12.3, 1)).toBe('12.3%');
  });

  it('returns em-dash for null', () => {
    expect(fmtPct(null)).toBe('—');
  });

  it('returns em-dash for undefined', () => {
    expect(fmtPct(undefined)).toBe('—');
  });

  it('formats zero', () => {
    expect(fmtPct(0)).toBe('0.00%');
  });
});

describe('fmtDate', () => {
  it('formats an ISO date string', () => {
    const result = fmtDate('2025-12-31');
    expect(result).toContain('Dec');
    expect(result).toContain('2025');
    expect(result).toContain('31');
  });

  it('returns em-dash for null', () => {
    expect(fmtDate(null)).toBe('—');
  });

  it('returns em-dash for undefined', () => {
    expect(fmtDate(undefined)).toBe('—');
  });

  it('returns em-dash for empty string', () => {
    expect(fmtDate('')).toBe('—');
  });
});

describe('fmtDateTime', () => {
  it('formats a datetime string with time component', () => {
    const result = fmtDateTime('2025-12-31T14:30:00Z');
    expect(result).toContain('Dec');
    expect(result).toContain('2025');
    expect(result).toContain('31');
  });

  it('returns em-dash for null', () => {
    expect(fmtDateTime(null)).toBe('—');
  });

  it('returns em-dash for undefined', () => {
    expect(fmtDateTime(undefined)).toBe('—');
  });

  it('returns em-dash for empty string', () => {
    expect(fmtDateTime('')).toBe('—');
  });
});
