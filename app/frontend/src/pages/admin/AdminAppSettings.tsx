import {
  Settings, Briefcase, Shield, BarChart3,
  AlertTriangle, Plus, Trash2, HelpCircle,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { inputCls, labelCls, CURRENCIES } from './types';
import type { AdminConfig, ScenarioRow } from './types';

function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex ml-1 cursor-help">
      <HelpCircle size={11} className="text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-400 transition" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 text-[10px] leading-tight bg-slate-800 text-white rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition pointer-events-none w-52 z-50 text-center">
        {text}
      </span>
    </span>
  );
}

export interface AdminAppSettingsProps {
  config: AdminConfig;
  onChange: (c: AdminConfig) => void;
}

export default function AdminAppSettings({ config, onChange }: AdminAppSettingsProps) {
  const { toast } = useToast();
  const settings = config.app_settings || {} as AdminConfig['app_settings'];
  const gov = settings.governance || {} as AdminConfig['app_settings']['governance'];

  const update = (field: string, value: any) => onChange({ ...config, app_settings: { ...settings, [field]: value } });
  const updateGov = (field: string, value: string | number) => onChange({ ...config, app_settings: { ...settings, governance: { ...gov, [field]: value } } });

  const handleCurrencyChange = (code: string) => {
    const cur = CURRENCIES.find(c => c.code === code);
    if (!cur) return;
    onChange({ ...config, app_settings: { ...settings, currency_code: cur.code, currency_symbol: cur.symbol, currency_locale: cur.locale } });
  };

  const updateScenario = (idx: number, field: keyof ScenarioRow, value: any) => {
    const scenarios = [...(settings.scenarios || [])];
    scenarios[idx] = { ...scenarios[idx], [field]: value };
    onChange({ ...config, app_settings: { ...settings, scenarios } });
  };

  const addScenario = () => {
    const key = `scenario_${(settings.scenarios || []).length + 1}`;
    const scenarios = [...(settings.scenarios || []), { key, name: 'New Scenario', weight: 0, pd_multiplier: 1.0, lgd_multiplier: 1.0, color: '#6366F1' }];
    onChange({ ...config, app_settings: { ...settings, scenarios } });
  };

  const removeScenario = (idx: number) => {
    if (!window.confirm(`Remove scenario "${(settings.scenarios || [])[idx].name}"?`)) return;
    onChange({ ...config, app_settings: { ...settings, scenarios: (settings.scenarios || []).filter((_, i) => i !== idx) } });
  };

  const normalizeWeights = () => {
    const total = (settings.scenarios || []).reduce((s: number, sc: ScenarioRow) => s + (sc.weight || 0), 0);
    if (total === 0) { toast('All weights are zero', 'error'); return; }
    const scenarios = (settings.scenarios || []).map((sc: ScenarioRow) => ({ ...sc, weight: Math.round((sc.weight / total) * 1000) / 1000 }));
    const diff = 1.0 - scenarios.reduce((s: number, sc: ScenarioRow) => s + sc.weight, 0);
    if (scenarios.length > 0) scenarios[0].weight = Math.round((scenarios[0].weight + diff) * 1000) / 1000;
    onChange({ ...config, app_settings: { ...settings, scenarios } });
    toast('Weights normalized to 100%', 'success');
  };

  const totalWeight = (settings.scenarios || []).reduce((s: number, sc: ScenarioRow) => s + (sc.weight || 0), 0);
  const weightValid = Math.abs(totalWeight - 1.0) < 0.005;

  return (
    <div className="space-y-4">
      <Card accent="brand" icon={<Briefcase size={16} />} title="Organization" subtitle="Bank / institution identity">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Organization Name</label>
            <input value={settings.organization_name} onChange={e => update('organization_name', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Legal Name</label>
            <input value={settings.organization_legal_name} onChange={e => update('organization_legal_name', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Country</label>
            <input value={settings.country} onChange={e => update('country', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Currency</label>
            <select value={settings.currency_code} onChange={e => handleCurrencyChange(e.target.value)} className={inputCls}>
              {CURRENCIES.map(c => <option key={c.code} value={c.code}>{c.code} — {c.label} ({c.symbol})</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>Logo URL <Tooltip text="Organization logo for reports" /></label>
            <div className="flex items-center gap-2">
              <input value={settings.logo_url || ''} onChange={e => update('logo_url', e.target.value)} placeholder="https://..." className={`${inputCls} flex-1`} />
              {settings.logo_url && <img src={settings.logo_url} alt="Logo" className="h-8 w-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-0.5" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
            </div>
          </div>
          <div>
            <label className={labelCls}>Reporting Period</label>
            <input value={settings.reporting_period || ''} onChange={e => update('reporting_period', e.target.value)} placeholder="e.g. Q4 2025" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Reporting Date</label>
            <input type="date" value={settings.reporting_date || ''} onChange={e => update('reporting_date', e.target.value)} className={inputCls} />
          </div>
        </div>
      </Card>

      <Card icon={<Shield size={16} />} title="Governance & Approvals" subtitle="Sign-off personnel and audit trail">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            ['cfo_name', 'CFO Name', 'cfo_title', 'CFO Title'],
            ['cro_name', 'CRO Name', 'cro_title', 'CRO Title'],
            ['head_credit_risk_name', 'Head of Credit Risk', 'head_credit_risk_title', 'Title'],
            ['model_validator_name', 'Model Validator', 'model_validator_title', 'Title'],
            ['external_auditor_firm', 'External Auditor Firm', 'external_auditor_partner', 'Partner'],
          ].map(([nameKey, nameLabel, titleKey, titleLabel]) => (
            <div key={nameKey} className="flex gap-3">
              <div className="flex-1">
                <label className={labelCls}>{nameLabel}</label>
                <input value={(gov as any)[nameKey] || ''} onChange={e => updateGov(nameKey, e.target.value)} className={inputCls} />
              </div>
              <div className="flex-1">
                <label className={labelCls}>{titleLabel}</label>
                <input value={(gov as any)[titleKey] || ''} onChange={e => updateGov(titleKey, e.target.value)} className={inputCls} />
              </div>
            </div>
          ))}
          <div>
            <label className={labelCls}>Board Committee</label>
            <input value={gov.board_committee} onChange={e => updateGov('board_committee', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Approval Workflow</label>
            <input value={gov.approval_workflow} onChange={e => updateGov('approval_workflow', e.target.value)} className={`${inputCls} font-mono text-xs`} />
          </div>
          <div>
            <label className={labelCls}>GL Reconciliation Tolerance (%)</label>
            <input type="number" step="0.01" min="0" max="10" value={gov.gl_reconciliation_tolerance_pct ?? 0.50} onChange={e => updateGov('gl_reconciliation_tolerance_pct', parseFloat(e.target.value) || 0.50)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>DQ Score Threshold (%)</label>
            <input type="number" step="1" min="0" max="100" value={gov.dq_score_threshold_pct ?? 90} onChange={e => updateGov('dq_score_threshold_pct', parseFloat(e.target.value) || 90)} className={inputCls} />
          </div>
        </div>
      </Card>

      <Card icon={<Settings size={16} />} title="Application" subtitle="App display settings">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>App Title</label>
            <input value={settings.app_title} onChange={e => update('app_title', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>App Subtitle</label>
            <input value={settings.app_subtitle} onChange={e => update('app_subtitle', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Framework</label>
            <select value={settings.framework_mode} onChange={e => {
              const mode = e.target.value;
              const fw = mode === 'ifrs9' ? 'IFRS 9' : mode === 'cecl' ? 'CECL' : 'IFRS 17';
              update('framework_mode', mode);
              update('framework', fw);
            }} className={inputCls}>
              <option value="ifrs9">IFRS 9 — Expected Credit Loss</option>
              <option value="cecl">CECL — Current Expected Credit Loss</option>
              <option value="ifrs17">IFRS 17 — Insurance Contracts</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>Model Version</label>
            <input value={settings.model_version} onChange={e => update('model_version', e.target.value)} className={inputCls} />
          </div>
        </div>
      </Card>

      <Card accent="purple" icon={<BarChart3 size={16} />} title="Scenario Weights" subtitle="Probability-weighted scenarios for ECL">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-700 dark:bg-slate-700/50">
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase w-8">Color</th>
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase">Key</th>
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase">Name</th>
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase">Weight</th>
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase">PD Mult.</th>
                <th className="text-left py-2 px-2 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase">LGD Mult.</th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {(settings.scenarios || []).map((sc, i) => (
                <tr key={sc.key} className="border-b border-slate-50 dark:border-slate-800 hover:bg-brand/3 transition">
                  <td className="py-1.5 px-2"><input type="color" value={sc.color} onChange={e => updateScenario(i, 'color', e.target.value)} className="w-6 h-6 rounded cursor-pointer border-0" /></td>
                  <td className="py-1.5 px-2"><span className="text-xs font-mono text-slate-500 dark:text-slate-400">{sc.key}</span></td>
                  <td className="py-1.5 px-2"><input value={sc.name} onChange={e => updateScenario(i, 'name', e.target.value)} className="w-full px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-brand/30 outline-none" /></td>
                  <td className="py-1.5 px-2"><input type="number" step={0.01} min={0} max={1} value={sc.weight} onChange={e => updateScenario(i, 'weight', parseFloat(e.target.value) || 0)} className="w-20 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" /></td>
                  <td className="py-1.5 px-2"><input type="number" step={0.05} min={0} value={sc.pd_multiplier} onChange={e => updateScenario(i, 'pd_multiplier', parseFloat(e.target.value) || 0)} className="w-20 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" /></td>
                  <td className="py-1.5 px-2"><input type="number" step={0.05} min={0} value={sc.lgd_multiplier} onChange={e => updateScenario(i, 'lgd_multiplier', parseFloat(e.target.value) || 0)} className="w-20 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" /></td>
                  <td className="py-1.5 px-2"><button onClick={() => removeScenario(i)} aria-label={`Remove scenario ${sc.name}`} className="text-slate-300 hover:text-red-500 transition focus-visible:ring-2 focus-visible:ring-brand rounded"><Trash2 size={14} /></button></td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-slate-200 dark:border-slate-700">
                <td colSpan={3} className="py-2 px-2 text-xs font-bold text-slate-600 dark:text-slate-300">Total Weight</td>
                <td className="py-2 px-2"><span className={`text-xs font-bold font-mono ${weightValid ? 'text-emerald-600' : 'text-red-600'}`}>{(totalWeight * 100).toFixed(1)}%</span></td>
                <td colSpan={3} className="py-2 px-2">
                  {!weightValid && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-red-500 flex items-center gap-1"><AlertTriangle size={12} /> Must sum to 100%</span>
                      <button onClick={normalizeWeights} className="text-xs text-brand font-semibold transition hover:text-brand-dark">Auto-fix</button>
                    </div>
                  )}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        <button onClick={addScenario} className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-brand hover:text-brand-dark transition">
          <Plus size={14} /> Add Scenario
        </button>
      </Card>
    </div>
  );
}
