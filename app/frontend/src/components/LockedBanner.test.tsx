import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LockedBanner from './LockedBanner';

describe('LockedBanner', () => {
  it('renders the locked message', () => {
    render(<LockedBanner />);
    expect(screen.getByText('Step Locked')).toBeInTheDocument();
    expect(screen.getByText('Complete the previous step to unlock this section.')).toBeInTheDocument();
  });

  it('shows previous step name when requiredStep is provided', () => {
    render(<LockedBanner requiredStep={2} />);
    expect(screen.getByText(/Data Processing/)).toBeInTheDocument();
  });

  it('does not show previous step hint when requiredStep is 0', () => {
    render(<LockedBanner requiredStep={0} />);
    expect(screen.queryByText(/Go to/)).toBeNull();
  });

  it('does not show previous step hint when requiredStep is not provided', () => {
    render(<LockedBanner />);
    expect(screen.queryByText(/Go to/)).toBeNull();
  });

  it('shows correct step name for different steps', () => {
    render(<LockedBanner requiredStep={5} />);
    expect(screen.getByText(/Monte Carlo/)).toBeInTheDocument();
  });
});
