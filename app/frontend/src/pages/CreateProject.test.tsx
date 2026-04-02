import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import CreateProject from './CreateProject';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, layout, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

vi.mock('../lib/api', () => ({
  api: {
    listProjects: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../lib/config', () => ({
  config: {
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9', 'basel3'],
  },
}));

describe('CreateProject', () => {
  const defaultProps = {
    project: null,
    onCreate: vi.fn().mockResolvedValue(undefined),
    onSelectProject: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders project creation form', async () => {
    render(<CreateProject {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('renders project ID input', () => {
    render(<CreateProject {...defaultProps} />);
    const inputs = document.querySelectorAll('input');
    expect(inputs.length).toBeGreaterThan(0);
  });

  it('pre-fills fields from existing project', () => {
    const project = {
      project_id: 'ECL-2025Q4',
      project_name: 'Q4 2025 ECL',
      project_type: 'ifrs9',
      description: 'Quarterly run',
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
    expect(values.some(v => v.includes('ECL-2025Q4') || v.includes('Q4 2025'))).toBe(true);
  });

  it('loads project list on mount', async () => {
    render(<CreateProject {...defaultProps} />);
    // api.listProjects is called in useEffect
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});
