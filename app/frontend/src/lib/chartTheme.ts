import { useTheme } from './theme';

export function useChartTheme() {
  const { isDark } = useTheme();
  return {
    grid: isDark ? 'rgba(255,255,255,0.06)' : '#F1F5F9',
    axis: isDark ? '#94A3B8' : '#475569',
    axisLight: isDark ? '#64748B' : '#64748B',
    label: isDark ? '#CBD5E1' : '#475569',
    tooltip: {
      bg: isDark ? 'rgba(30,41,59,0.95)' : 'rgba(255,255,255,0.95)',
      border: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
      text: isDark ? '#F1F5F9' : '#0F172A',
    },
    reference: isDark ? 'rgba(255,255,255,0.1)' : '#E5E7EB',
  };
}
