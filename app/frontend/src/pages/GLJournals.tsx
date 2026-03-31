import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, FileText, CheckCircle2, RotateCcw, Play,
  AlertTriangle, Scale, List, BarChart3, DollarSign, XCircle, Clock,
} from 'lucide-react';
import Card from '../components/Card';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import ConfirmDialog from '../components/ConfirmDialog';
import { api, type GLJournal, type GLTrialBalanceRow, type GLAccount, type Project } from '../lib/api';
import { getCurrentUser } from '../lib/userContext';

const fmt = (v: number | null | undefined) => v != null ? v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—';

const STATUS_STYLES: Record<string, { bg: string; icon: typeof CheckCircle2; label: string }> = {
  draft: { bg: 'bg-amber-50 text-amber-700 border-amber-200', icon: Clock, label: 'Draft' },
  posted: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2, label: 'Posted' },
  reversed: { bg: 'bg-red-50 text-red-700 border-red-200', icon: XCircle, label: 'Reversed' },
};

const TYPE_LABELS: Record<string, string> = {
  ecl_provision: 'ECL Provision',
  write_off: 'Write-off',
  recovery: 'Recovery',
  overlay: 'Overlay',
};

function JournalStatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.draft;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${s.bg}`}>
      <Icon size={12} /> {s.label}
    </span>
  );
}

function BalanceIndicator({ balanced, debit, credit }: { balanced: boolean; debit: number; credit: number }) {
  if (balanced) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <Scale size={12} /> Balanced
      </span>
    );
  }
  const diff = Math.abs(debit - credit);
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
      <AlertTriangle size={12} /> Imbalance: {fmt(diff)}
    </span>
  );
}

type Tab = 'journals' | 'trial-balance' | 'chart';

export default function GLJournals({ project }: { project: Project | null }) {
  const [tab, setTab] = useState<Tab>('journals');
  const [journals, setJournals] = useState<GLJournal[]>([]);
  const [selectedJournal, setSelectedJournal] = useState<GLJournal | null>(null);
  const [trialBalance, setTrialBalance] = useState<GLTrialBalanceRow[]>([]);
  const [chart, setChart] = useState<GLAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reverseConfirm, setReverseConfirm] = useState<string | null>(null);
  const [reverseLoading, setReverseLoading] = useState(false);

  const projectId = project?.project_id || '';

  const loadJournals = useCallback(async () => {
    if (!projectId) return;
    try {
      const data = await api.glListJournals(projectId);
      setJournals(data);
    } catch (e: any) {
      setError(e.message);
    }
  }, [projectId]);

  const loadTrialBalance = useCallback(async () => {
    if (!projectId) return;
    try {
      setTrialBalance(await api.glTrialBalance(projectId));
    } catch (e: any) {
      setError(e.message);
    }
  }, [projectId]);

  const loadChart = useCallback(async () => {
    try {
      setChart(await api.glChartOfAccounts());
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadJournals(), loadChart(), loadTrialBalance()])
      .finally(() => setLoading(false));
  }, [loadJournals, loadChart, loadTrialBalance]);

  const handleGenerate = async () => {
    if (!projectId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.glGenerateJournals(projectId, getCurrentUser());
      await loadJournals();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handlePost = async (journalId: string) => {
    try {
      await api.glPostJournal(journalId, getCurrentUser());
      await loadJournals();
      await loadTrialBalance();
      if (selectedJournal?.journal_id === journalId) {
        setSelectedJournal(await api.glGetJournal(journalId));
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleReverse = (journalId: string) => {
    setReverseConfirm(journalId);
  };

  const confirmReverse = async () => {
    if (!reverseConfirm) return;
    setReverseLoading(true);
    try {
      await api.glReverseJournal(reverseConfirm, getCurrentUser(), 'Reversed via confirmation dialog');
      await loadJournals();
      await loadTrialBalance();
      setSelectedJournal(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setReverseLoading(false);
      setReverseConfirm(null);
    }
  };

  const handleSelectJournal = async (journal: GLJournal) => {
    try {
      const detail = await api.glGetJournal(journal.journal_id);
      setSelectedJournal(detail);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const totalDebit = journals.reduce((s, j) => s + (j.status === 'posted' ? j.total_debit : 0), 0);
  const totalCredit = journals.reduce((s, j) => s + (j.status === 'posted' ? j.total_credit : 0), 0);
  const draftCount = journals.filter(j => j.status === 'draft').length;
  const postedCount = journals.filter(j => j.status === 'posted').length;

  const tabs: { key: Tab; label: string; icon: typeof BookOpen }[] = [
    { key: 'journals', label: 'Journal Entries', icon: FileText },
    { key: 'trial-balance', label: 'Trial Balance', icon: BarChart3 },
    { key: 'chart', label: 'Chart of Accounts', icon: List },
  ];

  if (!project) {
    return (
      <div className="text-center py-20 text-slate-400">
        <BookOpen size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-lg font-semibold">Select a project to view GL journals</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="GL Journal Entries & Ledger"
        subtitle="Generate, post, and manage IFRS 9 ECL journal entries"
      >
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white gradient-brand rounded-2xl shadow-lg glow-brand hover:opacity-90 transition disabled:opacity-50"
        >
          {generating ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Play size={15} />
          )}
          {generating ? 'Generating...' : 'Generate ECL Journals'}
        </button>
      </PageHeader>

      {error && (
        <ErrorDisplay title="Operation failed" message={error} technicalDetails={error}
          onRetry={() => { setError(null); loadJournals(); }} onDismiss={() => setError(null)} />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard title="Total Journals" value={String(journals.length)} icon={<FileText size={20} />} color="blue"
          subtitle={`${draftCount} draft, ${postedCount} posted`} />
        <KpiCard title="Posted Debits" value={fmt(totalDebit)} icon={<DollarSign size={20} />} color="green"
          subtitle="Total debit entries" />
        <KpiCard title="Posted Credits" value={fmt(totalCredit)} icon={<DollarSign size={20} />} color="purple"
          subtitle="Total credit entries" />
        <KpiCard title="Balance Check" value={Math.abs(totalDebit - totalCredit) < 0.01 ? 'Balanced' : fmt(Math.abs(totalDebit - totalCredit))}
          icon={<Scale size={20} />} color={Math.abs(totalDebit - totalCredit) < 0.01 ? 'teal' : 'red'}
          subtitle={Math.abs(totalDebit - totalCredit) < 0.01 ? 'Debits = Credits' : 'Imbalance detected'} />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-slate-100 rounded-2xl p-1">
        {tabs.map(t => {
          const Icon = t.icon;
          const active = tab === t.key;
          return (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                active ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}>
              <Icon size={15} />
              {t.label}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" />
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            {tab === 'journals' && (
              <JournalListView
                journals={journals}
                selectedJournal={selectedJournal}
                onSelect={handleSelectJournal}
                onPost={handlePost}
                onReverse={handleReverse}
                onClose={() => setSelectedJournal(null)}
              />
            )}
            {tab === 'trial-balance' && <TrialBalanceView data={trialBalance} />}
            {tab === 'chart' && <ChartOfAccountsView data={chart} />}
          </motion.div>
        </AnimatePresence>
      )}

      <ConfirmDialog
        open={!!reverseConfirm}
        title="Reverse Journal Entry"
        description="Are you sure you want to reverse this journal entry? This will create an offsetting entry and cannot be undone."
        confirmLabel="Reverse Entry"
        variant="danger"
        icon={<RotateCcw size={16} className="text-red-500" />}
        onConfirm={confirmReverse}
        onCancel={() => setReverseConfirm(null)}
        loading={reverseLoading}
      />
    </div>
  );
}

function JournalListView({
  journals, selectedJournal, onSelect, onPost, onReverse, onClose,
}: {
  journals: GLJournal[];
  selectedJournal: GLJournal | null;
  onSelect: (j: GLJournal) => void;
  onPost: (id: string) => void;
  onReverse: (id: string) => void;
  onClose: () => void;
}) {
  if (journals.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={<FileText size={48} />}
          title="No journal entries yet"
          description="Generate ECL journals from a completed project."
        />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card title="Journal Entries" icon={<FileText size={16} />} accent="brand">
        <DataTable
          columns={[
            { key: 'journal_id', label: 'Journal ID', format: (v: string) => (
              <span className="font-mono text-xs text-brand font-semibold">{v}</span>
            )},
            { key: 'journal_type', label: 'Type', format: (v: string) => (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-xs font-medium text-slate-600">
                {TYPE_LABELS[v] || v}
              </span>
            )},
            { key: 'journal_date', label: 'Date' },
            { key: 'status', label: 'Status', format: (v: string) => <JournalStatusBadge status={v} /> },
            { key: 'total_debit', label: 'Debit', align: 'right', format: (v: number) => (
              <span className="font-mono font-semibold text-slate-700">{fmt(v)}</span>
            )},
            { key: 'total_credit', label: 'Credit', align: 'right', format: (v: number) => (
              <span className="font-mono font-semibold text-slate-700">{fmt(v)}</span>
            )},
            { key: 'balanced', label: 'Balance', align: 'center', format: (_: boolean, row: GLJournal) => (
              <BalanceIndicator balanced={row.balanced} debit={row.total_debit} credit={row.total_credit} />
            )},
            { key: 'line_count', label: 'Lines', align: 'center' },
          ]}
          data={journals}
          onRowClick={onSelect}
          exportName="gl_journals"
          compact
        />
      </Card>

      <AnimatePresence>
        {selectedJournal && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <JournalDetail journal={selectedJournal} onPost={onPost} onReverse={onReverse} onClose={onClose} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function JournalDetail({
  journal, onPost, onReverse, onClose,
}: {
  journal: GLJournal;
  onPost: (id: string) => void;
  onReverse: (id: string) => void;
  onClose: () => void;
}) {
  const lines = journal.lines || [];
  const debitLines = lines.filter(l => l.debit > 0);
  const creditLines = lines.filter(l => l.credit > 0);

  return (
    <Card title={`Journal: ${journal.journal_id}`} subtitle={journal.description}
      icon={<BookOpen size={16} />} accent="blue"
      action={
        <div className="flex items-center gap-2">
          <JournalStatusBadge status={journal.status} />
          <BalanceIndicator balanced={journal.balanced} debit={journal.total_debit} credit={journal.total_credit} />
          {journal.status === 'draft' && (
            <button onClick={() => onPost(journal.journal_id)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-500 rounded-xl hover:bg-emerald-600 transition shadow-sm">
              <CheckCircle2 size={13} /> Post
            </button>
          )}
          {journal.status === 'posted' && (
            <button onClick={() => onReverse(journal.journal_id)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-red-500 rounded-xl hover:bg-red-600 transition shadow-sm">
              <RotateCcw size={13} /> Reverse
            </button>
          )}
          <button onClick={onClose}
            className="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-slate-500 bg-slate-100 rounded-xl hover:bg-slate-200 transition">
            <XCircle size={13} /> Close
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-4 gap-4 mb-5 text-xs">
        <div className="bg-slate-50 rounded-xl p-3">
          <p className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Type</p>
          <p className="font-bold text-slate-700 mt-1">{TYPE_LABELS[journal.journal_type] || journal.journal_type}</p>
        </div>
        <div className="bg-slate-50 rounded-xl p-3">
          <p className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Date</p>
          <p className="font-bold text-slate-700 mt-1">{journal.journal_date}</p>
        </div>
        <div className="bg-slate-50 rounded-xl p-3">
          <p className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Created By</p>
          <p className="font-bold text-slate-700 mt-1">{journal.created_by}</p>
        </div>
        <div className="bg-slate-50 rounded-xl p-3">
          <p className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Reference</p>
          <p className="font-bold text-slate-700 mt-1 font-mono">{journal.reference}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Debit Side */}
        <div>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" /> Debits
          </h4>
          <div className="space-y-2">
            {debitLines.map(l => (
              <div key={l.line_id} className="flex items-center justify-between bg-blue-50/50 border border-blue-100 rounded-xl px-4 py-2.5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-700">{l.account_name || l.account_code}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {l.account_code} &middot; {l.product_type}{l.stage ? ` &middot; Stage ${l.stage}` : ''}
                  </p>
                </div>
                <span className="font-mono font-bold text-sm text-blue-700">{fmt(l.debit)}</span>
              </div>
            ))}
            <div className="flex justify-end pt-2 border-t border-blue-100">
              <span className="font-mono font-extrabold text-sm text-blue-800">Total: {fmt(journal.total_debit)}</span>
            </div>
          </div>
        </div>

        {/* Credit Side */}
        <div>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500" /> Credits
          </h4>
          <div className="space-y-2">
            {creditLines.map(l => (
              <div key={l.line_id} className="flex items-center justify-between bg-emerald-50/50 border border-emerald-100 rounded-xl px-4 py-2.5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-700">{l.account_name || l.account_code}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {l.account_code} &middot; {l.product_type}{l.stage ? ` &middot; Stage ${l.stage}` : ''}
                  </p>
                </div>
                <span className="font-mono font-bold text-sm text-emerald-700">{fmt(l.credit)}</span>
              </div>
            ))}
            <div className="flex justify-end pt-2 border-t border-emerald-100">
              <span className="font-mono font-extrabold text-sm text-emerald-800">Total: {fmt(journal.total_credit)}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

function TrialBalanceView({ data }: { data: GLTrialBalanceRow[] }) {
  const totalDebit = data.reduce((s, r) => s + r.total_debit, 0);
  const totalCredit = data.reduce((s, r) => s + r.total_credit, 0);
  const balanced = Math.abs(totalDebit - totalCredit) < 0.01;

  if (data.length === 0) {
    return (
      <Card>
        <div className="text-center py-12 text-slate-400">
          <BarChart3 size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-semibold">No posted journals yet</p>
          <p className="text-xs mt-1">Post journal entries to see the trial balance</p>
        </div>
      </Card>
    );
  }

  return (
    <Card title="Trial Balance" subtitle="Aggregated balances from posted journal entries"
      icon={<BarChart3 size={16} />} accent="purple"
      action={<BalanceIndicator balanced={balanced} debit={totalDebit} credit={totalCredit} />}
    >
      <DataTable
        columns={[
          { key: 'account_code', label: 'Code', format: (v: string) => (
            <span className="font-mono text-xs font-semibold text-brand">{v}</span>
          )},
          { key: 'account_name', label: 'Account Name' },
          { key: 'account_type', label: 'Type', format: (v: string) => (
            <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${
              v === 'asset' ? 'bg-blue-50 text-blue-700' :
              v === 'contra-asset' ? 'bg-purple-50 text-purple-700' :
              v === 'expense' ? 'bg-red-50 text-red-700' :
              v === 'income' ? 'bg-emerald-50 text-emerald-700' :
              'bg-slate-50 text-slate-600'
            }`}>{v}</span>
          )},
          { key: 'total_debit', label: 'Debit', align: 'right', format: (v: number) => (
            <span className="font-mono font-semibold">{fmt(v)}</span>
          )},
          { key: 'total_credit', label: 'Credit', align: 'right', format: (v: number) => (
            <span className="font-mono font-semibold">{fmt(v)}</span>
          )},
          { key: 'balance', label: 'Balance', align: 'right', format: (v: number) => (
            <span className={`font-mono font-bold ${v >= 0 ? 'text-blue-700' : 'text-red-600'}`}>
              {v >= 0 ? '' : '('}{fmt(Math.abs(v))}{v >= 0 ? '' : ')'}
            </span>
          )},
        ]}
        data={data}
        exportName="gl_trial_balance"
        compact
      />

      {/* Totals Row */}
      <div className="mt-4 flex justify-end gap-8 bg-slate-800 text-white rounded-xl px-6 py-3 text-sm">
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider mr-3">Total Debits</span>
          <span className="font-mono font-extrabold">{fmt(totalDebit)}</span>
        </div>
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider mr-3">Total Credits</span>
          <span className="font-mono font-extrabold">{fmt(totalCredit)}</span>
        </div>
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider mr-3">Difference</span>
          <span className={`font-mono font-extrabold ${balanced ? 'text-emerald-400' : 'text-red-400'}`}>
            {fmt(Math.abs(totalDebit - totalCredit))}
          </span>
        </div>
      </div>
    </Card>
  );
}

function ChartOfAccountsView({ data }: { data: GLAccount[] }) {
  return (
    <Card title="Chart of Accounts" subtitle="Standard IFRS 9 ECL GL account structure"
      icon={<List size={16} />} accent="blue">
      <DataTable
        columns={[
          { key: 'account_code', label: 'Code', format: (v: string) => (
            <span className="font-mono text-xs font-bold text-brand">{v}</span>
          )},
          { key: 'account_name', label: 'Account Name', format: (v: string) => (
            <span className="font-semibold text-slate-700">{v}</span>
          )},
          { key: 'account_type', label: 'Type', format: (v: string) => (
            <span className={`inline-flex px-2.5 py-0.5 rounded-md text-xs font-semibold ${
              v === 'asset' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
              v === 'contra-asset' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
              v === 'expense' ? 'bg-red-50 text-red-700 border border-red-200' :
              v === 'income' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
              'bg-slate-50 text-slate-600 border border-slate-200'
            }`}>{v}</span>
          )},
          { key: 'parent_account', label: 'Parent', format: (v: string | null) => v || '—' },
          { key: 'is_ecl_related', label: 'ECL Related', align: 'center', format: (v: boolean) => (
            v ? <CheckCircle2 size={16} className="text-emerald-500 mx-auto" /> : <span className="text-slate-300">—</span>
          )},
        ]}
        data={data}
        exportName="gl_chart_of_accounts"
        compact
      />
    </Card>
  );
}
