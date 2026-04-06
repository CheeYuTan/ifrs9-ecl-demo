import { useState, useEffect, useCallback } from 'react';
import { Users, UserPlus, Crown, Trash2, ArrowRightLeft, Shield } from 'lucide-react';
import { api, type ProjectMembersResponse } from '../lib/api';
import { usePermissions } from '../hooks/usePermissions';
import { PROJECT_ROLE_LABELS, type ProjectRole } from '../lib/permissions';
import ConfirmDialog from './ConfirmDialog';

interface Props {
  projectId: string;
}

const ASSIGNABLE_ROLES: ProjectRole[] = ['viewer', 'editor', 'manager'];

export default function ProjectMembers({ projectId }: Props) {
  const { canManage, canOwn } = usePermissions(projectId);
  const [data, setData] = useState<ProjectMembersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newUserId, setNewUserId] = useState('');
  const [newRole, setNewRole] = useState<ProjectRole>('viewer');
  const [adding, setAdding] = useState(false);
  const [confirm, setConfirm] = useState<{ type: 'remove' | 'transfer'; userId: string; name: string } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchMembers = useCallback(() => {
    setLoading(true);
    api.getProjectMembers(projectId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [projectId]);

  useEffect(fetchMembers, [fetchMembers]);

  const handleAdd = async () => {
    if (!newUserId.trim()) return;
    setAdding(true);
    try {
      await api.addProjectMember(projectId, newUserId.trim(), newRole);
      setNewUserId('');
      setNewRole('viewer');
      fetchMembers();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAdding(false);
    }
  };

  const handleConfirmAction = async () => {
    if (!confirm) return;
    setActionLoading(true);
    try {
      if (confirm.type === 'remove') {
        await api.removeProjectMember(projectId, confirm.userId);
      } else {
        await api.transferOwnership(projectId, confirm.userId);
      }
      setConfirm(null);
      fetchMembers();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center gap-2 text-xs text-slate-400 animate-pulse">
          <Users size={14} /> Loading members...
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 dark:border-slate-700">
          <Shield size={14} className="text-indigo-500" />
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Project Members</h3>
          {data && (
            <span className="ml-auto text-xs text-slate-400">{data.members.length + (data.owner ? 1 : 0)}</span>
          )}
        </div>

        {error && (
          <div className="px-4 py-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20">{error}</div>
        )}

        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {/* Owner */}
          {data?.owner && (
            <div className="flex items-center gap-3 px-4 py-2.5">
              <Crown size={14} className="text-amber-500 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                  {data.owner.display_name}
                </p>
                <p className="text-xs text-slate-400 truncate">{data.owner.email}</p>
              </div>
              <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 px-2 py-0.5 rounded-full">
                Owner
              </span>
            </div>
          )}

          {/* Members */}
          {data?.members.map((m) => (
            <div key={m.user_id} className="flex items-center gap-3 px-4 py-2.5 group">
              <Users size={14} className="text-slate-400 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                  {m.display_name || m.user_id}
                </p>
                {m.email && <p className="text-xs text-slate-400 truncate">{m.email}</p>}
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-full">
                {PROJECT_ROLE_LABELS[m.role]}
              </span>
              {canManage && (
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {canOwn && (
                    <button
                      title="Transfer ownership"
                      onClick={() => setConfirm({ type: 'transfer', userId: m.user_id, name: m.display_name || m.user_id })}
                      className="p-1 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-indigo-500 transition"
                    >
                      <ArrowRightLeft size={13} />
                    </button>
                  )}
                  <button
                    title="Remove member"
                    onClick={() => setConfirm({ type: 'remove', userId: m.user_id, name: m.display_name || m.user_id })}
                    className="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-red-500 transition"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              )}
            </div>
          ))}

          {data?.members.length === 0 && !data.owner && (
            <div className="px-4 py-6 text-xs text-slate-400 text-center">No members yet</div>
          )}
        </div>

        {/* Add member form */}
        {canManage && (
          <div className="px-4 py-3 border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/30">
            <div className="flex items-center gap-2">
              <UserPlus size={14} className="text-slate-400 shrink-0" />
              <input
                type="text"
                value={newUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                placeholder="User ID or email"
                className="flex-1 min-w-0 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 outline-none focus:ring-1 focus:ring-indigo-400"
              />
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value as ProjectRole)}
                className="text-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none"
              >
                {ASSIGNABLE_ROLES.map((r) => (
                  <option key={r} value={r}>{PROJECT_ROLE_LABELS[r]}</option>
                ))}
              </select>
              <button
                onClick={handleAdd}
                disabled={adding || !newUserId.trim()}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition disabled:opacity-50"
              >
                {adding ? 'Adding...' : 'Add'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirm dialogs */}
      <ConfirmDialog
        open={confirm?.type === 'remove'}
        title="Remove Member"
        description={`Remove ${confirm?.name} from this project? They will lose all access.`}
        confirmLabel="Remove"
        variant="danger"
        loading={actionLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirm(null)}
      />
      <ConfirmDialog
        open={confirm?.type === 'transfer'}
        title="Transfer Ownership"
        description={`Transfer project ownership to ${confirm?.name}? You will be demoted to manager.`}
        confirmLabel="Transfer"
        variant="warning"
        icon={<ArrowRightLeft size={16} className="text-amber-500" />}
        loading={actionLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirm(null)}
      />
    </>
  );
}
