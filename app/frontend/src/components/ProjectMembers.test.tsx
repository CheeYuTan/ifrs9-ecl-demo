import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProjectMembers from './ProjectMembers';

vi.mock('../lib/api', () => ({
  api: {
    getProjectMembers: vi.fn(),
    addProjectMember: vi.fn(),
    removeProjectMember: vi.fn(),
    transferOwnership: vi.fn(),
  },
}));

vi.mock('../hooks/usePermissions', () => ({
  usePermissions: vi.fn().mockReturnValue({ canManage: true, canOwn: true }),
}));

vi.mock('../lib/permissions', () => ({
  PROJECT_ROLE_LABELS: {
    viewer: 'Viewer',
    editor: 'Editor',
    manager: 'Manager',
    owner: 'Owner',
  },
}));

vi.mock('./ConfirmDialog', () => ({
  default: ({ open, title, description, onConfirm, onCancel, confirmLabel }: any) =>
    open ? (
      <div data-testid="confirm-dialog">
        <p>{title}</p>
        <p>{description}</p>
        <button onClick={onConfirm}>{confirmLabel}</button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    ) : null,
}));

import { api } from '../lib/api';
import { usePermissions } from '../hooks/usePermissions';

const mockMembers = {
  owner: { user_id: 'owner-1', display_name: 'Alice Owner', email: 'alice@test.com' },
  members: [
    { user_id: 'user-1', display_name: 'Bob Editor', email: 'bob@test.com', role: 'editor' as const },
    { user_id: 'user-2', display_name: 'Carol Viewer', email: 'carol@test.com', role: 'viewer' as const },
  ],
};

describe('ProjectMembers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getProjectMembers as any).mockResolvedValue(mockMembers);
    (api.addProjectMember as any).mockResolvedValue({});
    (api.removeProjectMember as any).mockResolvedValue({});
    (api.transferOwnership as any).mockResolvedValue({});
    (usePermissions as any).mockReturnValue({ canManage: true, canOwn: true });
  });

  it('renders loading state initially', () => {
    (api.getProjectMembers as any).mockReturnValue(new Promise(() => {}));
    render(<ProjectMembers projectId="proj-1" />);
    expect(screen.getByText(/Loading members/)).toBeInTheDocument();
  });

  it('renders owner and members after loading', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Alice Owner')).toBeInTheDocument();
    });
    expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    expect(screen.getByText('Carol Viewer')).toBeInTheDocument();
  });

  it('displays owner badge', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Owner')).toBeInTheDocument();
    });
  });

  it('displays member roles', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getAllByText('Editor').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Viewer').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays member count', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('shows add member form when canManage', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('User ID or email')).toBeInTheDocument();
    });
    expect(screen.getByText('Add')).toBeInTheDocument();
  });

  it('hides add member form when not canManage', async () => {
    (usePermissions as any).mockReturnValue({ canManage: false, canOwn: false });
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Alice Owner')).toBeInTheDocument();
    });
    expect(screen.queryByPlaceholderText('User ID or email')).not.toBeInTheDocument();
  });

  it('adds a new member', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('User ID or email')).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText('User ID or email'), 'new-user');
    await user.click(screen.getByText('Add'));

    await waitFor(() => {
      expect(api.addProjectMember).toHaveBeenCalledWith('proj-1', 'new-user', 'viewer');
    });
  });

  it('disables add button when input is empty', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Add')).toBeInTheDocument();
    });
    expect(screen.getByText('Add')).toBeDisabled();
  });

  it('shows error on fetch failure', async () => {
    (api.getProjectMembers as any).mockRejectedValue(new Error('Network error'));
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows error on add failure', async () => {
    (api.addProjectMember as any).mockRejectedValue(new Error('Permission denied'));
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('User ID or email')).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText('User ID or email'), 'bad-user');
    await user.click(screen.getByText('Add'));

    await waitFor(() => {
      expect(screen.getByText('Permission denied')).toBeInTheDocument();
    });
  });

  it('shows confirm dialog when removing member', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByTitle('Remove member');
    await user.click(removeButtons[0]);

    await waitFor(() => {
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
      expect(screen.getByText('Remove Member')).toBeInTheDocument();
    });
  });

  it('confirms member removal', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByTitle('Remove member');
    await user.click(removeButtons[0]);

    await waitFor(() => {
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Remove'));

    await waitFor(() => {
      expect(api.removeProjectMember).toHaveBeenCalledWith('proj-1', 'user-1');
    });
  });

  it('shows transfer ownership dialog', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    });

    const transferButtons = screen.getAllByTitle('Transfer ownership');
    await user.click(transferButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Transfer Ownership')).toBeInTheDocument();
    });
  });

  it('hides transfer button when not canOwn', async () => {
    (usePermissions as any).mockReturnValue({ canManage: true, canOwn: false });
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    });
    expect(screen.queryByTitle('Transfer ownership')).not.toBeInTheDocument();
  });

  it('shows empty state when no members', async () => {
    (api.getProjectMembers as any).mockResolvedValue({ owner: null, members: [] });
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('No members yet')).toBeInTheDocument();
    });
  });

  it('displays member emails', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('alice@test.com')).toBeInTheDocument();
      expect(screen.getByText('bob@test.com')).toBeInTheDocument();
    });
  });

  it('displays user_id as fallback when no display_name', async () => {
    (api.getProjectMembers as any).mockResolvedValue({
      owner: null,
      members: [{ user_id: 'user-x', display_name: '', email: '', role: 'viewer' }],
    });
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('user-x')).toBeInTheDocument();
    });
  });

  it('role select defaults to viewer', async () => {
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      const select = screen.getByRole('combobox');
      expect(select).toHaveValue('viewer');
    });
  });

  it('cancels confirm dialog', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByText('Bob Editor')).toBeInTheDocument();
    });

    const removeButtons = screen.getAllByTitle('Remove member');
    await user.click(removeButtons[0]);
    await waitFor(() => {
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument();
    });
  });

  it('clears input after successful add', async () => {
    const user = userEvent.setup();
    render(<ProjectMembers projectId="proj-1" />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('User ID or email')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('User ID or email');
    await user.type(input, 'new-user');
    await user.click(screen.getByText('Add'));

    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });
});
