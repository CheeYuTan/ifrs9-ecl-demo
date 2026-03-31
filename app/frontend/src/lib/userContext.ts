/**
 * User context for the current session.
 * Returns the authenticated user's display name when RBAC is enabled,
 * otherwise falls back to a configurable default.
 */

import { config } from './config';

export function getCurrentUser(): string {
  // When Databricks OAuth / RBAC is wired in, this will read from the auth session.
  // For now, return the configured bank user or a sensible default.
  return (config as any).currentUser ?? 'ECL System User';
}
