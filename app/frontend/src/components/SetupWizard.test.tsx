import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SetupWizard from './SetupWizard';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_target, _prop) => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, style, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'ref' || k === 'key' || k === 'disabled' || k === 'href' || k === 'target'
            || k === 'type' || k === 'value' || k === 'onChange' || k === 'onSubmit' || k === 'name'
            || k === 'htmlFor' || k === 'placeholder') {
            domProps[k] = v;
          }
        }
        return <div style={style} {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../lib/api', () => ({
  api: {
    setupStatus: vi.fn().mockResolvedValue({
      status: 'not_started',
      steps: {
        data_connection: { complete: false },
        organization: { complete: false },
        first_project: { complete: false },
      },
    }),
    adminConfig: vi.fn().mockResolvedValue({}),
    testConnection: vi.fn().mockResolvedValue({ connected: true }),
    setupSeed: vi.fn().mockResolvedValue({}),
    setupComplete: vi.fn().mockResolvedValue({}),
    listProjects: vi.fn().mockResolvedValue([]),
    createProject: vi.fn().mockResolvedValue({ id: 1 }),
    adminUpdateConfig: vi.fn().mockResolvedValue({}),
    dataMappingCatalogs: vi.fn().mockResolvedValue([]),
  },
  SetupStatus: {},
}));

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

describe('SetupWizard', () => {
  const onComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<SetupWizard onComplete={onComplete} />);
    // Should render initial wizard view
    expect(document.body).toBeTruthy();
  });

  it('shows loading state initially', () => {
    render(<SetupWizard onComplete={onComplete} />);
    expect(screen.getByText('Checking setup status...')).toBeInTheDocument();
  });

  it('renders step labels after loading', async () => {
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(screen.getByText('Welcome')).toBeInTheDocument();
    });
    expect(screen.getByText('Data Connection')).toBeInTheDocument();
    expect(screen.getByText('Organization')).toBeInTheDocument();
    expect(screen.getByText('First Project')).toBeInTheDocument();
  });

  it('shows wizard content after loading completes', async () => {
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(screen.queryByText('Checking setup status...')).toBeNull();
    });
  });

  it('renders welcome step with get started button', async () => {
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Get Started/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders step indicator with 4 steps', async () => {
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(screen.getByText('Welcome')).toBeInTheDocument();
      expect(screen.getByText('Data Connection')).toBeInTheDocument();
      expect(screen.getByText('Organization')).toBeInTheDocument();
      expect(screen.getByText('First Project')).toBeInTheDocument();
    });
  });

  it('has a next/continue button on welcome step', async () => {
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Next|Continue|Get Started|Begin/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('calls setupStatus on mount', async () => {
    const { api: mockApi } = await import('../lib/api') as any;
    render(<SetupWizard onComplete={onComplete} />);
    await waitFor(() => {
      expect(mockApi.setupStatus).toHaveBeenCalled();
    });
  });
});
