/**
 * Permission constants and utilities for the two-layer permission model.
 *
 * Layer 1 (RBAC): Global role determines what actions a user CAN do.
 * Layer 2 (Project): Project membership determines WHICH projects.
 *
 * Both layers must be satisfied. Admin overrides Layer 2.
 * Anonymous / dev mode bypasses all checks.
 */

export type ProjectRole = 'viewer' | 'editor' | 'manager' | 'owner';
export type RbacRole = 'analyst' | 'reviewer' | 'approver' | 'admin';

/** Numeric level for role hierarchy comparison. */
export const PROJECT_ROLE_LEVEL: Record<ProjectRole, number> = {
  viewer: 0,
  editor: 1,
  manager: 2,
  owner: 3,
};

/** Display labels for project roles. */
export const PROJECT_ROLE_LABELS: Record<ProjectRole, string> = {
  viewer: 'Viewer',
  editor: 'Editor',
  manager: 'Manager',
  owner: 'Owner',
};

/** All valid project roles in order. */
export const PROJECT_ROLES: ProjectRole[] = ['viewer', 'editor', 'manager', 'owner'];

/** Actions that can be checked against a project role. */
export type ProjectAction =
  | 'view'
  | 'advance_step'
  | 'save_overlays'
  | 'save_weights'
  | 'run_models'
  | 'manage_members'
  | 'reset_project'
  | 'transfer_ownership'
  | 'sign_off';

/** Minimum project role required for each action. */
const ACTION_MIN_ROLE: Record<ProjectAction, ProjectRole> = {
  view: 'viewer',
  advance_step: 'editor',
  save_overlays: 'editor',
  save_weights: 'editor',
  run_models: 'editor',
  manage_members: 'manager',
  reset_project: 'manager',
  transfer_ownership: 'owner',
  sign_off: 'owner',
};

/**
 * Check whether a project role is sufficient to perform an action.
 *
 * Returns true if the role meets or exceeds the minimum required role.
 * Unknown roles return false.
 */
export function canPerformAction(role: string | null | undefined, action: ProjectAction): boolean {
  if (!role) return false;
  const level = PROJECT_ROLE_LEVEL[role as ProjectRole];
  if (level === undefined) return false;
  const required = ACTION_MIN_ROLE[action];
  return level >= PROJECT_ROLE_LEVEL[required];
}

/**
 * Check whether a role meets or exceeds a minimum role level.
 */
export function hasMinRole(role: string | null | undefined, minRole: ProjectRole): boolean {
  if (!role) return false;
  const level = PROJECT_ROLE_LEVEL[role as ProjectRole];
  if (level === undefined) return false;
  return level >= PROJECT_ROLE_LEVEL[minRole];
}

/**
 * Check whether the RBAC role is admin.
 */
export function isAdmin(rbacRole: string | null | undefined): boolean {
  return rbacRole === 'admin';
}
