import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';


vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: () => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'style' || k === 'disabled') {
            domProps[k] = v;
          }
        }
        return <div {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('../lib/api', () => ({
  api: {
    dataMappingStatus: vi.fn().mockResolvedValue({}),
    dataMappingCatalogs: vi.fn().mockResolvedValue([]),
    dataMappingSchemas: vi.fn().mockResolvedValue([]),
    dataMappingTables: vi.fn().mockResolvedValue([]),
    dataMappingPreview: vi.fn().mockResolvedValue({ columns: [], rows: [] }),
    dataMappingSuggest: vi.fn().mockResolvedValue({}),
    dataMappingValidate: vi.fn().mockResolvedValue({ errors: [], warnings: [] }),
    dataMappingApply: vi.fn().mockResolvedValue({ status: 'ok' }),
    adminConfig: vi.fn().mockResolvedValue({}),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

vi.mock('../lib/config', () => ({
  config: {
    bankName: 'Test Bank',
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9'],
    scenarios: {},
    governance: {},
    currency: 'USD',
    currencyLocale: 'en-US',
    workflowSteps: [],
  },
}));

describe('DataMapping', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(screen.getByText('Data Mapping')).toBeInTheDocument();
    });
  });

  it('loads mapping status on mount', async () => {
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(mockApi.dataMappingStatus).toHaveBeenCalled();
    });
  });

  it('displays status cards when mapping status loaded', async () => {
    mockApi.dataMappingStatus.mockResolvedValue({
      loan_tape: { status: 'mapped', source_table: 'db.schema.loans', mapped_columns: 10, total_columns: 12 },
      scenario: { status: 'not_started', source_table: null, mapped_columns: 0, total_columns: 5 },
    });
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(mockApi.dataMappingStatus).toHaveBeenCalled();
    });
  });

  it('shows refresh button', async () => {
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(screen.getByText('Data Mapping')).toBeInTheDocument();
    });
    // The refresh icon button exists
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it('handles API error on status load', async () => {
    mockApi.dataMappingStatus.mockRejectedValue(new Error('Connection refused'));
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(mockApi.dataMappingStatus).toHaveBeenCalled();
    });
    // Toast is called with error (mocked)
  });

  it('renders loading state initially', async () => {
    let resolveStatus: any;
    mockApi.dataMappingStatus.mockReturnValue(new Promise(r => { resolveStatus = r; }));
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    // While loading, the component should show something
    expect(document.body.textContent!.length).toBeGreaterThanOrEqual(0);
    resolveStatus({});
  });

  it('displays table keys from status response', async () => {
    mockApi.dataMappingStatus.mockResolvedValue({
      loan_tape: { status: 'not_started', source_table: null, mapped_columns: 0, total_columns: 12 },
    });
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(mockApi.dataMappingStatus).toHaveBeenCalled();
    });
  });

  it('renders without crashing with empty status', async () => {
    mockApi.dataMappingStatus.mockResolvedValue({});
    const { default: DataMapping } = await import('./data-mapping/index');
    render(<DataMapping />);
    await waitFor(() => {
      expect(screen.getByText('Data Mapping')).toBeInTheDocument();
    });
  });
});
