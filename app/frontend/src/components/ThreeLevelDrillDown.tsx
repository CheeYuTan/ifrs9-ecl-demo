import { useState, useMemo, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import ChartTooltip from './ChartTooltip';
import { formatProductName } from '../lib/format';
import { useChartTheme } from '../lib/chartTheme';
import { api } from '../lib/api';
import { sortChartData } from '../lib/chartUtils';

type DrillLevel = 'level0' | 'product' | 'cohort';

interface Props {
  level0Data: any[];
  level0Key: string;
  level0Label: string;
  dataKey: string;
  title: string;
  formatValue?: (v: number) => string;
  height?: number;
  colors?: string[];
  level0Colors?: Record<string | number, string>;
  fetchProductData: (level0Value: string | number) => Promise<any[]>;
  fetchCohortData: (product: string, dimension?: string) => Promise<any[]>;
}

const DEFAULT_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'];

export default function ThreeLevelDrillDown({
  level0Data,
  level0Key,
  level0Label,
  dataKey,
  title: _title,
  formatValue = (v) => v.toLocaleString(),
  height = 340,
  colors = DEFAULT_COLORS,
  level0Colors,
  fetchProductData,
  fetchCohortData,
}: Props) {
  void _title;
  const ct = useChartTheme();
  const [level, setLevel] = useState<DrillLevel>('level0');
  const [selectedL0, setSelectedL0] = useState<string | number | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [productData, setProductData] = useState<any[]>([]);
  const [cohortData, setCohortData] = useState<any[]>([]);
  const [loadingProduct, setLoadingProduct] = useState(false);
  const [loadingCohort, setLoadingCohort] = useState(false);
  const [dimensions, setDimensions] = useState<{ key: string; label: string }[]>([]);
  const [activeDimension, setActiveDimension] = useState('risk_band');

  useEffect(() => {
    api.drillDownDimensions().then(setDimensions).catch(() => {});
  }, []);

  const chartData = useMemo(() => {
    if (level === 'level0') {
      return sortChartData(level0Data.map(d => ({
        ...d,
        name: d.name || formatProductName(d[level0Key]),
        _rawKey: d[level0Key],
      })));
    }
    if (level === 'product') {
      return sortChartData(productData.map(d => ({
        ...d,
        name: formatProductName(d.product_type || d.name || 'Unknown'),
        _rawKey: d.product_type,
      })));
    }
    if (level === 'cohort') {
      return sortChartData(cohortData.map(d => ({
        ...d,
        name: d.cohort_id || d.name || 'Unknown',
      })));
    }
    return [];
  }, [level, level0Data, productData, cohortData, level0Key]);

  const getBarColor = useCallback((entry: any, idx: number) => {
    if (level === 'level0' && level0Colors) {
      return level0Colors[entry._rawKey] || colors[idx % colors.length];
    }
    return colors[idx % colors.length];
  }, [level, level0Colors, colors]);

  const useHorizontal = chartData.length > 8;

  const breadcrumb = useMemo(() => {
    const parts = [`All ${level0Label}s`];
    if ((level === 'product' || level === 'cohort') && selectedL0 != null) {
      parts.push(formatProductName(selectedL0));
    }
    if (level === 'cohort' && selectedProduct) {
      parts.push(formatProductName(selectedProduct));
    }
    return parts;
  }, [level, selectedL0, selectedProduct, level0Label]);

  const handleBarClick = useCallback(async (rechartsData: any, idx: number) => {
    const entry = rechartsData?.payload || rechartsData || chartData[idx] || {};

    if (level === 'level0') {
      const rawKey = entry._rawKey ?? entry[level0Key];
      if (rawKey == null) return;
      setSelectedL0(rawKey);
      setLevel('product');
      setLoadingProduct(true);
      try {
        const data = await fetchProductData(rawKey);
        setProductData(data);
      } catch {
        setProductData([]);
      } finally {
        setLoadingProduct(false);
      }
    } else if (level === 'product') {
      const product = entry._rawKey || entry.product_type;
      if (!product) return;
      setSelectedProduct(product);
      setLevel('cohort');
      setLoadingCohort(true);
      try {
        const data = await fetchCohortData(product, activeDimension);
        setCohortData(data);
      } catch {
        setCohortData([]);
      } finally {
        setLoadingCohort(false);
      }
    }
  }, [level, chartData, level0Key, fetchProductData, fetchCohortData, activeDimension]);

  const handleDimensionChange = useCallback(async (dim: string) => {
    setActiveDimension(dim);
    if (selectedProduct) {
      setLoadingCohort(true);
      try {
        const data = await fetchCohortData(selectedProduct, dim);
        setCohortData(data);
      } catch {
        setCohortData([]);
      } finally {
        setLoadingCohort(false);
      }
    }
  }, [selectedProduct, fetchCohortData]);

  const goBack = useCallback(() => {
    if (level === 'cohort') {
      setLevel('product');
      setSelectedProduct(null);
      setCohortData([]);
    } else if (level === 'product') {
      setLevel('level0');
      setSelectedL0(null);
      setProductData([]);
    }
  }, [level]);

  const goToLevel = useCallback((idx: number) => {
    if (idx === 0) {
      setLevel('level0');
      setSelectedL0(null);
      setSelectedProduct(null);
      setProductData([]);
      setCohortData([]);
    } else if (idx === 1) {
      setLevel('product');
      setSelectedProduct(null);
      setCohortData([]);
    }
  }, []);

  useEffect(() => {
    setLevel('level0');
    setSelectedL0(null);
    setSelectedProduct(null);
    setProductData([]);
    setCohortData([]);
  }, [level0Data]);

  const isLoading = (level === 'product' && loadingProduct) || (level === 'cohort' && loadingCohort);
  const isEmpty = !isLoading && chartData.length === 0 && level !== 'level0';
  const isClickable = level !== 'cohort';
  const dynamicHeight = useHorizontal ? Math.max(height, chartData.length * 36 + 40) : height;

  const hintText = level === 'level0'
    ? `Click a ${level0Label.toLowerCase()} to drill into products`
    : level === 'product'
    ? 'Click a product to drill by dimension'
    : null;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          {breadcrumb.map((part, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={10} className="text-slate-300" />}
              <button
                onClick={() => goToLevel(i)}
                className={i < breadcrumb.length - 1 ? 'text-brand hover:underline cursor-pointer' : 'font-semibold text-slate-700 dark:text-slate-200'}
              >
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
          {level !== 'level0' && (
            <button onClick={goBack} className="flex items-center gap-1 text-xs text-brand hover:underline">
              <ArrowLeft size={12} /> Back
            </button>
          )}
        </div>
      </div>

      {hintText && (
        <p className="text-[10px] text-slate-400 mb-3">{hintText}</p>
      )}

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-6 h-6 border-2 border-brand border-t-transparent rounded-full" />
        </div>
      )}

      {isEmpty && (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
            <ChevronRight size={16} />
          </div>
          <p className="text-sm font-semibold">No data available</p>
          <p className="text-xs mt-1">Try selecting a different dimension or go back.</p>
          <button onClick={goBack} className="mt-3 text-xs text-brand font-semibold hover:underline flex items-center gap-1">
            <ArrowLeft size={12} /> Go back
          </button>
        </div>
      )}

      {!isLoading && chartData.length > 0 && (
        <div style={{ height: dynamicHeight, overflow: 'hidden' }}>
          <ResponsiveContainer width="100%" height="100%">
            {useHorizontal ? (
              <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ct.grid} />
                <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={formatValue} axisLine={false} tickLine={false} tickMargin={8} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} width={140} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={formatValue} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey={dataKey} radius={[0, 8, 8, 0]} barSize={24}
                  cursor={isClickable ? 'pointer' : 'default'}
                  onClick={isClickable ? handleBarClick : undefined}>
                  {chartData.map((entry, i) => <Cell key={i} fill={getBarColor(entry, i)} />)}
                </Bar>
              </BarChart>
            ) : (
              <BarChart data={chartData} margin={{ left: 10, right: 10, bottom: 40, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={ct.grid} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} interval={0} axisLine={false} tickLine={false} tickMargin={16} />
                <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={formatValue} axisLine={false} tickLine={false} tickMargin={8} />
                <Tooltip content={<ChartTooltip formatValue={formatValue} />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey={dataKey} radius={[8, 8, 0, 0]} barSize={48}
                  cursor={isClickable ? 'pointer' : 'default'}
                  onClick={isClickable ? handleBarClick : undefined}>
                  {chartData.map((entry, i) => <Cell key={i} fill={getBarColor(entry, i)} />)}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
