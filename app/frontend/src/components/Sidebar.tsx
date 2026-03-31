import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Database, FlaskConical, GitBranch, Activity,
  BookOpen, ClipboardList, Shield, Sparkles, Settings,
  ChevronLeft, ChevronRight, Menu, X, Workflow, Upload,
} from 'lucide-react';

export type ViewType =
  | 'workflow'
  | 'data-mapping'
  | 'models'
  | 'backtesting'
  | 'markov'
  | 'hazard'
  | 'gl-journals'
  | 'reports'
  | 'approvals'
  | 'advanced'
  | 'admin';

interface NavItem {
  id: ViewType;
  label: string;
  icon: typeof Zap;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Workflow',
    items: [
      { id: 'workflow', label: 'ECL Workflow', icon: Workflow },
      { id: 'data-mapping', label: 'Data Mapping', icon: Upload },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { id: 'models', label: 'Models', icon: Database },
      { id: 'backtesting', label: 'Backtesting', icon: FlaskConical },
      { id: 'markov', label: 'Markov Chains', icon: GitBranch },
      { id: 'hazard', label: 'Hazard Models', icon: Activity },
    ],
  },
  {
    title: 'Operations',
    items: [
      { id: 'gl-journals', label: 'GL Journals', icon: BookOpen },
      { id: 'reports', label: 'Reports', icon: ClipboardList },
      { id: 'approvals', label: 'Approvals', icon: Shield },
      { id: 'advanced', label: 'Advanced', icon: Sparkles },
    ],
  },
];

const SETTINGS_ITEM: NavItem = { id: 'admin', label: 'Admin', icon: Settings };

const COLLAPSED_W = 64;
const EXPANDED_W = 240;

export function Sidebar({
  activeView,
  onNavigate,
}: {
  activeView: ViewType;
  onNavigate: (view: ViewType) => void;
}) {
  const [expanded, setExpanded] = useState(() => window.innerWidth >= 1440);
  const [hoverExpanded, setHoverExpanded] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const hoverTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1440px)');
    const handler = (e: MediaQueryListEvent) => setExpanded(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [activeView]);

  useEffect(() => {
    if (!mobileOpen) return;
    const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMobileOpen(false); };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [mobileOpen]);

  const isWide = expanded || hoverExpanded;
  const sidebarWidth = isWide ? EXPANDED_W : COLLAPSED_W;

  const handleMouseEnter = () => {
    if (!expanded) {
      hoverTimeout.current = setTimeout(() => setHoverExpanded(true), 200);
    }
  };

  const handleMouseLeave = () => {
    clearTimeout(hoverTimeout.current);
    setHoverExpanded(false);
  };

  const renderNavContent = (isMobile: boolean, layoutScope: 'mobile' | 'desktop' = 'desktop') => (
    <div className="flex flex-col h-full">
      {/* Logo area */}
      <div className={`flex items-center gap-3 px-4 h-16 flex-shrink-0 ${isMobile ? '' : 'border-b border-white/[0.06]'}`}>
        <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 shadow-lg">
          <Zap size={18} strokeWidth={2.5} className="text-white" />
        </div>
        <AnimatePresence>
          {(isWide || isMobile) && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.15 }}
              className="text-sm font-extrabold text-white whitespace-nowrap overflow-hidden"
            >
              ECL Workspace
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav groups */}
      <nav role="navigation" aria-label="Main navigation" className="flex-1 overflow-y-auto py-3 px-2 space-y-4 sidebar-scrollbar">
        {NAV_GROUPS.map((group) => (
          <div key={group.title}>
            <AnimatePresence>
              {(isWide || isMobile) && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.1 }}
                  className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-[0.15em] text-white/25"
                >
                  {group.title}
                </motion.p>
              )}
            </AnimatePresence>
            {!isWide && !isMobile && (
              <div className="mx-auto mb-1.5 w-6 h-px bg-white/[0.08]" />
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavButton
                  key={item.id}
                  item={item}
                  isActive={activeView === item.id}
                  isWide={isWide || isMobile}
                  onClick={() => onNavigate(item.id)}
                  layoutScope={layoutScope}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Settings at bottom */}
      <div className="flex-shrink-0 border-t border-white/[0.06] p-2 space-y-1">
        <NavButton
          item={SETTINGS_ITEM}
          isActive={activeView === 'admin'}
          isWide={isWide || isMobile}
          onClick={() => onNavigate('admin')}
          layoutScope={layoutScope}
        />
        {!isMobile && (
          <button
            onClick={() => setExpanded(!expanded)}
            aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-all duration-200 focus-visible:ring-2 focus-visible:ring-brand"
          >
            {expanded ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            <AnimatePresence>
              {isWide && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.15 }}
                  className="text-xs font-medium whitespace-nowrap overflow-hidden"
                >
                  Collapse
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation menu"
        aria-expanded={mobileOpen}
        className="fixed top-4 left-4 z-50 lg:hidden w-10 h-10 rounded-xl bg-[#0B0F1A]/90 border border-white/[0.08] flex items-center justify-center text-white/60 hover:text-white hover:bg-white/[0.1] transition-all backdrop-blur-sm focus-visible:ring-2 focus-visible:ring-brand"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -EXPANDED_W }}
              animate={{ x: 0 }}
              exit={{ x: -EXPANDED_W }}
              transition={{ type: 'spring', stiffness: 400, damping: 35 }}
              className="fixed top-0 left-0 bottom-0 z-50 lg:hidden"
              style={{ width: EXPANDED_W }}
            >
              <div className="h-full bg-[#0B0F1A] border-r border-white/[0.06] flex flex-col">
                <div className="absolute top-3 right-3 z-10">
                  <button
                    onClick={() => setMobileOpen(false)}
                    aria-label="Close navigation menu"
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white/40 hover:text-white hover:bg-white/[0.08] transition focus-visible:ring-2 focus-visible:ring-brand"
                  >
                    <X size={16} />
                  </button>
                </div>
                {renderNavContent(true, 'mobile')}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <motion.aside
        className="hidden lg:block fixed top-0 left-0 bottom-0 z-40"
        animate={{ width: sidebarWidth }}
        transition={{ type: 'spring', stiffness: 400, damping: 35 }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="h-full bg-[#0B0F1A] border-r border-white/[0.06] overflow-hidden">
          {renderNavContent(false)}
        </div>
      </motion.aside>

      {/* Spacer for desktop layout */}
      <motion.div
        className="hidden lg:block flex-shrink-0"
        animate={{ width: expanded ? EXPANDED_W : COLLAPSED_W }}
        transition={{ type: 'spring', stiffness: 400, damping: 35 }}
      />
    </>
  );
}

function NavButton({
  item,
  isActive,
  isWide,
  onClick,
  layoutScope = 'desktop',
}: {
  item: NavItem;
  isActive: boolean;
  isWide: boolean;
  onClick: () => void;
  layoutScope?: 'mobile' | 'desktop';
}) {
  const Icon = item.icon;

  return (
    <button
      onClick={onClick}
      aria-current={isActive ? 'page' : undefined}
      aria-label={!isWide ? item.label : undefined}
      className={`relative w-full flex items-center gap-3 rounded-xl transition-all duration-200 focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-1 focus-visible:ring-offset-[#0B0F1A] ${
        isWide ? 'px-3 py-2.5' : 'px-0 py-2.5 justify-center'
      } ${
        isActive
          ? 'bg-[var(--color-brand)]/15 text-[var(--color-brand)]'
          : 'text-white/45 hover:text-white/80 hover:bg-white/[0.04]'
      }`}
    >
      {isActive && (
        <motion.div
          layoutId={`sidebar-active-pill-${layoutScope}`}
          className="absolute inset-0 rounded-xl bg-[var(--color-brand)]/15 border border-[var(--color-brand)]/20"
          transition={{ type: 'spring', stiffness: 350, damping: 30 }}
        />
      )}
      <Icon
        size={20}
        strokeWidth={isActive ? 2.2 : 1.8}
        className={`relative z-10 flex-shrink-0 transition-colors duration-200 ${
          isActive ? 'text-[var(--color-brand)]' : ''
        }`}
      />
      <AnimatePresence>
        {isWide && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.15 }}
            className={`relative z-10 text-[13px] font-semibold whitespace-nowrap overflow-hidden ${
              isActive ? 'text-[var(--color-brand)]' : ''
            }`}
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
