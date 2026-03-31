import { useState } from 'react';
import {
  Moon, Sun, Palette, Eye, Pipette, Check, Sparkles,
} from 'lucide-react';
import Card from '../../components/Card';
import { useTheme, PRESETS } from '../../lib/theme';

const PRESET_META: Record<string, { label: string; emoji: string }> = {
  emerald: { label: 'Emerald', emoji: '💚' },
  blue: { label: 'Ocean Blue', emoji: '🌊' },
  purple: { label: 'Royal Purple', emoji: '👑' },
  rose: { label: 'Rose', emoji: '🌹' },
  amber: { label: 'Amber', emoji: '🔥' },
  indigo: { label: 'Indigo', emoji: '🔮' },
  cyan: { label: 'Cyan', emoji: '❄️' },
  orange: { label: 'Sunset', emoji: '🌅' },
};

function adjustBrightness(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount));
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount));
  return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
}

export default function AdminThemeConfig() {
  const { theme, setPreset, setMode, setCustomColors } = useTheme();
  const [customBrand, setCustomBrand] = useState(theme.colors.brand);

  const handleCustomColor = () => {
    const brandDark = adjustBrightness(customBrand, -20);
    const brandLight = adjustBrightness(customBrand, 90);
    setCustomColors({ brand: customBrand, brandDark, brandLight });
  };

  return (
    <div className="space-y-4">
      <Card accent="purple" icon={<Moon size={16} />} title="Appearance Mode" subtitle="Switch between light and dark mode">
        <div className="grid grid-cols-2 gap-4">
          {(['light', 'dark'] as const).map(mode => {
            const isActive = theme.mode === mode;
            const Icon = mode === 'light' ? Sun : Moon;
            return (
              <button key={mode} onClick={() => setMode(mode)}
                className={`relative flex items-center gap-4 p-5 rounded-2xl border-2 transition-all ${
                  isActive ? 'border-brand/40 bg-brand/5 shadow-md' : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  mode === 'light' ? 'bg-gradient-to-br from-amber-100 to-orange-100' : 'bg-gradient-to-br from-slate-700 to-slate-900'
                }`}>
                  <Icon size={22} className={mode === 'light' ? 'text-amber-600' : 'text-slate-300'} />
                </div>
                <div className="text-left">
                  <p className="text-sm font-bold text-slate-700 dark:text-slate-200 capitalize">{mode} Mode</p>
                  <p className="text-xs text-slate-400 mt-0.5">{mode === 'light' ? 'Clean, bright interface' : 'Easy on the eyes, sleek'}</p>
                </div>
                {isActive && (
                  <div className="absolute top-3 right-3 w-6 h-6 rounded-full gradient-brand flex items-center justify-center">
                    <Check size={12} className="text-white" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </Card>

      <Card accent="brand" icon={<Palette size={16} />} title="Color Theme" subtitle="Choose a preset or create your own">
        <div className="grid grid-cols-4 gap-3">
          {Object.entries(PRESETS).map(([key, colors]) => {
            const isActive = theme.preset === key;
            const meta = PRESET_META[key] || { label: key, emoji: '🎨' };
            return (
              <button key={key} onClick={() => setPreset(key)}
                className={`relative flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${
                  isActive ? 'border-brand/40 shadow-md scale-[1.02]' : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm'
                }`}>
                <div className="flex items-center gap-1.5">
                  <div className="w-8 h-8 rounded-lg shadow-inner" style={{ background: `linear-gradient(135deg, ${colors.brand}, ${colors.brandDark})` }} />
                  <div className="flex flex-col gap-0.5">
                    <div className="w-4 h-2 rounded-sm" style={{ background: colors.brand, opacity: 0.6 }} />
                    <div className="w-3 h-2 rounded-sm" style={{ background: colors.brandLight }} />
                  </div>
                </div>
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">{meta.emoji} {meta.label}</span>
                {isActive && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center" style={{ background: colors.brand }}>
                    <Check size={10} className="text-white" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </Card>

      <Card icon={<Pipette size={16} />} title="Custom Color" subtitle="Pick your own brand color">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <input type="color" value={customBrand} onChange={e => setCustomBrand(e.target.value)}
              className="w-12 h-12 rounded-xl cursor-pointer border-2 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition" />
            <div>
              <input value={customBrand} onChange={e => setCustomBrand(e.target.value)}
                className="w-28 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-sm font-mono focus:ring-2 focus:ring-brand/30 outline-none" />
              <p className="text-[10px] text-slate-400 mt-1">Hex color code</p>
            </div>
          </div>
          <button onClick={handleCustomColor}
            className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold gradient-brand text-white rounded-xl hover:opacity-90 transition shadow-md">
            <Sparkles size={14} /> Apply Custom Color
          </button>
          <div className="ml-4 flex items-center gap-2">
            <span className="text-xs text-slate-400">Preview:</span>
            <div className="flex gap-1">
              <div className="w-10 h-6 rounded" style={{ background: customBrand }} />
              <div className="w-10 h-6 rounded" style={{ background: adjustBrightness(customBrand, -20) }} />
              <div className="w-10 h-6 rounded" style={{ background: adjustBrightness(customBrand, 90) }} />
            </div>
          </div>
        </div>
      </Card>

      <Card icon={<Eye size={16} />} title="Live Preview" subtitle="See how your theme looks">
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-xl" style={{ background: `linear-gradient(135deg, ${theme.colors.brand}, ${theme.colors.brandDark})` }}>
            <p className="text-white text-sm font-bold">Primary Button</p>
            <p className="text-white/70 text-xs mt-1">Call to action</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <p className="text-sm font-bold" style={{ color: theme.colors.brand }}>Accent Text</p>
            <p className="text-xs text-slate-500 mt-1">Secondary content</p>
          </div>
          <div className="p-4 rounded-xl border-2" style={{ borderColor: theme.colors.brand + '40', background: theme.colors.brandLight }}>
            <p className="text-sm font-bold" style={{ color: theme.colors.brandDark }}>Highlight Card</p>
            <p className="text-xs mt-1" style={{ color: theme.colors.brandDark + 'AA' }}>Selected state</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
