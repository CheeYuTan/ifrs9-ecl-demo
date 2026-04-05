/**
 * Hook to fetch and cache the current user's effective project role.
 *
 * Calls GET /api/auth/projects/{id}/my-role and caches by project ID.
 * Provides convenience booleans for common permission checks.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { api, type MyProjectRoleResponse } from '../lib/api';
import { canPerformAction, hasMinRole, isAdmin } from '../lib/permissions';
import type { ProjectRole, ProjectAction } from '../lib/permissions';

export interface UsePermissionsResult {
  /** The raw role response from the API. */
  data: MyProjectRoleResponse | null;
  /** Effective project role (viewer/editor/manager/owner). */
  projectRole: ProjectRole | null;
  /** Global RBAC role. */
  rbacRole: string | null;
  /** True while the role is being fetched. */
  isLoading: boolean;
  /** Error message if the fetch failed. */
  error: string | null;
  /** User has at least editor project role. */
  canEdit: boolean;
  /** User has at least manager project role. */
  canManage: boolean;
  /** User has owner project role. */
  canOwn: boolean;
  /** User has admin RBAC role. */
  isAdminUser: boolean;
  /** Check a specific action against the effective project role. */
  can: (action: ProjectAction) => boolean;
  /** Re-fetch the role (cache-bust). */
  refetch: () => void;
}

const cache = new Map<string, MyProjectRoleResponse>();

export function usePermissions(projectId: string | null | undefined): UsePermissionsResult {
  const [data, setData] = useState<MyProjectRoleResponse | null>(
    projectId ? cache.get(projectId) ?? null : null,
  );
  const [isLoading, setIsLoading] = useState(!data && !!projectId);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const fetchRole = useCallback((pid: string, bustCache = false) => {
    if (!bustCache && cache.has(pid)) {
      const cached = cache.get(pid)!;
      setData(cached);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    api.getMyProjectRole(pid)
      .then((resp) => {
        cache.set(pid, resp);
        if (mountedRef.current) {
          setData(resp);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : String(err));
          setIsLoading(false);
          setData(null);
        }
      });
  }, []);

  useEffect(() => {
    if (!projectId) {
      setData(null);
      setIsLoading(false);
      setError(null);
      return;
    }
    fetchRole(projectId);
  }, [projectId, fetchRole]);

  const projectRole = (data?.project_role as ProjectRole) ?? null;
  const rbacRole = data?.rbac_role ?? null;

  const refetch = useCallback(() => {
    if (projectId) {
      cache.delete(projectId);
      fetchRole(projectId, true);
    }
  }, [projectId, fetchRole]);

  return {
    data,
    projectRole,
    rbacRole,
    isLoading,
    error,
    canEdit: hasMinRole(projectRole, 'editor'),
    canManage: hasMinRole(projectRole, 'manager'),
    canOwn: hasMinRole(projectRole, 'owner'),
    isAdminUser: isAdmin(rbacRole),
    can: (action: ProjectAction) => canPerformAction(projectRole, action),
    refetch,
  };
}

/** Clear the permission cache (useful for testing). */
export function _resetPermissionCache(): void {
  cache.clear();
}
