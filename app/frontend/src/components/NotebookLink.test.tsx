import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import NotebookLink from './NotebookLink';

vi.mock('../lib/api', () => ({
  api: {
    jobsConfig: vi.fn().mockResolvedValue({
      job_ids: { demo_data: 101, full_pipeline: 102, satellite_ecl_sync: 103 },
      workspace_url: 'https://myworkspace.databricks.com',
      workspace_id: '12345',
    }),
  },
}));

describe('NotebookLink', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders null when notebooks array is empty', () => {
    const { container } = render(<NotebookLink notebooks={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders null when notebooks have no matching metadata', () => {
    const { container } = render(<NotebookLink notebooks={['unknown_notebook']} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders notebook links after loading job config', async () => {
    render(<NotebookLink notebooks={['01_generate_data']} />);
    await waitFor(() => {
      expect(screen.getByText('Generate Demo Data')).toBeInTheDocument();
    });
  });

  it('shows description in default (non-compact) mode', async () => {
    render(<NotebookLink notebooks={['01_generate_data']} />);
    await waitFor(() => {
      expect(screen.getByText(/Synthetic data generation/)).toBeInTheDocument();
    });
  });

  it('renders external link with correct URL', async () => {
    render(<NotebookLink notebooks={['01_generate_data']} />);
    await waitFor(() => {
      const link = screen.getByText('Generate Demo Data').closest('a');
      expect(link).toHaveAttribute('href', 'https://myworkspace.databricks.com/?o=12345#job/101');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  it('deduplicates notebooks with same jobKey', async () => {
    // 03a and 03b share the same jobKey (satellite_ecl_sync)
    render(<NotebookLink notebooks={['03a_satellite_model', '03b_run_ecl_calculation']} />);
    await waitFor(() => {
      // Only one should render due to dedup
      expect(screen.getByText('Satellite Model Pipeline')).toBeInTheDocument();
    });
  });

  it('renders multiple unique notebook links', async () => {
    render(<NotebookLink notebooks={['01_generate_data', '02_run_data_processing']} />);
    await waitFor(() => {
      expect(screen.getByText('Generate Demo Data')).toBeInTheDocument();
      expect(screen.getByText('Full Pipeline')).toBeInTheDocument();
    });
  });

  it('renders compact mode', async () => {
    render(<NotebookLink notebooks={['01_generate_data']} compact />);
    await waitFor(() => {
      expect(screen.getByText('Generate Demo Data')).toBeInTheDocument();
    });
  });

  it('shows "not provisioned" when job ID is missing', async () => {
    const { api } = await import('../lib/api');
    (api.jobsConfig as any).mockResolvedValueOnce({ job_ids: {}, workspace_url: '' });
    render(<NotebookLink notebooks={['01_generate_data']} />);
    await waitFor(() => {
      expect(screen.getByText(/not provisioned/i)).toBeInTheDocument();
    });
  });

  it('handles API failure gracefully', async () => {
    const { api } = await import('../lib/api');
    (api.jobsConfig as any).mockRejectedValueOnce(new Error('fail'));
    const { container } = render(<NotebookLink notebooks={['01_generate_data']} />);
    // Should render but without links (no job IDs loaded)
    await waitFor(() => {
      // Component still mounts, just no job IDs
      expect(container).toBeTruthy();
    });
  });

  it('builds URL without workspace_id when only host is available', async () => {
    const { api } = await import('../lib/api');
    (api.jobsConfig as any).mockResolvedValueOnce({
      job_ids: { demo_data: 101 },
      workspace_url: 'https://ws.databricks.com',
    });
    render(<NotebookLink notebooks={['01_generate_data']} />);
    await waitFor(() => {
      const link = screen.getByText('Generate Demo Data').closest('a');
      expect(link).toHaveAttribute('href', 'https://ws.databricks.com/#job/101');
    });
  });
});
