import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Stepper from './Stepper';
import type { Project } from '../lib/api';

const makeProject = (overrides: Partial<Project> = {}): Project => ({
  project_id: 'p1',
  project_name: 'Test',
  project_type: 'IFRS9',
  description: '',
  reporting_date: '2025-12-31',
  current_step: 3,
  step_status: {
    create_project: 'completed',
    data_processing: 'completed',
    data_control: 'completed',
  },
  overlays: [],
  scenario_weights: {},
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: null,
  signed_off_at: null,
  ...overrides,
});

describe('Stepper', () => {
  it('renders all step labels', () => {
    render(<Stepper project={null} activeStep={0} onStepClick={() => {}} />);
    expect(screen.getByText('Create')).toBeInTheDocument();
    expect(screen.getByText('Data Proc')).toBeInTheDocument();
    expect(screen.getByText('Data QC')).toBeInTheDocument();
    expect(screen.getByText('Satellite Model')).toBeInTheDocument();
    expect(screen.getByText('Monte Carlo')).toBeInTheDocument();
    expect(screen.getByText('Stress Test')).toBeInTheDocument();
    expect(screen.getByText('Overlays')).toBeInTheDocument();
    expect(screen.getByText('Sign Off')).toBeInTheDocument();
  });

  it('calls onStepClick for reachable steps', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const project = makeProject();
    render(<Stepper project={project} activeStep={0} onStepClick={onClick} />);

    await user.click(screen.getByText('Data QC'));
    expect(onClick).toHaveBeenCalledWith(2);
  });

  it('does not call onStepClick for unreachable steps', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const project = makeProject({ current_step: 1 });
    render(<Stepper project={project} activeStep={0} onStepClick={onClick} />);

    const signOffButton = screen.getByText('Sign Off').closest('button');
    expect(signOffButton).toBeDisabled();
    await user.click(signOffButton!);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('shows step labels for non-completed steps', () => {
    render(<Stepper project={makeProject({ current_step: 0, step_status: {} })} activeStep={0} onStepClick={() => {}} />);
    expect(screen.getByText('Create')).toBeInTheDocument();
    expect(screen.getByText('Data Proc')).toBeInTheDocument();
  });

  it('disables steps beyond current_step', () => {
    const project = makeProject({ current_step: 2 });
    render(<Stepper project={project} activeStep={0} onStepClick={() => {}} />);
    const signOffBtn = screen.getByText('Sign Off').closest('button');
    expect(signOffBtn).toBeDisabled();
  });
});
