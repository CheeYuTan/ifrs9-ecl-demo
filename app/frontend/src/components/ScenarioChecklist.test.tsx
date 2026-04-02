import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ScenarioChecklist, { type ScenarioProgress } from './ScenarioChecklist';

const makeScenario = (overrides: Partial<ScenarioProgress> = {}): ScenarioProgress => ({
  key: 'base',
  label: 'Base',
  color: '#10B981',
  weightPct: 50,
  status: 'pending',
  ...overrides,
});

describe('ScenarioChecklist', () => {
  it('renders scenario labels', () => {
    const scenarios = [
      makeScenario({ key: 'base', label: 'Base Case', weightPct: 50 }),
      makeScenario({ key: 'adverse', label: 'Adverse', weightPct: 30 }),
    ];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('Base Case')).toBeInTheDocument();
    expect(screen.getByText('Adverse')).toBeInTheDocument();
  });

  it('renders weight percentages', () => {
    const scenarios = [makeScenario({ weightPct: 60 })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('(60%)')).toBeInTheDocument();
  });

  it('shows Pending text for pending scenarios', () => {
    const scenarios = [makeScenario({ status: 'pending' })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('shows Computing… for running scenarios', () => {
    const scenarios = [makeScenario({ status: 'running' })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('Computing…')).toBeInTheDocument();
  });

  it('shows ECL amount for done scenarios', () => {
    const scenarios = [makeScenario({ status: 'done', ecl: 1500000 })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    // fmtCurrency should format this as a currency value
    const text = screen.getByText((content) => content.includes('1,500,000'));
    expect(text).toBeInTheDocument();
  });

  it('shows duration for completed scenarios', () => {
    const scenarios = [makeScenario({ status: 'done', ecl: 100, durationMs: 2500 })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('2.5s')).toBeInTheDocument();
  });

  it('shows dash for duration when not available', () => {
    const scenarios = [makeScenario({ status: 'pending' })];
    render(<ScenarioChecklist scenarios={scenarios} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('renders color dot with correct style', () => {
    const scenarios = [makeScenario({ color: '#FF0000' })];
    const { container } = render(<ScenarioChecklist scenarios={scenarios} />);
    const dot = container.querySelector('.rounded-full');
    expect(dot).toBeTruthy();
    expect(dot?.getAttribute('style')).toContain('rgb(255, 0, 0)');
  });
});
