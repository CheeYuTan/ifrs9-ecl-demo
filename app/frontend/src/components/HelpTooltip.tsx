import { useState, useRef, useEffect, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, X } from 'lucide-react';

interface Props {
  content: ReactNode;
  term?: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  size?: number;
  className?: string;
  inline?: boolean;
}

export default function HelpTooltip({
  content,
  term,
  position = 'top',
  size = 14,
  className = '',
  inline = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const [adjustedPos, setAdjustedPos] = useState(position);
  const ref = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  // Viewport boundary detection: adjust position if tooltip would render off-screen
  useEffect(() => {
    if (!open || !tooltipRef.current) { setAdjustedPos(position); return; }
    const rect = tooltipRef.current.getBoundingClientRect();
    let pos = position;
    if (rect.top < 0) pos = 'bottom';
    else if (rect.bottom > window.innerHeight) pos = 'top';
    else if (rect.left < 0) pos = 'right';
    else if (rect.right > window.innerWidth) pos = 'left';
    setAdjustedPos(pos);
  }, [open, position]);

  const positionClasses: Record<string, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses: Record<string, string> = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-slate-800 border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-slate-800 border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-slate-800 border-y-transparent border-l-transparent',
  };

  const originMap: Record<string, string> = {
    top: 'bottom center',
    bottom: 'top center',
    left: 'right center',
    right: 'left center',
  };

  return (
    <div
      ref={ref}
      className={`relative ${inline ? 'inline-flex' : 'inline-flex'} items-center ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      {term ? (
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-0.5 text-inherit border-b border-dashed border-current/30 hover:border-current/60 transition cursor-help"
        >
          <span>{term}</span>
          <HelpCircle size={size - 2} className="text-slate-400 hover:text-brand transition flex-shrink-0" />
        </button>
      ) : (
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-brand/10 text-slate-400 hover:text-brand transition cursor-help"
          aria-label="Help"
        >
          <HelpCircle size={size} />
        </button>
      )}

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            ref={tooltipRef}
            style={{ transformOrigin: originMap[adjustedPos] }}
            className={`absolute z-50 ${positionClasses[adjustedPos]} w-72 max-w-[90vw]`}
          >
            <div className="relative bg-slate-800 text-white rounded-xl shadow-xl px-4 py-3">
              <button
                onClick={(e) => { e.stopPropagation(); setOpen(false); }}
                aria-label="Close"
                className="absolute top-2 right-2 text-white/40 hover:text-white transition"
              >
                <X size={12} />
              </button>
              <div className="text-xs leading-relaxed pr-4 [&_strong]:text-brand [&_a]:text-brand [&_a]:underline">
                {content}
              </div>
              <div className={`absolute w-0 h-0 border-[6px] ${arrowClasses[adjustedPos]}`} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export const IFRS9_HELP = {
  ECL: (
    <span>
      <strong>Expected Credit Loss (ECL)</strong> — the probability-weighted estimate of credit losses
      over the expected life of a financial instrument, per <strong>IFRS 9.5.5.17</strong>.
    </span>
  ),
  GCA: (
    <span>
      <strong>Gross Carrying Amount (GCA)</strong> — the amortized cost of a financial asset before
      deducting any loss allowance.
    </span>
  ),
  STAGE_1: (
    <span>
      <strong>Stage 1 — 12-month ECL</strong>: Assets with no significant increase in credit risk
      since initial recognition. Loss allowance equals 12-month expected credit losses.
    </span>
  ),
  STAGE_2: (
    <span>
      <strong>Stage 2 — Lifetime ECL</strong>: Assets with significant increase in credit risk (SICR)
      but not credit-impaired, per <strong>IFRS 9.5.5.3</strong>. Loss allowance equals lifetime ECL.
    </span>
  ),
  STAGE_3: (
    <span>
      <strong>Stage 3 — Lifetime ECL (credit-impaired)</strong>: Assets where objective evidence of
      impairment exists, per <strong>IFRS 9.5.5.1</strong>. Interest revenue calculated on net carrying amount.
    </span>
  ),
  PD: (
    <span>
      <strong>Probability of Default (PD)</strong> — the likelihood that a borrower will default within
      a given time horizon. Point-in-time PD is adjusted for forward-looking macro scenarios.
    </span>
  ),
  LGD: (
    <span>
      <strong>Loss Given Default (LGD)</strong> — the percentage of exposure that is lost if a borrower
      defaults. LGD = 1 − Recovery Rate. Adjusted for collateral and workout costs.
    </span>
  ),
  EAD: (
    <span>
      <strong>Exposure at Default (EAD)</strong> — the total value exposed to loss at the time of default,
      including drawn balances and a credit conversion factor for undrawn commitments.
    </span>
  ),
  SICR: (
    <span>
      <strong>Significant Increase in Credit Risk (SICR)</strong> — the trigger for moving from Stage 1
      to Stage 2, assessed by comparing lifetime PD at origination vs. reporting date, per{' '}
      <strong>IFRS 9.5.5.9</strong>.
    </span>
  ),
  COVERAGE_RATIO: (
    <span>
      <strong>Coverage Ratio</strong> = ECL ÷ GCA — the proportion of gross carrying amount covered
      by the loss allowance. Higher ratios indicate greater provisioning relative to exposure.
    </span>
  ),
  GL_RECON: (
    <span>
      <strong>GL Reconciliation</strong> — verifies that the loan tape balances match the General Ledger.
      Variances beyond tolerance require Finance sign-off per <strong>IFRS 7.35I</strong>.
    </span>
  ),
} as const;
