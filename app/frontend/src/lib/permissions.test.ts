import { describe, it, expect } from 'vitest';
import {
  canPerformAction,
  hasMinRole,
  isAdmin,
  PROJECT_ROLE_LEVEL,
  PROJECT_ROLES,
  PROJECT_ROLE_LABELS,
  type ProjectAction,
  type ProjectRole,
} from './permissions';

describe('permissions', () => {
  describe('PROJECT_ROLE_LEVEL', () => {
    it('defines correct hierarchy', () => {
      expect(PROJECT_ROLE_LEVEL.viewer).toBeLessThan(PROJECT_ROLE_LEVEL.editor);
      expect(PROJECT_ROLE_LEVEL.editor).toBeLessThan(PROJECT_ROLE_LEVEL.manager);
      expect(PROJECT_ROLE_LEVEL.manager).toBeLessThan(PROJECT_ROLE_LEVEL.owner);
    });

    it('has all four roles', () => {
      expect(Object.keys(PROJECT_ROLE_LEVEL)).toHaveLength(4);
    });
  });

  describe('PROJECT_ROLES', () => {
    it('lists roles in ascending order', () => {
      expect(PROJECT_ROLES).toEqual(['viewer', 'editor', 'manager', 'owner']);
    });
  });

  describe('PROJECT_ROLE_LABELS', () => {
    it('has a label for each role', () => {
      for (const role of PROJECT_ROLES) {
        expect(PROJECT_ROLE_LABELS[role]).toBeTruthy();
      }
    });
  });

  describe('canPerformAction', () => {
    it('viewer can view', () => {
      expect(canPerformAction('viewer', 'view')).toBe(true);
    });

    it('viewer cannot advance step', () => {
      expect(canPerformAction('viewer', 'advance_step')).toBe(false);
    });

    it('editor can advance step', () => {
      expect(canPerformAction('editor', 'advance_step')).toBe(true);
    });

    it('editor can save overlays', () => {
      expect(canPerformAction('editor', 'save_overlays')).toBe(true);
    });

    it('editor cannot manage members', () => {
      expect(canPerformAction('editor', 'manage_members')).toBe(false);
    });

    it('manager can manage members', () => {
      expect(canPerformAction('manager', 'manage_members')).toBe(true);
    });

    it('manager cannot sign off', () => {
      expect(canPerformAction('manager', 'sign_off')).toBe(false);
    });

    it('owner can sign off', () => {
      expect(canPerformAction('owner', 'sign_off')).toBe(true);
    });

    it('owner can do everything', () => {
      const actions: ProjectAction[] = [
        'view', 'advance_step', 'save_overlays', 'save_weights',
        'run_models', 'manage_members', 'reset_project',
        'transfer_ownership', 'sign_off',
      ];
      for (const action of actions) {
        expect(canPerformAction('owner', action)).toBe(true);
      }
    });

    it('null role returns false', () => {
      expect(canPerformAction(null, 'view')).toBe(false);
    });

    it('undefined role returns false', () => {
      expect(canPerformAction(undefined, 'view')).toBe(false);
    });

    it('unknown role returns false', () => {
      expect(canPerformAction('unknown', 'view')).toBe(false);
    });

    it('higher roles inherit lower role permissions', () => {
      expect(canPerformAction('manager', 'advance_step')).toBe(true);
      expect(canPerformAction('owner', 'manage_members')).toBe(true);
    });
  });

  describe('hasMinRole', () => {
    it('viewer meets viewer', () => {
      expect(hasMinRole('viewer', 'viewer')).toBe(true);
    });

    it('viewer does not meet editor', () => {
      expect(hasMinRole('viewer', 'editor')).toBe(false);
    });

    it('owner meets all roles', () => {
      const roles: ProjectRole[] = ['viewer', 'editor', 'manager', 'owner'];
      for (const r of roles) {
        expect(hasMinRole('owner', r)).toBe(true);
      }
    });

    it('null returns false', () => {
      expect(hasMinRole(null, 'viewer')).toBe(false);
    });
  });

  describe('isAdmin', () => {
    it('admin returns true', () => {
      expect(isAdmin('admin')).toBe(true);
    });

    it('analyst returns false', () => {
      expect(isAdmin('analyst')).toBe(false);
    });

    it('null returns false', () => {
      expect(isAdmin(null)).toBe(false);
    });

    it('undefined returns false', () => {
      expect(isAdmin(undefined)).toBe(false);
    });
  });
});
