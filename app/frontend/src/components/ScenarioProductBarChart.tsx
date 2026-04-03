import { useState, useMemo, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Cell } from 'recharts';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import ChartTooltip from './ChartTooltip';
import { fmtCurrency, formatProductName } from '../lib/format';
import { chartAxisProps, sortChartData } from '../lib/chartUtils';
import { config } from '../lib/config';
import { useChartTheme } from '../lib/chartTheme';
import { api } from '../lib/api';

interface Props {
  data: any[];
  scenarioColors: Record<string, string>;
  scenarioLabels?: Record<string, string>;
  height?: number;
}

type DrillLevel = 'products' | 'cohort';

const COHORT_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'];

export default function ScenarioProductBarChart({
  data,
  scenarioColors,
  scenarioLabels = {},
  height = 320,
}: Props) {
  const ct = useChartTheme();
  const [level, setLevel] = useState<DrillLevel>('products');
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [cohortData, setCohortData] = useState<any[]>([]);
  const [loadingCohort, setLoadingCohort] = useState(false);
  const [dimensions, setDimensions] = useState<{ key: string; label: string }[]>([]);
  const [activeDimension, setActiveDimension] = useState('risk_band');

  useEffect(() => {
    api.drillDownDimensions().then(setDimensions).catch(() => {});
  }, []);

  // Reset drill level when data changes
  useEffect(() => {
    setLevel('products');
    setSelectedProduct(null);
    setCohortData([]);
  }, [data]);

  const fetchCohort = useCallback(async (product: string, dim: string) => {
    setLoadingCohort(true);
    try {
      const result = await api.eclByCohort(product, dim);
      setCohortData(result);
    } catch {
      setCohortData([]);
    } finally {
      setLoadingCohort(false);
    }
  }, []);

  const handleBarClick = useCallback(async (rechartsData: any) => {
    if (level !== 'products') return;
    const entry = rechartsData?.payload || rechartsData || {};
    const product = entry._rawProduct || entry.product;
    if (!product) return;
    setSelectedProduct(product);
    setLevel('cohort');
    await fetchCohort(product, activeDimension);
  }, [level, activeDimension, fetchCohort]);

  const handleDimensionChange = useCallback(async (dim: string) => {
    setActiveDimension(dim);
    if (selectedProduct) {
      await fetchCohort(selectedProduct, dim);
    }
  }, [selectedProduct, fetchCohort]);

  const goBack = () => {
    setLevel('products');
    setSelectedProduct(null);
    setCohortData([]);
  };

  const sortedCohortData = useMemo(() => {
    return sortChartData(cohortData.map(d => ({
      ...d,
      name: d.cohort_id || d.name || 'Unknown',
    })));
  }, [cohortData]);

  if (!data.length) {
    return <p className="text-sm text-slate-400 py-8 text-center">No scenario comparison data available</p>;
  }

  const breadcrumb = level === 'products'
    ? ['All Products']
    : ['All Products', formatProductName(selectedProduct || '')];

  const useHorizontal = level === 'cohort' && sortedCohortData.length > 8;
  const dynamicHeight = useHorizontal ? Math.max(height, sortedCohortData.length * 36 + 40) : height;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          {breadcrumb.map((part, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={10} className="text-slate-300" />}
              <button onClick={() => { if (i === 0) goBack(); }}
                className={i < breadcrumb.length - 1 ? 'text-brand hover:underline cursor-pointer' : 'font-semibold text-slate-700 dark:text-slate-200'}>
                {part}
              </button>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {level === 'cohort' && dimensions.length > 1 && (
            <select
              value={activeDimension}
              onChange={e => handleDimensionChange(e.target.value)}
              aria-label="Drill-down dimension"
              className="text-[10px] px-2 py-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium focus:ring-1 focus:ring-brand/30 outline-none"
            >
              {dimensions.map(d => (
                <option key={d.key} value={d.key}>{d.label}</option>
              ))}
            </select>
          )}
          {level !== 'products' && (
            <button onClick={goBack} className="flex items-center gap-1 text-xs text-brand hover:underline">
              <ArrowLeft size={12} /> Back
            </button>
          )}
        </div>
      </div>

      {level === 'products' && (
        <p className="text-[10px] text-slate-400 mb-3">Click a product bar to drill down by dimension</p>
      )}

      {loadingCohort && (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-6 h-6 border-2 border-brand border-t-transparent rounded-full" />
        </div>
      )}

      {!loadingCohort && level === 'products' && (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} barGap={2} margin={{ bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis
              dataKey="product"
              tick={{ fontSize: chartAxisProps(data.length).fontSize, fill: ct.axisLight }}
              interval={0}
              angle={chartAxisProps(data.length).angle}
              textAnchor="end"
              height={chartAxisProps(data.length).height}
              tickMargin={12}
            />
            <YAxis
              tick={{ fontSize: 11, fill: ct.axisLight }}
              tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`}
            />
            <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
            <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
            {Object.entries(scenarioColors).map(([key, color]) => {
              const hasData = data.some((r: any) => r[key] !== undefined);
              if (!hasData) return null;
              return (
                <Bar
                  key={key}
                  dataKey={key}
                  name={scenarioLabels[key] || key.replace(/_/g, ' ')}
                  fill={color}
                  radius={[2, 2, 0, 0]}
                  cursor="pointer"
                  onClick={handleBarClick}
                />
              );
            })}
          </BarChart>
        </ResponsiveContainer>
      )}

      {!loadingCohort && level === 'cohort' && sortedCohortData.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <p className="text-sm font-semibold">No cohort data available</p>
          <p className="text-xs mt-1">Try selecting a different dimension above.</p>
          <button onClick={goBack} className="mt-3 text-xs text-brand font-semibold hover:underline flex items-center gap-1">
            <ArrowLeft size={12} /> Back to all products
          </button>
        </div>
      )}

      {!loadingCohort && level === 'cohort' && sortedCohortData.length > 0 && (
        <div style={{ height: dynamicHeight, overflow: 'hidden' }}>
          <ResponsiveContainer width="100%" height="100%">
            {useHorizontal ? (
              <BarChart data={sortedCohortData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ct.grid} />
                <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v) => fmtCurrency(v)} axisLine={false} tickLine={false} tickMargin={8} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} width={140} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={(v) => fmtCurrency(v)} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey="total_ecl" radius={[0, 8, 8, 0]} barSize={24}>
                  {sortedCohortData.map((_, i) => <Cell key={i} fill={COHORT_COLORS[i % COHORT_COLORS.length]} />)}
                </Bar>
              </BarChart>
            ) : (
              <BarChart data={sortedCohortData} margin={{ left: 10, right: 10, bottom: 40, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={ct.grid} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} interval={0} axisLine={false} tickLine={false} tickMargin={16} />
                <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v) => fmtCurrency(v)} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={(v) => fmtCurrency(v)} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey="total_ecl" radius={[8, 8, 0, 0]} barSize={48}>
                  {sortedCohortData.map((_, i) => <Cell key={i} fill={COHORT_COLORS[i % COHORT_COLORS.length]} />)}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
