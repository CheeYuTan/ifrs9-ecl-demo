import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, ChevronRight, Check, X, RefreshCw,
} from 'lucide-react';
import { useToast } from '../../components/Toast';
import { api } from '../../lib/api';
import { WIZARD_STEPS } from './types';
import type { MappingStatus, SourceColumn, WizardStep } from './types';
import StatusCards from './StatusCards';
import SourceBrowser from './SourceBrowser';
import ColumnMapper from './ColumnMapper';
import ValidationStep from './ValidationStep';
import ApplyStep from './ApplyStep';

// ── Main Component ─────────────────────────────────────────────────────────

export default function DataMapping() {
  const { toast } = useToast();

  // Status
  const [status, setStatus] = useState<Record<string, MappingStatus>>({});
  const [loadingStatus, setLoadingStatus] = useState(true);

  // Wizard state
  const [wizardOpen, setWizardOpen] = useState(false);
  const [step, setStep] = useState<WizardStep>('select-table');
  const [selectedTableKey, setSelectedTableKey] = useState<string>('');

  // Source browsing
  const [catalogs, setCatalogs] = useState<any[]>([]);
  const [selectedCatalog, setSelectedCatalog] = useState('');
  const [schemas, setSchemas] = useState<any[]>([]);
  const [selectedSchema, setSelectedSchema] = useState('');
  const [tables, setTables] = useState<any[]>([]);
  const [selectedSourceTable, setSelectedSourceTable] = useState('');
  const [loadingBrowse, setLoadingBrowse] = useState(false);

  // Source columns & preview
  const [sourceColumns, setSourceColumns] = useState<SourceColumn[]>([]);
  const [previewData, setPreviewData] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  // Column mappings
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [columnFilter, setColumnFilter] = useState('');

  // Validation
  const [validationResult, setValidationResult] = useState<any>(null);
  const [validating, setValidating] = useState(false);

  // Apply
  const [applying, setApplying] = useState(false);
  const [applyResult, setApplyResult] = useState<any>(null);
  const [applyMode, setApplyMode] = useState<'overwrite' | 'append'>('overwrite');

  // ── Load status ────────────────────────────────────────────────────────

  const loadStatus = useCallback(async () => {
    setLoadingStatus(true);
    try {
      const data = await api.dataMappingStatus();
      setStatus(data);
    } catch (e: any) {
      toast(`Failed to load status: ${e.message}`, 'error');
    } finally {
      setLoadingStatus(false);
    }
  }, [toast]);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  // ── Browse catalogs ────────────────────────────────────────────────────

  const loadCatalogs = useCallback(async () => {
    setLoadingBrowse(true);
    try {
      const data = await api.dataMappingCatalogs();
      setCatalogs(data);
    } catch {
      toast('Failed to load catalogs', 'error');
    } finally {
      setLoadingBrowse(false);
    }
  }, [toast]);

  const loadSchemas = useCallback(async (catalog: string) => {
    setLoadingBrowse(true);
    try {
      const data = await api.dataMappingSchemas(catalog);
      setSchemas(data);
    } catch {
      toast('Failed to load schemas', 'error');
    } finally {
      setLoadingBrowse(false);
    }
  }, [toast]);

  const loadTables = useCallback(async (catalog: string, schema: string) => {
    setLoadingBrowse(true);
    try {
      const data = await api.dataMappingTables(catalog, schema);
      setTables(data);
    } catch {
      toast('Failed to load tables', 'error');
    } finally {
      setLoadingBrowse(false);
    }
  }, [toast]);

  // ── Preview ────────────────────────────────────────────────────────────

  const loadPreview = useCallback(async (sourceTable: string) => {
    setLoadingPreview(true);
    try {
      const data = await api.dataMappingPreview(sourceTable, 10);
      setPreviewData(data);
      setSourceColumns(data.columns || []);
      setShowPreview(true);
    } catch (e: any) {
      toast(`Preview failed: ${e.message}`, 'error');
    } finally {
      setLoadingPreview(false);
    }
  }, [toast]);

  // ── Auto-suggest ───────────────────────────────────────────────────────

  const autoSuggest = useCallback(async () => {
    if (!selectedTableKey || !selectedSourceTable) return;
    try {
      const data = await api.dataMappingSuggest(selectedTableKey, selectedSourceTable);
      const newMappings: Record<string, string> = {};
      for (const [eclCol, info] of Object.entries(data.suggestions) as [string, any][]) {
        if (info.source_column) newMappings[eclCol] = info.source_column;
      }
      setMappings(newMappings);
      toast(`Auto-mapped ${Object.keys(newMappings).length} columns`, 'success');
    } catch (e: any) {
      toast(`Auto-suggest failed: ${e.message}`, 'error');
    }
  }, [selectedTableKey, selectedSourceTable, toast]);

  // ── Validate ───────────────────────────────────────────────────────────

  const runValidation = useCallback(async () => {
    if (!selectedTableKey || !selectedSourceTable) return;
    setValidating(true);
    try {
      const result = await api.dataMappingValidate(selectedTableKey, selectedSourceTable, mappings);
      setValidationResult(result);
      if (result.valid && (!result.warnings || result.warnings.length === 0)) {
        toast('Validation passed', 'success');
      } else if (result.valid) {
        toast(`Valid with ${result.warnings.length} warning(s)`, 'info');
      } else {
        toast(`${result.errors.length} error(s) found`, 'error');
      }
    } catch (e: any) {
      toast(`Validation failed: ${e.message}`, 'error');
    } finally {
      setValidating(false);
    }
  }, [selectedTableKey, selectedSourceTable, mappings, toast]);

  // ── Apply ──────────────────────────────────────────────────────────────

  const runApply = useCallback(async () => {
    if (!selectedTableKey || !selectedSourceTable) return;
    setApplying(true);
    setApplyResult(null);
    try {
      const result = await api.dataMappingApply(selectedTableKey, selectedSourceTable, mappings, applyMode);
      setApplyResult(result);
      if (result.status === 'success') {
        toast(`Ingested ${result.rows_written} rows`, 'success');
        loadStatus(); // refresh status cards
      } else {
        toast(result.message || 'Apply failed', 'error');
      }
    } catch (e: any) {
      toast(`Apply failed: ${e.message}`, 'error');
    } finally {
      setApplying(false);
    }
  }, [selectedTableKey, selectedSourceTable, mappings, applyMode, toast, loadStatus]);

  // ── ECL table config for column defs ───────────────────────────────────

  const [eclConfig, setEclConfig] = useState<any>(null);
  useEffect(() => {
    api.adminConfig().then(setEclConfig).catch(() => {});
  }, []);

  const eclTableDef = useMemo(() => {
    if (!eclConfig || !selectedTableKey) return null;
    return eclConfig.data_sources?.tables?.[selectedTableKey] || null;
  }, [eclConfig, selectedTableKey]);

  const allEclColumns = useMemo(() => {
    if (!eclTableDef) return [];
    const mandatory = (eclTableDef.mandatory_columns || []).map((c: any) => ({ ...c, is_mandatory: true }));
    const optional = (eclTableDef.optional_columns || []).map((c: any) => ({ ...c, is_mandatory: false }));
    return [...mandatory, ...optional];
  }, [eclTableDef]);

  const filteredEclColumns = useMemo(() => {
    if (!columnFilter) return allEclColumns;
    const q = columnFilter.toLowerCase();
    return allEclColumns.filter((c: any) =>
      c.name.toLowerCase().includes(q) ||
      (c.description || '').toLowerCase().includes(q) ||
      (mappings[c.name] || '').toLowerCase().includes(q)
    );
  }, [allEclColumns, columnFilter, mappings]);

  // ── Source column names for dropdown ────────────────────────────────────

  const sourceColNames = useMemo(() => sourceColumns.map(c => c.name), [sourceColumns]);

  // ── Wizard helpers ─────────────────────────────────────────────────────

  const startWizard = (tableKey: string) => {
    setSelectedTableKey(tableKey);
    setStep('select-source');
    setSelectedCatalog('');
    setSelectedSchema('');
    setSelectedSourceTable('');
    setSourceColumns([]);
    setPreviewData(null);
    setShowPreview(false);
    setMappings({});
    setValidationResult(null);
    setApplyResult(null);
    setColumnFilter('');
    setWizardOpen(true);
    loadCatalogs();
  };

  const handleSelectCatalog = useCallback((catalog: string) => {
    setSelectedCatalog(catalog);
    setSelectedSchema('');
    setSelectedSourceTable('');
    setSchemas([]);
    setTables([]);
    if (catalog) loadSchemas(catalog);
  }, [loadSchemas]);

  const handleSelectSchema = useCallback((schema: string) => {
    setSelectedSchema(schema);
    setSelectedSourceTable('');
    setTables([]);
    if (schema && selectedCatalog) loadTables(selectedCatalog, schema);
  }, [selectedCatalog, loadTables]);

  const handleContinueToMapColumns = useCallback(() => {
    setStep('map-columns');
    loadPreview(selectedSourceTable);
  }, [selectedSourceTable, loadPreview]);

  const handleValidateAndAdvance = useCallback(() => {
    runValidation();
    setStep('validate');
  }, [runValidation]);

  const handleAdvanceToApply = useCallback(() => {
    setStep('apply');
  }, []);

  const stepIndex = WIZARD_STEPS.findIndex(s => s.key === step);

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
            <Upload size={24} className="text-brand" />
            Data Mapping
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Map your source data from Unity Catalog to the ECL schema tables
          </p>
        </div>
        <button onClick={loadStatus} disabled={loadingStatus}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-white/10 text-xs font-semibold text-slate-500 dark:text-white/60 hover:text-slate-800 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/5 transition">
          <RefreshCw size={14} className={loadingStatus ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Status Cards */}
      <StatusCards status={status} loadingStatus={loadingStatus} onStartWizard={startWizard} />

      {/* Wizard Modal */}
      <AnimatePresence>
        {wizardOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
            onClick={(e) => { if (e.target === e.currentTarget) setWizardOpen(false); }}>
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-5xl max-h-[90vh] overflow-hidden rounded-3xl bg-white dark:bg-[#141927] border border-slate-200 dark:border-white/10 shadow-2xl flex flex-col">

              {/* Wizard Header */}
              <div className="px-6 py-4 border-b border-slate-200 dark:border-white/10 flex items-center justify-between flex-shrink-0">
                <div>
                  <h2 className="text-lg font-bold text-slate-800 dark:text-white">
                    Map Data: {selectedTableKey.replace(/_/g, ' ')}
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {eclTableDef?.description || ''}
                  </p>
                </div>
                <button onClick={() => setWizardOpen(false)} className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 text-slate-400 hover:text-slate-800 dark:hover:text-white transition">
                  <X size={18} />
                </button>
              </div>

              {/* Stepper */}
              <div className="px-6 py-3 border-b border-slate-100 dark:border-white/5 flex items-center gap-1 flex-shrink-0">
                {WIZARD_STEPS.map((ws, i) => (
                  <div key={ws.key} className="flex items-center">
                    <button onClick={() => { if (i <= stepIndex) setStep(ws.key); }}
                      disabled={i > stepIndex}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        step === ws.key ? 'bg-brand/10 text-brand' :
                        i < stepIndex ? 'text-emerald-400 hover:bg-slate-100 dark:hover:bg-white/5' :
                        'text-slate-500 cursor-not-allowed'
                      }`}>
                      {i < stepIndex ? <Check size={12} /> : <span className="w-4 h-4 rounded-full border border-current flex items-center justify-center text-[9px]">{i + 1}</span>}
                      <span className="hidden sm:inline">{ws.label}</span>
                      <span className="sm:hidden">{ws.short}</span>
                    </button>
                    {i < WIZARD_STEPS.length - 1 && <ChevronRight size={12} className="text-slate-400 dark:text-slate-500 mx-0.5" />}
                  </div>
                ))}
              </div>

              {/* Wizard Body */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* Step: Select Source */}
                {step === 'select-source' && (
                  <SourceBrowser
                    catalogs={catalogs}
                    selectedCatalog={selectedCatalog}
                    schemas={schemas}
                    selectedSchema={selectedSchema}
                    tables={tables}
                    selectedSourceTable={selectedSourceTable}
                    loadingBrowse={loadingBrowse}
                    loadingPreview={loadingPreview}
                    showPreview={showPreview}
                    previewData={previewData}
                    onSelectCatalog={handleSelectCatalog}
                    onSelectSchema={handleSelectSchema}
                    onSelectSourceTable={setSelectedSourceTable}
                    onLoadPreview={loadPreview}
                    onContinueToMapColumns={handleContinueToMapColumns}
                  />
                )}

                {/* Step: Map Columns */}
                {step === 'map-columns' && (
                  <ColumnMapper
                    mappings={mappings}
                    allEclColumns={allEclColumns}
                    filteredEclColumns={filteredEclColumns}
                    columnFilter={columnFilter}
                    sourceColNames={sourceColNames}
                    onSetMappings={setMappings}
                    onSetColumnFilter={setColumnFilter}
                    onAutoSuggest={autoSuggest}
                    onValidateAndAdvance={handleValidateAndAdvance}
                  />
                )}

                {/* Step: Validate */}
                {step === 'validate' && (
                  <ValidationStep
                    validationResult={validationResult}
                    validating={validating}
                    onRunValidation={runValidation}
                    onAdvanceToApply={handleAdvanceToApply}
                  />
                )}

                {/* Step: Apply */}
                {step === 'apply' && (
                  <ApplyStep
                    selectedSourceTable={selectedSourceTable}
                    selectedTableKey={selectedTableKey}
                    mappings={mappings}
                    applyMode={applyMode}
                    applying={applying}
                    applyResult={applyResult}
                    onSetApplyMode={setApplyMode}
                    onRunApply={runApply}
                  />
                )}
              </div>

              {/* Wizard Footer */}
              <div className="px-6 py-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between flex-shrink-0">
                <button
                  onClick={() => {
                    const idx = WIZARD_STEPS.findIndex(s => s.key === step);
                    if (idx > 0) setStep(WIZARD_STEPS[idx - 1].key);
                    else setWizardOpen(false);
                  }}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 dark:bg-white/5 text-xs font-semibold text-slate-700 dark:text-white hover:bg-slate-200 dark:hover:bg-white/10 transition">
                  Back
                </button>
                <div className="text-[10px] text-slate-500">
                  Step {stepIndex + 1} of {WIZARD_STEPS.length}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
