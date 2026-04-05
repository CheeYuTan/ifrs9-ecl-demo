import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Download, CheckCircle2, Clock, Lock, AlertTriangle,
  BarChart3, Layers, TrendingUp, PieChart, RefreshCw,
  ChevronRight, Eye, FileSpreadsheet, Loader2,
} from 'lucide-react';
import Card from '../components/Card';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api, type Project } from '../lib/api';

const fmt = (v: number) => v?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '0.00';

const REPORT_TYPES: { key: string; label: string; icon: typeof FileText; color: string; description: string }[] = [
  { key: 'ifrs7_disclosure', label: 'IFRS 7 Disclosure', icon: FileText, color: 'blue', description: 'Comprehensive IFRS 7.35F-36 disclosure package' },
  { key: 'ecl_movement', label: 'ECL Movement', icon: TrendingUp, color: 'green', description: 'Period-over-period ECL waterfall analysis' },
  { key: 'stage_migration', label: 'Stage Migration', icon: Layers, color: 'purple', description: 'Stage transition matrix and rates' },
  { key: 'sensitivity_analysis', label: 'Sensitivity Analysis', icon: BarChart3, color: 'amber', description: 'PD/LGD sensitivity and scenario analysis' },
  { key: 'concentration_risk', label: 'Concentration Risk', icon: PieChart, color: 'red', description: 'Product, segment, and single-name concentration' },
];

const STATUS_STYLES: Record<string, { bg: string; icon: typeof CheckCircle2; label: string }> = {
  draft: { bg: 'bg-amber-50 text-amber-700 border-amber-200', icon: Clock, label: 'Draft' },
  final: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: Lock, label: 'Final' },
  submitted: { bg: 'bg-blue-50 text-blue-700 border-blue-200', icon: CheckCircle2, label: 'Submitted' },
};

function ReportStatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.draft;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${s.bg}`}>
      <Icon size={12} /> {s.label}
    </span>
  );
}

function ReportTypeBadge({ type }: { type: string }) {
  const rt = REPORT_TYPES.find(r => r.key === type);
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    red: 'bg-red-50 text-red-700 border-red-200',
  };
  const color = colors[rt?.color || 'blue'] || colors.blue;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${color}`}>
      {rt?.label || type}
    </span>
  );
}

function SectionTable({ title, data }: { title: string; data: any[] }) {
  if (!data || data.length === 0) return null;
  const cols = Object.keys(data[0]);
  const columns = cols.map(k => ({
    key: k,
    label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    align: (typeof data[0][k] === 'number' ? 'right' : 'left') as 'left' | 'right',
    format: (v: any) => {
      if (v == null) return '—';
      if (typeof v === 'number') {
        if (Math.abs(v) >= 1000) return fmt(v);
        if (Math.abs(v) < 1 && v !== 0) return v.toFixed(4);
        return v.toLocaleString();
      }
      return String(v);
    },
  }));

  return (
    <Card title={title} accent="brand" icon={<FileSpreadsheet size={16} />}>
      <DataTable columns={columns} data={data} compact exportName={title.replace(/\s+/g, '_')} />
    </Card>
  );
}

type View = 'dashboard' | 'viewer';

export default function RegulatoryReports({ project }: { project: Project | null }) {
  const [view, setView] = useState<View>('dashboard');
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');

  const projectId = project?.project_id || '';

  const loadReports = useCallback(async () => {
    try {
      const data = await api.listReports(projectId || undefined, filterType || undefined);
      setReports(data);
    } catch (e: any) {
      setError(e.message);
    }
  }, [projectId, filterType]);

  useEffect(() => {
    setLoading(true);
    loadReports().finally(() => setLoading(false));
  }, [loadReports]);

  const handleGenerate = async (reportType: string) => {
    if (!projectId) {
      setError('No project selected');
      return;
    }
    setGenerating(reportType);
    setError(null);
    try {
      await api.generateReport(projectId, reportType, 'Credit Risk Analyst');
      await loadReports();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(null);
    }
  };

  const handleViewReport = async (reportId: string) => {
    setLoading(true);
    setError(null);
    try {
      const report = await api.getReport(reportId);
      setSelectedReport(report);
      setView('viewer');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async (reportId: string) => {
    try {
      await api.finalizeReport(reportId);
      await loadReports();
      if (selectedReport?.report_id === reportId) {
        const updated = await api.getReport(reportId);
        setSelectedReport(updated);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleExport = async (reportId: string) => {
    try {
      const blob = await api.exportReportCsv(reportId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const totalReports = reports.length;
  const draftCount = reports.filter(r => r.status === 'draft').length;
  const finalCount = reports.filter(r => r.status === 'final').length;
  const submittedCount = reports.filter(r => r.status === 'submitted').length;

  if (view === 'viewer' && selectedReport) {
    return <ReportViewer report={selectedReport} onBack={() => setView('dashboard')} onFinalize={handleFinalize} onExport={handleExport} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regulatory Reports"
        subtitle="IFRS 7 disclosure packages and regulatory report generation"
      >
        <button onClick={loadReports} className="btn-secondary text-xs">
          <RefreshCw size={13} /> Refresh
        </button>
      </PageHeader>

      {error && (
        <ErrorDisplay title="Report operation failed" message={error} technicalDetails={error}
          onRetry={loadReports} onDismiss={() => setError(null)} />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard title="Total Reports" value={String(totalReports)} icon={<FileText size={20} />} color="blue" />
        <KpiCard title="Draft" value={String(draftCount)} icon={<Clock size={20} />} color="amber" />
        <KpiCard title="Final" value={String(finalCount)} icon={<Lock size={20} />} color="green" />
        <KpiCard title="Submitted" value={String(submittedCount)} icon={<CheckCircle2 size={20} />} color="purple" />
      </div>

      {/* Generate Reports */}
      <Card title="Generate Reports" subtitle="Select a report type to generate from current project data" accent="brand" icon={<FileSpreadsheet size={16} />}>
        {!projectId && (
          <p className="text-sm text-amber-600 mb-4 flex items-center gap-2">
            <AlertTriangle size={14} /> Select a project first to generate reports
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {REPORT_TYPES.map(rt => {
            const Icon = rt.icon;
            const isGenerating = generating === rt.key;
            const colorMap: Record<string, string> = {
              blue: 'from-blue-500 to-blue-600',
              green: 'from-emerald-500 to-emerald-600',
              purple: 'from-purple-500 to-purple-600',
              amber: 'from-amber-500 to-amber-600',
              red: 'from-red-500 to-red-600',
            };
            const bgMap: Record<string, string> = {
              blue: 'bg-blue-500/10 text-blue-600',
              green: 'bg-emerald-500/10 text-emerald-600',
              purple: 'bg-purple-500/10 text-purple-600',
              amber: 'bg-amber-500/10 text-amber-600',
              red: 'bg-red-500/10 text-red-600',
            };
            return (
              <motion.button
                key={rt.key}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleGenerate(rt.key)}
                disabled={!projectId || !!generating}
                className={`relative text-left p-5 rounded-2xl border border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800/80 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed group`}
              >
                <div className={`absolute top-0 left-0 right-0 h-[2px] rounded-t-2xl bg-gradient-to-r ${colorMap[rt.color]}`} />
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-xl ${bgMap[rt.color]} flex items-center justify-center flex-shrink-0`}>
                    {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <Icon size={18} />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{rt.label}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-300 mt-1">{rt.description}</p>
                  </div>
                </div>
                <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-slate-500 dark:text-slate-300 group-hover:text-brand transition-colors">
                  {isGenerating ? 'Generating...' : 'Generate'} <ChevronRight size={12} />
                </div>
              </motion.button>
            );
          })}
        </div>
      </Card>

      {/* Report List */}
      <Card title="Generated Reports" subtitle="Click a report to view its contents" accent="blue" icon={<FileText size={16} />}
        action={
          <select value={filterType} onChange={e => setFilterType(e.target.value)}
            className="form-input text-xs py-1.5 px-3 w-48">
            <option value="">All Types</option>
            {REPORT_TYPES.map(rt => <option key={rt.key} value={rt.key}>{rt.label}</option>)}
          </select>
        }>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand" />
          </div>
        ) : reports.length === 0 ? (
          <EmptyState
            icon={<FileText size={48} />}
            title="No reports generated"
            description="Generate an IFRS 7 disclosure from a completed project."
          />
        ) : (
          <DataTable
            columns={[
              { key: 'report_id', label: 'Report ID', format: (v: string) => <span className="font-mono text-xs">{v}</span> },
              { key: 'report_type', label: 'Type', format: (v: string) => <ReportTypeBadge type={v} /> },
              { key: 'report_date', label: 'Report Date' },
              { key: 'status', label: 'Status', format: (v: string) => <ReportStatusBadge status={v} /> },
              { key: 'generated_by', label: 'Generated By' },
              { key: 'created_at', label: 'Created', format: (v: string) => v ? new Date(v).toLocaleString() : '—' },
              {
                key: '_actions', label: 'Actions',
                format: (_: any, row: any) => (
                  <div className="flex items-center gap-2">
                    <button onClick={(e) => { e.stopPropagation(); handleViewReport(row.report_id); }}
                      className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 transition" title="View">
                      <Eye size={14} />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); handleExport(row.report_id); }}
                      className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600 transition" title="Export CSV">
                      <Download size={14} />
                    </button>
                    {row.status === 'draft' && (
                      <button onClick={(e) => { e.stopPropagation(); handleFinalize(row.report_id); }}
                        className="p-1.5 rounded-lg hover:bg-purple-50 text-purple-600 transition" title="Finalize">
                        <Lock size={14} />
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
            data={reports}
            onRowClick={(row) => handleViewReport(row.report_id)}
            compact
            exportName="regulatory_reports"
          />
        )}
      </Card>
    </div>
  );
}


function ReportViewer({ report, onBack, onFinalize, onExport }: {
  report: any;
  onBack: () => void;
  onFinalize: (id: string) => void;
  onExport: (id: string) => void;
}) {
  let rd: any = {};
  try {
    rd = typeof report.report_data === 'string' ? JSON.parse(report.report_data) : (report.report_data || {});
  } catch {
    rd = {};
  }
  const sections = rd.sections || {};
  const sectionKeys = Object.keys(sections);

  const [activeSection, setActiveSection] = useState(sectionKeys[0] || '');

  const currentSection = sections[activeSection];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="btn-secondary text-xs">
            &larr; Back to Reports
          </button>
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
              <ReportTypeBadge type={report.report_type} />
              <ReportStatusBadge status={report.status} />
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-300 mt-1 font-mono">{report.report_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => onExport(report.report_id)} className="btn-secondary text-xs">
            <Download size={13} /> Export CSV
          </button>
          {report.status === 'draft' && (
            <button onClick={() => onFinalize(report.report_id)}
              className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl shadow-lg hover:opacity-80 transition">
              <Lock size={13} /> Finalize Report
            </button>
          )}
        </div>
      </div>

      {/* Report metadata */}
      <Card>
        <div className="grid grid-cols-4 gap-6 text-sm">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-300 mb-1">Report Date</p>
            <p className="font-semibold text-slate-700 dark:text-slate-200">{report.report_date || rd.report_date}</p>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-300 mb-1">Project</p>
            <p className="font-semibold text-slate-700 dark:text-slate-200">{report.project_id}</p>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-300 mb-1">Generated By</p>
            <p className="font-semibold text-slate-700 dark:text-slate-200">{report.generated_by}</p>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-300 mb-1">Generated At</p>
            <p className="font-semibold text-slate-700 dark:text-slate-200">{rd.generated_at ? new Date(rd.generated_at).toLocaleString() : '—'}</p>
          </div>
        </div>
      </Card>

      {/* Section tabs */}
      {sectionKeys.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {sectionKeys.map(key => {
            const section = sections[key];
            const isActive = key === activeSection;
            return (
              <button
                key={key}
                onClick={() => setActiveSection(key)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'gradient-brand text-white shadow-lg'
                    : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {section?.title || key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                {section?.data?.length > 0 && (
                  <span className={`ml-2 px-1.5 py-0.5 rounded-full text-[11px] ${isActive ? 'bg-white/20' : 'bg-slate-100 dark:bg-slate-700'}`}>
                    {section.data.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Section content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeSection} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
          {currentSection ? (
            currentSection.error ? (
              <Card>
                <div className="flex items-center gap-3 text-amber-600 text-sm">
                  <AlertTriangle size={16} />
                  <span>Data unavailable: {currentSection.error}</span>
                </div>
              </Card>
            ) : currentSection.data?.length > 0 ? (
              <SectionTable title={currentSection.title} data={currentSection.data} />
            ) : (
              <Card>
                <div className="text-center py-8 text-slate-500 dark:text-slate-300">
                  <FileText size={24} className="mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No data available for this section</p>
                </div>
              </Card>
            )
          ) : (
            <Card>
              <p className="text-sm text-slate-500 dark:text-slate-300 text-center py-8">Select a section to view</p>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
