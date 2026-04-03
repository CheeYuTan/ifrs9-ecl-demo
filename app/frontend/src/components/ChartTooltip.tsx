interface Props {
  active?: boolean;
  payload?: any[];
  formatValue?: (v: number) => string;
}

export default function ChartTooltip({ active, payload, formatValue = (v) => v.toLocaleString() }: Props) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="glass-card rounded-xl px-3 py-2 shadow-lg border border-slate-100 dark:border-slate-700">
      <p className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-0.5">{d.payload.name || d.name}</p>
      <p className="text-sm font-extrabold" style={{ color: d.fill || d.color }}>
        {formatValue(d.value)}
      </p>
    </div>
  );
}
