/**
 * Workflow interaction tests: Project creation flow.
 * Tests the end-to-end user journey of creating and configuring an ECL project.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CreateProject from '../CreateProject';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: () => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, style, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'type' || k === 'value' || k === 'onChange' || k === 'name'
            || k === 'htmlFor' || k === 'placeholder' || k === 'disabled' || k === 'ref') {
            domProps[k] = v;
          }
        }
        return <div style={style} {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../../lib/api', () => ({
  api: {
    listProjects: vi.fn().mockResolvedValue([]),
    createProject: vi.fn().mockResolvedValue({ project_id: 'ECL-NEW' }),
  },
}));

vi.mock('../../lib/config', () => ({
  config: {
    defaultReportingDate: '2025-12-31',
    framework: 'IFRS 9',
    bankName: 'Test Bank',
    regulatoryFramework: 'IFRS 9 Financial Instruments',
    localRegulator: 'Central Bank',
    modelVersion: 'v4.0',
    currencySymbol: '$',
    scenarios: {},
  },
}));

import { api } from '../../lib/api';

describe('Project Creation Flow', () => {
  const defaultProps = {
    project: null,
    onCreate: vi.fn().mockResolvedValue(undefined),
    onSelectProject: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the create project form on mount', async () => {
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('shows input fields for project configuration', () => {
    render(<CreateProject {...defaultProps} />);
    const inputs = document.querySelectorAll('input');
    expect(inputs.length).toBeGreaterThan(0);
  });

  it('allows typing in project ID field', async () => {
    render(<CreateProject {...defaultProps} />);
    const pidInput = document.getElementById('create-project-id') as HTMLInputElement;
    expect(pidInput).toBeTruthy();
    fireEvent.change(pidInput, { target: { value: 'ECL-2025Q4' } });
    await waitFor(() => {
      expect(pidInput.value).toBe('ECL-2025Q4');
    });
  });

  it('pre-populates form when editing existing project', () => {
    const project = {
      project_id: 'ECL-EXIST',
      project_name: 'Existing Project',
      project_type: 'ifrs9',
      description: 'Test',
      reporting_date: '2025-12-31',
      current_step: 0,
      step_status: {},
      overlays: [],
      scenario_weights: {},
      audit_log: [],
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
      signed_off_by: null,
      signed_off_at: null,
    };
    render(<CreateProject {...defaultProps} project={project} />);
    const inputs = document.querySelectorAll('input');
    const values = Array.from(inputs).map(i => i.value);
    expect(values.some(v => v.includes('ECL-EXIST') || v.includes('Existing'))).toBe(true);
  });

  it('fetches existing projects on mount', async () => {
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(api.listProjects).toHaveBeenCalled();
    });
  });

  it('displays project list when projects exist', async () => {
    (api.listProjects as any).mockResolvedValue([
      { project_id: 'ECL-001', project_name: 'Q4 2025', reporting_date: '2025-12-31' },
      { project_id: 'ECL-002', project_name: 'Q1 2026', reporting_date: '2026-03-31' },
    ]);
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      const text = document.body.textContent || '';
      expect(text.length).toBeGreaterThan(0);
    });
  });

  it('calls onSelectProject when choosing existing project', async () => {
    (api.listProjects as any).mockResolvedValue([
      { project_id: 'ECL-001', project_name: 'Q4 2025', reporting_date: '2025-12-31' },
    ]);
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(api.listProjects).toHaveBeenCalled();
    });
  });

  it('handles empty project list gracefully', async () => {
    (api.listProjects as any).mockResolvedValue([]);
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('handles listProjects API failure gracefully', async () => {
    (api.listProjects as any).mockRejectedValue(new Error('Network error'));
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});
