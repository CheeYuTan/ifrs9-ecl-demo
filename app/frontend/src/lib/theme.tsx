import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

export interface ThemeColors {
  brand: string;
  brandDark: string;
  brandLight: string;
}

export interface ThemeConfig {
  mode: 'light' | 'dark';
  colors: ThemeColors;
  preset: string;
}

const PRESETS: Record<string, ThemeColors> = {
  emerald: { brand: '#00D09C', brandDark: '#00B386', brandLight: '#E6FBF5' },
  blue: { brand: '#3B82F6', brandDark: '#2563EB', brandLight: '#EFF6FF' },
  purple: { brand: '#8B5CF6', brandDark: '#7C3AED', brandLight: '#F5F3FF' },
  rose: { brand: '#F43F5E', brandDark: '#E11D48', brandLight: '#FFF1F2' },
  amber: { brand: '#F59E0B', brandDark: '#D97706', brandLight: '#FFFBEB' },
  indigo: { brand: '#6366F1', brandDark: '#4F46E5', brandLight: '#EEF2FF' },
  cyan: { brand: '#06B6D4', brandDark: '#0891B2', brandLight: '#ECFEFF' },
  orange: { brand: '#F97316', brandDark: '#EA580C', brandLight: '#FFF7ED' },
};

export { PRESETS };

const DEFAULT_THEME: ThemeConfig = {
  mode: 'light',
  colors: PRESETS.emerald,
  preset: 'emerald',
};

const STORAGE_KEY = 'ecl-theme';

function loadTheme(): ThemeConfig {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return { ...DEFAULT_THEME, ...JSON.parse(stored) };
  } catch { /* */ }
  return DEFAULT_THEME;
}

function applyThemeToDOM(theme: ThemeConfig) {
  const root = document.documentElement;
  const { mode, colors } = theme;

  root.style.setProperty('--color-brand', colors.brand);
  root.style.setProperty('--color-brand-dark', colors.brandDark);
  root.style.setProperty('--color-brand-light', colors.brandLight);

  if (mode === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

interface ThemeCtx {
  theme: ThemeConfig;
  setMode: (mode: 'light' | 'dark') => void;
  toggleMode: () => void;
  setPreset: (preset: string) => void;
  setCustomColors: (colors: ThemeColors) => void;
  isDark: boolean;
}

const Ctx = createContext<ThemeCtx>({
  theme: DEFAULT_THEME,
  setMode: () => {},
  toggleMode: () => {},
  setPreset: () => {},
  setCustomColors: () => {},
  isDark: false,
});

export const useTheme = () => useContext(Ctx);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<ThemeConfig>(loadTheme);

  useEffect(() => {
    applyThemeToDOM(theme);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(theme));
  }, [theme]);

  const setMode = useCallback((mode: 'light' | 'dark') => {
    setTheme(prev => ({ ...prev, mode }));
  }, []);

  const toggleMode = useCallback(() => {
    setTheme(prev => ({ ...prev, mode: prev.mode === 'dark' ? 'light' : 'dark' }));
  }, []);

  const setPreset = useCallback((preset: string) => {
    const colors = PRESETS[preset];
    if (colors) setTheme(prev => ({ ...prev, preset, colors }));
  }, []);

  const setCustomColors = useCallback((colors: ThemeColors) => {
    setTheme(prev => ({ ...prev, preset: 'custom', colors }));
  }, []);

  return (
    <Ctx.Provider value={{ theme, setMode, toggleMode, setPreset, setCustomColors, isDark: theme.mode === 'dark' }}>
      {children}
    </Ctx.Provider>
  );
}
