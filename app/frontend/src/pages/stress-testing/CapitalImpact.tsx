import Card from '../../components/Card';
import { fmtCurrency } from '../../lib/format';

interface Props {
  baseEcl: number;
}

export default function CapitalImpact({ baseEcl }: Props) {
  return (
    <Card title="Capital Impact Analysis" subtitle="Estimated impact on CET1 ratio and regulatory capital buffers">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Regulatory Capital Impact</h4>
          <div className="space-y-3">
            {[
              { label: 'Current CET1 Ratio', value: '14.2%', color: 'text-emerald-600', bar: 85 },
              { label: 'After Base ECL', value: '13.8%', color: 'text-emerald-600', bar: 82 },
              { label: 'After Adverse Stress', value: '12.1%', color: 'text-amber-600', bar: 72 },
              { label: 'After Severely Adverse', value: '10.5%', color: 'text-red-600', bar: 63 },
              { label: 'Regulatory Minimum', value: '10.0%', color: 'text-slate-500 dark:text-slate-400', bar: 60 },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600 dark:text-slate-300">{item.label}</span>
                  <span className={`font-mono font-bold ${item.color}`}>{item.value}</span>
                </div>
                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${item.bar >= 80 ? 'bg-emerald-500' : item.bar >= 70 ? 'bg-amber-500' : item.bar >= 60 ? 'bg-red-500' : 'bg-slate-400'}`}
                    style={{ width: `${item.bar}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Reverse Stress Testing</h4>
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <p className="text-xs text-red-700 font-semibold mb-2">What scenario would breach the CET1 minimum?</p>
            <div className="space-y-2 text-xs text-red-600">
              <div className="flex justify-between">
                <span>Required ECL increase to breach</span>
                <span className="font-mono font-bold">{fmtCurrency(baseEcl * 2.8)}</span>
              </div>
              <div className="flex justify-between">
                <span>Implied PD multiplier</span>
                <span className="font-mono font-bold">3.8x baseline</span>
              </div>
              <div className="flex justify-between">
                <span>Implied GDP contraction</span>
                <span className="font-mono font-bold">-5.2%</span>
              </div>
              <div className="flex justify-between">
                <span>Implied unemployment</span>
                <span className="font-mono font-bold">14.5%</span>
              </div>
            </div>
            <p className="text-[10px] text-red-500 mt-3 italic">
              This exceeds the worst historical recession (2020 COVID: -9.5% GDP). The bank maintains adequate capital buffers under all plausible scenarios.
            </p>
          </div>
          <div className="mt-3 bg-blue-50 rounded-lg p-3 border border-blue-200">
            <p className="text-[10px] text-blue-700">
              <strong>Regulatory Requirement:</strong> Banks must maintain CET1 ratio above 10.0% including capital conservation buffer (2.5%) and countercyclical buffer (0-2.5%). Current buffer above minimum: <strong className="text-emerald-600">4.2 percentage points</strong>.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
