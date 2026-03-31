import { useState, useMemo, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import ChartTooltip from './ChartTooltip';
import { formatProductName } from '../lib/format';
import { api } from '../lib/api';
import { sortChartData } from '../lib/chartUtils';
import { useChartTheme } from '../lib/chartTheme';

type DrillLevel = 'total' | 'product';

interface DrillDownData {
  totalData: any[];
  productData: Record<string, any[]>;
  cohortData: Record<string, any[]>;
}

interface Props {
  data: DrillDownData;
  dataKey: string;
  nameKey?: string;
  title: string;
  formatValue?: (v: number) => string;
  height?: number;
  colors?: string[];
  fetchByDimension?: (product: string, dimension: string) => Promise<any[]>;
}

const DEFAULT_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'];

export default function DrillDownChart({
  data,
  dataKey,
  nameKey = 'name',
  title,
  formatValue = (v) => v.toLocaleString(),
  height = 340,
  colors = DEFAULT_COLORS,
  fetchByDimension,
}: Props) {
  const ct = useChartTheme();
  const [level, setLevel] = useState<DrillLevel>('total');
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState<{ key: string; label: string }[]>([]);
  const [activeDimension, setActiveDimension] = useState('risk_band');
  const [dimensionData, setDimensionData] = useState<any[]>([]);
  const [loadingDimension, setLoadingDimension] = useState(false);

  useEffect(() => {
    api.drillDownDimensions().then(setDimensions).catch(() => {});
  }, []);

  const fetchDimensionData = useCallback(async (product: string, dim: string) => {
    setLoadingDimension(true);
    try {
      if (fetchByDimension) {
        const result = await fetchByDimension(product, dim);
        setDimensionData(result);
      } else {
        const fallback = data.productData[product] || [];
        setDimensionData(fallback);
      }
    } catch {
      setDimensionData(data.productData[product] || []);
    } finally {
      setLoadingDimension(false);
    }
  }, [fetchByDimension, data.productData]);

  const chartData = useMemo(() => {
    if (level === 'total') {
      return sortChartData(data.totalData.map(d => ({
        ...d,
        name: d[nameKey] ? formatProductName(d[nameKey]) : d.product_type ? formatProductName(d.product_type) : 'Unknown',
      })));
    }
    if (level === 'product' && selectedProduct) {
      return sortChartData(dimensionData.map(d => ({
        ...d,
        name: d.cohort_id || d[nameKey] || 'Unknown',
      })));
    }
    return [];
  }, [level, selectedProduct, data, nameKey, dimensionData]);

  const useHorizontal = chartData.length > 8;

  const breadcrumb = useMemo(() => {
    const parts = ['All Products'];
    if (level === 'product' && selectedProduct) parts.push(formatProductName(selectedProduct));
    return parts;
  }, [level, selectedProduct]);

  const handleBarClick = useCallback(async (rechartsData: any, idx: number) => {
    if (level !== 'total') return;
    const entry = rechartsData?.payload || rechartsData || chartData[idx] || {};
    const clickedName = entry.name || entry.product_type || entry[nameKey];
    if (!clickedName) return;
    const rawProduct = entry.product_type
      || data.totalData.find(d =>
        d.product_type === clickedName
        || formatProductName(d.product_type || '') === clickedName
        || d[nameKey] === clickedName
      )?.product_type
      || clickedName;
    setSelectedProduct(rawProduct);
    setLevel('product');
    await fetchDimensionData(rawProduct, activeDimension);
  }, [level, chartData, nameKey, data.totalData, activeDimension, fetchDimensionData]);

  const handleDimensionChange = useCallback(async (dim: string) => {
    setActiveDimension(dim);
    if (selectedProduct) {
      await fetchDimensionData(selectedProduct, dim);
    }
  }, [selectedProduct, fetchDimensionData]);

  const goBack = () => {
    setLevel('total');
    setSelectedProduct(null);
    setDimensionData([]);
  };

  const dynamicHeight = useHorizontal ? Math.max(height, chartData.length * 36 + 40) : height;

  return (
    <div role="figure" aria-label={title}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          {breadcrumb.map((part, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={10} className="text-slate-300" />}
              <button onClick={() => { if (i === 0) goBack(); }}
                className={i < breadcrumb.length - 1 ? 'text-brand hover:underline cursor-pointer' : 'font-semibold text-slate-700'}>
                {part}
              </button>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {level === 'product' && dimensions.length > 1 && (
            <select
              value={activeDimension}
              onChange={e => handleDimensionChange(e.target.value)}
              aria-label="Drill-down dimension"
              className="text-[10px] px-2 py-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 font-medium focus:ring-1 focus:ring-brand/30 outline-none"
            >
              {dimensions.map(d => (
                <option key={d.key} value={d.key}>{d.label}</option>
              ))}
            </select>
          )}
          {level !== 'total' && (
            <button onClick={goBack} className="flex items-center gap-1 text-xs text-brand hover:underline">
              <ArrowLeft size={12} /> Back
            </button>
          )}
        </div>
      </div>

      {level === 'total' && (
        <p className="text-[10px] text-slate-400 mb-3">Click a bar to drill down by dimension</p>
      )}

      {loadingDimension && (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-6 h-6 border-2 border-brand border-t-transparent rounded-full" />
        </div>
      )}

      {!loadingDimension && chartData.length === 0 && level !== 'total' && (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
            <ChevronRight size={16} />
          </div>
          <p className="text-sm font-semibold">No data available for this dimension</p>
          <p className="text-xs mt-1">Try selecting a different drill-down dimension above.</p>
          <button onClick={goBack} className="mt-3 text-xs text-brand font-semibold hover:underline flex items-center gap-1">
            <ArrowLeft size={12} /> Back to all products
          </button>
        </div>
      )}

      {!loadingDimension && chartData.length > 0 && (
        <div style={{ height: dynamicHeight, overflow: 'hidden' }} role="img" aria-label={`Bar chart showing ${breadcrumb.join(' > ')} data with ${chartData.length} items`}>
          <ResponsiveContainer width="100%" height="100%">
            {useHorizontal ? (
              <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ct.grid} />
                <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={formatValue} axisLine={false} tickLine={false} tickMargin={8} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} width={140} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={formatValue} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey={dataKey} radius={[0, 8, 8, 0]} barSize={24}
                  cursor={level === 'total' ? 'pointer' : 'default'}
                  onClick={level === 'total' ? handleBarClick : undefined}>
                  {chartData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
                </Bar>
              </BarChart>
            ) : (
              <BarChart data={chartData} margin={{ left: 10, right: 10, bottom: 40, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={ct.grid} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} interval={0} axisLine={false} tickLine={false} tickMargin={16} />
                <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={formatValue} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={formatValue} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey={dataKey} radius={[8, 8, 0, 0]} barSize={48}
                  cursor={level === 'total' ? 'pointer' : 'default'}
                  onClick={level === 'total' ? handleBarClick : undefined}>
                  {chartData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
