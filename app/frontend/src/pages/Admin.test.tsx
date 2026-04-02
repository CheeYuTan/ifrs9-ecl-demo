import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Admin from './Admin';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, layout, whileHover, whileTap, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
    button: ({ children, ...props }: any) => {
      const { whileHover, whileTap, ...rest } = props;
      return <button {...rest}>{children}</button>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('./admin/types', () => ({
  fetchJson: vi.fn().mockResolvedValue({
    data_mapping: { tables: {} },
    model: {},
    jobs: {},
    app: { bank_name: 'Test Bank' },
    theme: {},
    system: {},
  }),
}));

vi.mock('./admin/AdminDataMappings', () => ({ default: () => <div data-testid="admin-data">Data Mappings</div> }));
vi.mock('./admin/AdminModelConfig', () => ({ default: () => <div data-testid="admin-model">Model Config</div> }));
vi.mock('./admin/AdminJobsConfig', () => ({ default: () => <div data-testid="admin-jobs">Jobs Config</div> }));
vi.mock('./admin/AdminAppSettings', () => ({ default: () => <div data-testid="admin-app">App Settings</div> }));
vi.mock('./admin/AdminThemeConfig', () => ({ default: () => <div data-testid="admin-theme">Theme Config</div> }));
vi.mock('./admin/AdminSystemConfig', () => ({ default: () => <div data-testid="admin-system">System Config</div> }));

describe('Admin', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders tab labels after loading', async () => {
    render(<Admin />);
    await waitFor(() => {
      expect(screen.getByText('Data Mapping')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText('Model Config')).toBeInTheDocument();
    expect(screen.getByText('Jobs & Pipelines')).toBeInTheDocument();
    expect(screen.getByText('App Settings')).toBeInTheDocument();
    expect(screen.getByText('Theme')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('loads config on mount', async () => {
    render(<Admin />);
    await waitFor(() => {
      expect(screen.getByTestId('admin-data')).toBeInTheDocument();
    });
  });

  it('switches tabs when clicked', async () => {
    const user = userEvent.setup();
    render(<Admin />);
    await waitFor(() => {
      expect(screen.getByTestId('admin-data')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Model Config'));
    await waitFor(() => {
      expect(screen.getByTestId('admin-model')).toBeInTheDocument();
    });
  });
});
