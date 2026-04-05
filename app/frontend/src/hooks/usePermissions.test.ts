import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { usePermissions, _resetPermissionCache } from './usePermissions';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
  api: {
    getMyProjectRole: vi.fn(),
  },
}));

const mockApi = api as unknown as {
  getMyProjectRole: ReturnType<typeof vi.fn>;
};

describe('usePermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _resetPermissionCache();
  });

  it('returns null data when projectId is null', () => {
    const { result } = renderHook(() => usePermissions(null));
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.canEdit).toBe(false);
  });

  it('starts loading when projectId provided', () => {
    mockApi.getMyProjectRole.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => usePermissions('P1'));
    expect(result.current.isLoading).toBe(true);
  });

  it('fetches and returns editor role', async () => {
    mockApi.getMyProjectRole.mockResolvedValue({
      user_id: 'usr-001',
      project_role: 'editor',
      rbac_role: 'analyst',
    });

    const { result } = renderHook(() => usePermissions('P1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.projectRole).toBe('editor');
    expect(result.current.canEdit).toBe(true);
    expect(result.current.canManage).toBe(false);
    expect(result.current.canOwn).toBe(false);
    expect(result.current.isAdminUser).toBe(false);
  });

  it('owner has all permissions', async () => {
    mockApi.getMyProjectRole.mockResolvedValue({
      user_id: 'usr-004',
      project_role: 'owner',
      rbac_role: 'admin',
    });

    const { result } = renderHook(() => usePermissions('P1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.canEdit).toBe(true);
    expect(result.current.canManage).toBe(true);
    expect(result.current.canOwn).toBe(true);
    expect(result.current.isAdminUser).toBe(true);
  });

  it('viewer has read-only permissions', async () => {
    mockApi.getMyProjectRole.mockResolvedValue({
      user_id: 'usr-001',
      project_role: 'viewer',
      rbac_role: 'analyst',
    });

    const { result } = renderHook(() => usePermissions('P1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.canEdit).toBe(false);
    expect(result.current.canManage).toBe(false);
    expect(result.current.canOwn).toBe(false);
    expect(result.current.can('view')).toBe(true);
    expect(result.current.can('advance_step')).toBe(false);
  });

  it('can() checks specific actions', async () => {
    mockApi.getMyProjectRole.mockResolvedValue({
      user_id: 'usr-001',
      project_role: 'manager',
      rbac_role: 'reviewer',
    });

    const { result } = renderHook(() => usePermissions('P1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.can('view')).toBe(true);
    expect(result.current.can('advance_step')).toBe(true);
    expect(result.current.can('manage_members')).toBe(true);
    expect(result.current.can('sign_off')).toBe(false);
  });

  it('handles fetch error', async () => {
    mockApi.getMyProjectRole.mockRejectedValue(new Error('403'));

    const { result } = renderHook(() => usePermissions('P1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.error).toBe('403');
    expect(result.current.data).toBeNull();
    expect(result.current.canEdit).toBe(false);
  });

  it('caches results by project ID', async () => {
    mockApi.getMyProjectRole.mockResolvedValue({
      user_id: 'usr-001',
      project_role: 'editor',
      rbac_role: 'analyst',
    });

    const { result: r1 } = renderHook(() => usePermissions('P1'));
    await waitFor(() => expect(r1.current.isLoading).toBe(false));

    const { result: r2 } = renderHook(() => usePermissions('P1'));
    // Should use cache — no additional API call
    expect(r2.current.projectRole).toBe('editor');
    expect(mockApi.getMyProjectRole).toHaveBeenCalledTimes(1);
  });

  it('fetches separately for different project IDs', async () => {
    mockApi.getMyProjectRole
      .mockResolvedValueOnce({ user_id: 'u', project_role: 'editor', rbac_role: 'analyst' })
      .mockResolvedValueOnce({ user_id: 'u', project_role: 'viewer', rbac_role: 'analyst' });

    const { result: r1 } = renderHook(() => usePermissions('P1'));
    await waitFor(() => expect(r1.current.isLoading).toBe(false));

    const { result: r2 } = renderHook(() => usePermissions('P2'));
    await waitFor(() => expect(r2.current.isLoading).toBe(false));

    expect(r1.current.projectRole).toBe('editor');
    expect(r2.current.projectRole).toBe('viewer');
    expect(mockApi.getMyProjectRole).toHaveBeenCalledTimes(2);
  });
});
