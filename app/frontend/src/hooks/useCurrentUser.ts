/**
 * Hook to fetch and cache the current user's RBAC identity.
 *
 * Calls GET /api/auth/me once and caches the result for the session.
 * Provides the user's global RBAC role and permissions list.
 */
import { useState, useEffect, useRef } from 'react';
import { api, type AuthMeResponse } from '../lib/api';

interface UseCurrentUserResult {
  user: AuthMeResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

let cachedUser: AuthMeResponse | null = null;
let fetchPromise: Promise<AuthMeResponse> | null = null;

export function useCurrentUser(): UseCurrentUserResult {
  const [user, setUser] = useState<AuthMeResponse | null>(cachedUser);
  const [isLoading, setIsLoading] = useState(!cachedUser);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const fetchUser = () => {
    if (cachedUser) {
      setUser(cachedUser);
      setIsLoading(false);
      return;
    }

    if (!fetchPromise) {
      fetchPromise = api.authMe();
    }

    setIsLoading(true);
    setError(null);

    fetchPromise
      .then((data) => {
        cachedUser = data;
        fetchPromise = null;
        if (mountedRef.current) {
          setUser(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        fetchPromise = null;
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : String(err));
          setIsLoading(false);
        }
      });
  };

  useEffect(() => {
    fetchUser();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const refetch = () => {
    cachedUser = null;
    fetchPromise = null;
    fetchUser();
  };

  return { user, isLoading, error, refetch };
}

/** Reset the cache (useful for testing). */
export function _resetUserCache(): void {
  cachedUser = null;
  fetchPromise = null;
}
