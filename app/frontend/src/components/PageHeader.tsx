import StatusBadge from './StatusBadge';

interface Props {
  title: string;
  subtitle: string;
  status?: string;
  children?: React.ReactNode;
}

export default function PageHeader({ title, subtitle, status, children }: Props) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">{title}</h2>
        <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        {children}
        {status && <StatusBadge status={status} />}
      </div>
    </div>
  );
}
