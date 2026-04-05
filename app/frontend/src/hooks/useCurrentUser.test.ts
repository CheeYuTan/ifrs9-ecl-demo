import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useCurrentUser, _resetUserCache } from './useCurrentUser';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
  api: {
    authMe: vi.fn(),
  },
}));

const mockApi = api as unknown as {
  authMe: ReturnType<typeof vi.fn>;
};

describe('useCurrentUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _resetUserCache();
  });

  it('starts in loading state', () => {
    mockApi.authMe.mockReturnValue(new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useCurrentUser());
    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it('fetches and returns user', async () => {
    const mockUser = {
      user_id: 'usr-001',
      email: 'ana@bank.com',
      display_name: 'Ana Reyes',
      role: 'analyst',
      permissions: ['view_portfolio'],
    };
    mockApi.authMe.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useCurrentUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBeNull();
  });

  it('handles error', async () => {
    mockApi.authMe.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCurrentUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.error).toBe('Network error');
  });

  it('caches result across multiple renders', async () => {
    const mockUser = {
      user_id: 'usr-001',
      email: 'ana@bank.com',
      display_name: 'Ana',
      role: 'analyst',
      permissions: [],
    };
    mockApi.authMe.mockResolvedValue(mockUser);

    const { result: r1 } = renderHook(() => useCurrentUser());
    await waitFor(() => expect(r1.current.isLoading).toBe(false));

    // Second render should use cache
    const { result: r2 } = renderHook(() => useCurrentUser());
    expect(r2.current.user).toEqual(mockUser);
    expect(mockApi.authMe).toHaveBeenCalledTimes(1);
  });
});
