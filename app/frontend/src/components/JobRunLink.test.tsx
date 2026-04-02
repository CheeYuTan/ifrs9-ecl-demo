import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import JobRunLink from './JobRunLink';

const makeRun = (overrides: Partial<any> = {}) => ({
  run_id: 123,
  job_id: 456,
  lifecycle_state: 'TERMINATED',
  result_state: 'SUCCESS',
  run_url: 'https://workspace.databricks.com/run/123',
  ...overrides,
});

describe('JobRunLink', () => {
  it('returns null when run is null', () => {
    const { container } = render(<JobRunLink run={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders label and link in default mode', () => {
    render(<JobRunLink run={makeRun()} />);
    expect(screen.getByText('Databricks Job Run')).toBeInTheDocument();
    expect(screen.getByText('Open in Databricks')).toBeInTheDocument();
  });

  it('renders custom label', () => {
    render(<JobRunLink run={makeRun()} label="Custom Job" />);
    expect(screen.getByText('Custom Job')).toBeInTheDocument();
  });

  it('shows SUCCESS result state', () => {
    render(<JobRunLink run={makeRun({ result_state: 'SUCCESS' })} />);
    expect(screen.getByText('SUCCESS')).toBeInTheDocument();
  });

  it('shows Running... for RUNNING state', () => {
    render(<JobRunLink run={makeRun({ lifecycle_state: 'RUNNING', result_state: null })} />);
    expect(screen.getByText('Running...')).toBeInTheDocument();
  });

  it('shows FAILED result state', () => {
    render(<JobRunLink run={makeRun({ result_state: 'FAILED' })} />);
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });

  it('renders compact mode with link', () => {
    render(<JobRunLink run={makeRun()} compact />);
    const link = screen.getByText('Databricks Job Run');
    expect(link.closest('a')).toHaveAttribute('href', 'https://workspace.databricks.com/run/123');
  });

  it('shows duration when available', () => {
    render(<JobRunLink run={makeRun({ run_duration_ms: 45000 })} />);
    expect(screen.getByText('45s')).toBeInTheDocument();
  });

  it('renders task list when tasks present', () => {
    const run = makeRun({
      tasks: [
        { task_key: 'load_data', lifecycle_state: 'TERMINATED', result_state: 'SUCCESS', run_url: '#', execution_duration_ms: 5000 },
        { task_key: 'compute_ecl', lifecycle_state: 'TERMINATED', result_state: 'SUCCESS', run_url: '#', execution_duration_ms: 30000 },
      ],
    });
    render(<JobRunLink run={run} />);
    expect(screen.getByText('load_data')).toBeInTheDocument();
    expect(screen.getByText('compute_ecl')).toBeInTheDocument();
  });

  it('link opens in new tab', () => {
    render(<JobRunLink run={makeRun()} />);
    const link = screen.getByText('Open in Databricks').closest('a');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
