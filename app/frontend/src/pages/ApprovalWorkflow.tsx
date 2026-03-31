import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Users, Clock, CheckCircle2, XCircle, AlertTriangle,
  Send, Eye, ChevronRight, FileText, Layers, BookOpen,
  Filter, Flag, X,
} from 'lucide-react';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import KpiCard from '../components/KpiCard';
import PageHeader from '../components/PageHeader';
import PageLoader from '../components/PageLoader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api, type RbacUser, type ApprovalRequest } from '../lib/api';
import { fmtDateTime } from '../lib/format';

const REQUEST_TYPE_CONFIG: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  model_approval:   { label: 'Model Approval',   color: 'text-blue-700',    bg: 'bg-blue-50 border-blue-200',      icon: FileText },
  overlay_approval: { label: 'Overlay Approval',  color: 'text-purple-700',  bg: 'bg-purple-50 border-purple-200',  icon: Layers },
  journal_posting:  { label: 'Journal Posting',   color: 'text-amber-700',   bg: 'bg-amber-50 border-amber-200',    icon: BookOpen },
  sign_off:         { label: 'Sign Off',          color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200', icon: CheckCircle2 },
};

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  pending:   { label: 'Pending',   color: 'text-amber-700',   bg: 'bg-amber-50 border-amber-200',    icon: Clock },
  approved:  { label: 'Approved',  color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200', icon: CheckCircle2 },
  rejected:  { label: 'Rejected',  color: 'text-red-700',     bg: 'bg-red-50 border-red-200',         icon: XCircle },
  escalated: { label: 'Escalated', color: 'text-orange-700',  bg: 'bg-orange-50 border-orange-200',   icon: AlertTriangle },
};

const ROLE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  analyst:  { label: 'Analyst',  color: 'text-blue-700',    bg: 'bg-blue-50 border-blue-200' },
  reviewer: { label: 'Reviewer', color: 'text-purple-700',  bg: 'bg-purple-50 border-purple-200' },
  approver: { label: 'Approver', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  admin:    { label: 'Admin',    color: 'text-red-700',     bg: 'bg-red-50 border-red-200' },
};

const TABS = ['Dashboard', 'Pending Queue', 'History', 'Users'] as const;
type Tab = typeof TABS[number];

function TypeBadge({ type }: { type: string }) {
  const cfg = REQUEST_TYPE_CONFIG[type] || REQUEST_TYPE_CONFIG.model_approval;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${cfg.bg} ${cfg.color}`}>
      <Icon size={11} /> {cfg.label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${cfg.bg} ${cfg.color}`}>
      <Icon size={11} /> {cfg.label}
    </span>
  );
}

function RoleBadge({ role }: { role: string }) {
  const cfg = ROLE_CONFIG[role] || ROLE_CONFIG.analyst;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${cfg.bg} ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const isUrgent = priority === 'urgent';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
      isUrgent ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-slate-50 text-slate-500 border border-slate-200'
    }`}>
      <Flag size={9} /> {isUrgent ? 'Urgent' : 'Normal'}
    </span>
  );
}

interface CreateRequestModalProps {
  users: RbacUser[];
  onSubmit: (data: any) => Promise<void>;
  onClose: () => void;
}

function CreateRequestModal({ users, onSubmit, onClose }: CreateRequestModalProps) {
  const [form, setForm] = useState({
    request_type: 'model_approval',
    entity_id: '',
    entity_type: '',
    requested_by: users.find(u => u.role === 'analyst')?.user_id || '',
    assigned_to: users.find(u => u.role === 'approver')?.user_id || '',
    priority: 'normal',
    due_date: '',
    comments: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(form);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700">
          <h3 className="text-sm font-bold text-slate-700">New Approval Request</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition"><X size={16} className="text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Request Type</label>
              <select value={form.request_type} onChange={e => setForm({ ...form, request_type: e.target.value })} className="form-input text-xs w-full">
                <option value="model_approval">Model Approval</option>
                <option value="overlay_approval">Overlay Approval</option>
                <option value="journal_posting">Journal Posting</option>
                <option value="sign_off">Sign Off</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Priority</label>
              <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="form-input text-xs w-full">
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Entity ID</label>
            <input value={form.entity_id} onChange={e => setForm({ ...form, entity_id: e.target.value })}
              placeholder="e.g. PD-Model-v3, OVL-2024-Q4" className="form-input text-xs w-full" required />
          </div>
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Entity Type</label>
            <input value={form.entity_type} onChange={e => setForm({ ...form, entity_type: e.target.value })}
              placeholder="e.g. PD Model, Management Overlay" className="form-input text-xs w-full" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Requested By</label>
              <select value={form.requested_by} onChange={e => setForm({ ...form, requested_by: e.target.value })} className="form-input text-xs w-full">
                {users.map(u => <option key={u.user_id} value={u.user_id}>{u.display_name} ({u.role})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Assigned To</label>
              <select value={form.assigned_to} onChange={e => setForm({ ...form, assigned_to: e.target.value })} className="form-input text-xs w-full">
                <option value="">Auto-assign</option>
                {users.filter(u => u.role === 'approver' || u.role === 'admin').map(u =>
                  <option key={u.user_id} value={u.user_id}>{u.display_name} ({u.role})</option>
                )}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Due Date</label>
            <input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} className="form-input text-xs w-full" />
          </div>
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Comments</label>
            <textarea value={form.comments} onChange={e => setForm({ ...form, comments: e.target.value })}
              placeholder="Describe the approval request..." className="form-input text-xs w-full h-20 resize-none" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary text-xs">Cancel</button>
            <button type="submit" disabled={submitting || !form.entity_id}
              className="btn-primary text-xs disabled:opacity-50">
              <Send size={12} /> {submitting ? 'Creating...' : 'Create Request'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

interface RequestDetailProps {
  request: ApprovalRequest;
  users: RbacUser[];
  onApprove: (requestId: string, userId: string, comment: string) => Promise<void>;
  onReject: (requestId: string, userId: string, comment: string) => Promise<void>;
  onClose: () => void;
}

function RequestDetail({ request, users, onApprove, onReject, onClose }: RequestDetailProps) {
  const [actionUser, setActionUser] = useState(users.find(u => u.role === 'approver')?.user_id || '');
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  const handleAction = async (action: 'approve' | 'reject') => {
    setActing(true);
    try {
      if (action === 'approve') await onApprove(request.request_id, actionUser, comment);
      else await onReject(request.request_id, actionUser, comment);
      onClose();
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700">
          <div>
            <h3 className="text-sm font-bold text-slate-700">Approval Request</h3>
            <p className="text-[10px] text-slate-400 font-mono mt-0.5">{request.request_id}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition"><X size={16} className="text-slate-400" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Type</p>
              <TypeBadge type={request.request_type} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Status</p>
              <StatusBadge status={request.status} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Entity</p>
              <p className="text-xs font-semibold text-slate-700">{request.entity_id}</p>
              {request.entity_type && <p className="text-[10px] text-slate-400">{request.entity_type}</p>}
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Priority</p>
              <PriorityBadge priority={request.priority} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Requested By</p>
              <p className="text-xs font-semibold text-slate-700">{request.requested_by_name || request.requested_by}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Assigned To</p>
              <p className="text-xs font-semibold text-slate-700">{request.assigned_to_name || request.assigned_to || '—'}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Created</p>
              <p className="text-xs text-slate-600">{fmtDateTime(request.created_at)}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Due Date</p>
              <p className="text-xs text-slate-600">{request.due_date || '—'}</p>
            </div>
          </div>
          {request.comments && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Comments</p>
              <p className="text-xs text-slate-600 bg-slate-50 rounded-xl p-3">{request.comments}</p>
            </div>
          )}
          {request.status === 'approved' && request.approved_by_name && (
            <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-100">
              <p className="text-xs font-semibold text-emerald-700">Approved by {request.approved_by_name}</p>
              <p className="text-[10px] text-emerald-600">{fmtDateTime(request.approved_at)}</p>
            </div>
          )}
          {request.status === 'rejected' && (
            <div className="bg-red-50 rounded-xl p-3 border border-red-100">
              <p className="text-xs font-semibold text-red-700">Rejected by {request.approved_by_name}</p>
              {request.rejection_reason && <p className="text-[10px] text-red-600 mt-1">{request.rejection_reason}</p>}
            </div>
          )}
          {request.status === 'pending' && (
            <div className="border-t border-slate-100 pt-4 space-y-3">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Action By</label>
                <select value={actionUser} onChange={e => setActionUser(e.target.value)} className="form-input text-xs w-full">
                  {users.filter(u => u.role === 'approver' || u.role === 'admin').map(u =>
                    <option key={u.user_id} value={u.user_id}>{u.display_name} ({u.role})</option>
                  )}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Comment</label>
                <textarea value={comment} onChange={e => setComment(e.target.value)}
                  placeholder="Add a comment..." className="form-input text-xs w-full h-16 resize-none" />
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => handleAction('reject')} disabled={acting}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 transition disabled:opacity-50">
                  <XCircle size={13} /> Reject
                </button>
                <button onClick={() => handleAction('approve')} disabled={acting}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white gradient-brand shadow-md hover:opacity-90 transition disabled:opacity-50">
                  <CheckCircle2 size={13} /> Approve
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default function ApprovalWorkflow() {
  const [users, setUsers] = useState<RbacUser[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('Dashboard');
  const [showCreate, setShowCreate] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setError(null);
    try {
      const [u, a] = await Promise.all([api.rbacListUsers(), api.rbacListApprovals()]);
      setUsers(u);
      setApprovals(a);
    } catch (e: any) {
      setError(e.message || 'Failed to load approval workflow data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const pending = useMemo(() => approvals.filter(a => a.status === 'pending'), [approvals]);
  const approvedToday = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return approvals.filter(a => a.status === 'approved' && a.approved_at?.startsWith(today));
  }, [approvals]);
  const rejected = useMemo(() => approvals.filter(a => a.status === 'rejected'), [approvals]);
  const overdue = useMemo(() => {
    const now = new Date();
    return pending.filter(a => a.due_date && new Date(a.due_date) < now);
  }, [pending]);

  const filteredApprovals = useMemo(() => {
    let result = approvals;
    if (filterType) result = result.filter(a => a.request_type === filterType);
    if (filterStatus) result = result.filter(a => a.status === filterStatus);
    return result;
  }, [approvals, filterType, filterStatus]);

  const handleCreate = async (data: any) => {
    await api.rbacCreateApproval(data);
    await loadData();
  };

  const handleApprove = async (requestId: string, userId: string, comment: string) => {
    await api.rbacApprove(requestId, userId, comment);
    await loadData();
  };

  const handleReject = async (requestId: string, userId: string, comment: string) => {
    await api.rbacReject(requestId, userId, comment);
    await loadData();
  };

  if (loading) return <PageLoader />;

  if (error && approvals.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Approval Workflow" subtitle="Maker-Checker-Approver governance for IFRS 9 ECL" />
        <ErrorDisplay title="Failed to load approvals" message={error} technicalDetails={error}
          onRetry={() => { setLoading(true); loadData(); }} onDismiss={() => setError(null)} />
      </div>
    );
  }

  if (approvals.length === 0 && users.length > 0 && !error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Approval Workflow" subtitle="Maker-Checker-Approver governance for IFRS 9 ECL">
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white gradient-brand shadow-md hover:opacity-90 transition">
            <Send size={13} /> New Request
          </button>
        </PageHeader>
        <Card>
          <EmptyState
            icon={<Shield size={48} />}
            title="No approval requests"
            description="Create a request to start the governance workflow."
            action={{ label: 'New Request', onClick: () => setShowCreate(true) }}
          />
        </Card>
        <AnimatePresence>
          {showCreate && (
            <CreateRequestModal users={users} onSubmit={handleCreate} onClose={() => setShowCreate(false)} />
          )}
        </AnimatePresence>
      </div>
    );
  }

  const pendingColumns = [
    { key: 'request_type', label: 'Type', format: (v: string) => <TypeBadge type={v} /> },
    { key: 'entity_id', label: 'Entity', format: (v: string, row: any) => (
      <div>
        <p className="font-semibold text-slate-700">{v}</p>
        {row.entity_type && <p className="text-[10px] text-slate-400">{row.entity_type}</p>}
      </div>
    )},
    { key: 'requested_by_name', label: 'Requested By', format: (v: string) => <span className="text-slate-600">{v || '—'}</span> },
    { key: 'assigned_to_name', label: 'Assigned To', format: (v: string) => <span className="text-slate-600">{v || '—'}</span> },
    { key: 'priority', label: 'Priority', format: (v: string) => <PriorityBadge priority={v} /> },
    { key: 'due_date', label: 'Due Date', format: (v: string) => {
      if (!v) return <span className="text-slate-300">—</span>;
      const isOverdue = new Date(v) < new Date();
      return <span className={`text-xs ${isOverdue ? 'text-red-600 font-bold' : 'text-slate-600'}`}>{v}</span>;
    }},
    { key: 'created_at', label: 'Created', format: (v: string) => <span className="text-slate-500 text-[11px]">{fmtDateTime(v)}</span> },
    { key: '_actions', label: '', format: (_: any, row: ApprovalRequest) => (
      <button onClick={(e) => { e.stopPropagation(); setSelectedRequest(row); }}
        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-brand bg-brand/5 hover:bg-brand/10 transition">
        <Eye size={11} /> Review
      </button>
    )},
  ];

  const historyColumns = [
    { key: 'request_type', label: 'Type', format: (v: string) => <TypeBadge type={v} /> },
    { key: 'entity_id', label: 'Entity' },
    { key: 'status', label: 'Status', format: (v: string) => <StatusBadge status={v} /> },
    { key: 'requested_by_name', label: 'Requested By' },
    { key: 'approved_by_name', label: 'Actioned By', format: (v: string) => v || '—' },
    { key: 'priority', label: 'Priority', format: (v: string) => <PriorityBadge priority={v} /> },
    { key: 'created_at', label: 'Created', format: (v: string) => <span className="text-[11px]">{fmtDateTime(v)}</span> },
    { key: 'approved_at', label: 'Actioned At', format: (v: string) => v ? <span className="text-[11px]">{fmtDateTime(v)}</span> : '—' },
  ];

  const userColumns = [
    { key: 'display_name', label: 'Name', format: (v: string, row: RbacUser) => (
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-slate-500 font-bold text-xs">
          {v.split(' ').map(n => n[0]).join('')}
        </div>
        <div>
          <p className="font-semibold text-slate-700">{v}</p>
          <p className="text-[10px] text-slate-400">{row.email}</p>
        </div>
      </div>
    )},
    { key: 'role', label: 'Role', format: (v: string) => <RoleBadge role={v} /> },
    { key: 'department', label: 'Department' },
    { key: 'is_active', label: 'Status', format: (v: boolean) => (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
        v ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-slate-50 text-slate-400 border border-slate-200'
      }`}>
        <div className={`w-1.5 h-1.5 rounded-full ${v ? 'bg-emerald-500' : 'bg-slate-300'}`} /> {v ? 'Active' : 'Inactive'}
      </span>
    )},
    { key: 'created_at', label: 'Joined', format: (v: string) => <span className="text-[11px]">{fmtDateTime(v)}</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Approval Workflow" subtitle="Maker-Checker-Approver governance for IFRS 9 ECL">
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white gradient-brand shadow-md hover:opacity-90 transition">
          <Send size={13} /> New Request
        </button>
      </PageHeader>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === tab ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}>
            {tab}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>

          {/* Dashboard Tab */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <KpiCard title="Pending Approvals" value={String(pending.length)} subtitle="Awaiting action"
                  icon={<Clock size={20} />} color="amber" />
                <KpiCard title="Approved Today" value={String(approvedToday.length)} subtitle="Completed today"
                  icon={<CheckCircle2 size={20} />} color="green" />
                <KpiCard title="Rejected" value={String(rejected.length)} subtitle="Total rejected"
                  icon={<XCircle size={20} />} color="red" />
                <KpiCard title="Overdue" value={String(overdue.length)} subtitle="Past due date"
                  icon={<AlertTriangle size={20} />} color={overdue.length > 0 ? 'red' : 'blue'} />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <Card title="Recent Pending" subtitle="Requests awaiting action" icon={<Clock size={16} />} accent="amber">
                  {pending.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 text-sm">No pending approvals</div>
                  ) : (
                    <div className="space-y-2">
                      {pending.slice(0, 5).map(req => (
                        <button key={req.request_id} onClick={() => setSelectedRequest(req)}
                          className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition text-left group">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <TypeBadge type={req.request_type} />
                              <PriorityBadge priority={req.priority} />
                            </div>
                            <p className="text-xs font-semibold text-slate-700 truncate">{req.entity_id}</p>
                            <p className="text-[10px] text-slate-400">by {req.requested_by_name || req.requested_by}</p>
                          </div>
                          <ChevronRight size={14} className="text-slate-300 group-hover:text-brand transition" />
                        </button>
                      ))}
                    </div>
                  )}
                </Card>

                <Card title="User Directory" subtitle="Team roles and permissions" icon={<Users size={16} />} accent="blue">
                  <div className="space-y-2">
                    {users.map(user => (
                      <div key={user.user_id} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50/50">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center text-slate-600 font-bold text-xs">
                          {user.display_name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-slate-700">{user.display_name}</p>
                          <p className="text-[10px] text-slate-400">{user.department}</p>
                        </div>
                        <RoleBadge role={user.role} />
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <Card title="Approval Pipeline" subtitle="All requests by status" icon={<Shield size={16} />} accent="brand">
                <div className="grid grid-cols-4 gap-4">
                  {(['pending', 'approved', 'rejected', 'escalated'] as const).map(status => {
                    const items = approvals.filter(a => a.status === status);
                    const cfg = STATUS_CONFIG[status];
                    const Icon = cfg.icon;
                    return (
                      <div key={status} className="text-center">
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.color} mb-3`}>
                          <Icon size={12} /> {cfg.label}
                        </div>
                        <p className="text-2xl font-extrabold text-slate-800">{items.length}</p>
                        <p className="text-[10px] text-slate-400 mt-1">
                          {items.filter(a => a.priority === 'urgent').length} urgent
                        </p>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>
          )}

          {/* Pending Queue Tab */}
          {activeTab === 'Pending Queue' && (
            <Card title="Pending Approval Queue" subtitle={`${pending.length} requests awaiting action`}
              icon={<Clock size={16} />} accent="amber">
              <DataTable columns={pendingColumns} data={pending} pageSize={10}
                onRowClick={(row) => setSelectedRequest(row)} exportName="pending_approvals" />
            </Card>
          )}

          {/* History Tab */}
          {activeTab === 'History' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Filter size={14} className="text-slate-400" />
                  <select value={filterType} onChange={e => setFilterType(e.target.value)} className="form-input text-xs">
                    <option value="">All Types</option>
                    <option value="model_approval">Model Approval</option>
                    <option value="overlay_approval">Overlay Approval</option>
                    <option value="journal_posting">Journal Posting</option>
                    <option value="sign_off">Sign Off</option>
                  </select>
                </div>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="form-input text-xs">
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <Card title="Approval History" subtitle={`${filteredApprovals.length} total requests`}
                icon={<FileText size={16} />} accent="blue">
                <DataTable columns={historyColumns} data={filteredApprovals} pageSize={15}
                  onRowClick={(row) => setSelectedRequest(row)} exportName="approval_history" />
              </Card>
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'Users' && (
            <div className="space-y-6">
              <Card title="User Directory" subtitle={`${users.length} active users`}
                icon={<Users size={16} />} accent="purple">
                <DataTable columns={userColumns} data={users} pageSize={10} exportName="rbac_users" />
              </Card>

              <Card title="Role Permissions Matrix" subtitle="Actions available per role" icon={<Shield size={16} />} accent="brand">
                <div className="overflow-x-auto rounded-2xl border border-slate-100">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gradient-to-r from-slate-100 to-slate-50 text-slate-700 dark:from-slate-800 dark:to-slate-700 dark:text-white">
                        <th className="py-2.5 px-4 text-left text-[10px] font-bold uppercase tracking-wider">Permission</th>
                        <th className="py-2.5 px-4 text-center text-[10px] font-bold uppercase tracking-wider">Analyst</th>
                        <th className="py-2.5 px-4 text-center text-[10px] font-bold uppercase tracking-wider">Reviewer</th>
                        <th className="py-2.5 px-4 text-center text-[10px] font-bold uppercase tracking-wider">Approver</th>
                        <th className="py-2.5 px-4 text-center text-[10px] font-bold uppercase tracking-wider">Admin</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        'create_models', 'run_backtests', 'generate_journals', 'create_overlays',
                        'submit_for_approval', 'review_models', 'review_overlays',
                        'approve_requests', 'reject_requests', 'sign_off_projects', 'post_journals',
                        'manage_users', 'manage_config',
                      ].map((perm, i) => (
                        <tr key={perm} className={i % 2 === 1 ? 'bg-slate-50/40 dark:bg-white/[0.02]' : ''}>
                          <td className="py-2 px-4 font-medium text-slate-700">{perm.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</td>
                          {['analyst', 'reviewer', 'approver', 'admin'].map(role => {
                            const perms: Record<string, Set<string>> = {
                              analyst: new Set(['create_models', 'run_backtests', 'generate_journals', 'create_overlays', 'view_portfolio', 'view_reports']),
                              reviewer: new Set(['create_models', 'run_backtests', 'generate_journals', 'create_overlays', 'view_portfolio', 'view_reports', 'submit_for_approval', 'review_models', 'review_overlays']),
                              approver: new Set(['create_models', 'run_backtests', 'generate_journals', 'create_overlays', 'view_portfolio', 'view_reports', 'submit_for_approval', 'review_models', 'review_overlays', 'approve_requests', 'reject_requests', 'sign_off_projects', 'post_journals']),
                              admin: new Set(['create_models', 'run_backtests', 'generate_journals', 'create_overlays', 'view_portfolio', 'view_reports', 'submit_for_approval', 'review_models', 'review_overlays', 'approve_requests', 'reject_requests', 'sign_off_projects', 'post_journals', 'manage_users', 'manage_config', 'manage_roles']),
                            };
                            const has = perms[role]?.has(perm);
                            return (
                              <td key={role} className="py-2 px-4 text-center">
                                {has ? (
                                  <CheckCircle2 size={14} className="text-emerald-500 mx-auto" />
                                ) : (
                                  <XCircle size={14} className="text-slate-200 mx-auto" />
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Modals */}
      <AnimatePresence>
        {showCreate && (
          <CreateRequestModal users={users} onSubmit={handleCreate} onClose={() => setShowCreate(false)} />
        )}
        {selectedRequest && (
          <RequestDetail request={selectedRequest} users={users}
            onApprove={handleApprove} onReject={handleReject}
            onClose={() => setSelectedRequest(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
