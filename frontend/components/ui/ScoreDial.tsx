'use client';

import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import { cn, clamp } from '@/lib/utils';

interface ScoreDialProps {
  value: number | null | undefined;
  /** Number of blocks in the dial. */
  segments?: number;
  className?: string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SIZES = {
  sm: { num: 'text-4xl', seg: 'h-3', gap: 'gap-1' },
  md: { num: 'text-6xl', seg: 'h-5', gap: 'gap-1.5' },
  lg: { num: 'text-8xl', seg: 'h-7', gap: 'gap-2' },
};

/** Colour ramps up as the score climbs. */
function colorFor(index: number, segments: number) {
  const pct = ((index + 1) / segments) * 100;
  if (pct <= 33) return 'bg-blood';
  if (pct <= 55) return 'bg-tangerine';
  if (pct <= 75) return 'bg-sun';
  return 'bg-acid';
}

/**
 * Segmented block gauge. Deliberately chunky and stepped — no smooth arcs.
 */
export default function ScoreDial({
  value,
  segments = 20,
  className,
  label = 'Confidence',
  size = 'md',
}: ScoreDialProps) {
  const available = value !== null && value !== undefined;
  const target = clamp(available ? value : 0);
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (!available) {
      setShown(0);
      return;
    }
    if (reduce) {
      setShown(target);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / 1000, 1);
      const eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      setShown(target * eased);
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, available, reduce]);

  const filled = Math.round((shown / 100) * segments);
  const s = SIZES[size];

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-end justify-between gap-2">
        <span className="eyebrow">{label}</span>
        <span className="font-mono text-xs font-bold">
          {available ? `${Math.round(shown)}/100` : '--/100'}
        </span>
      </div>

      <div
        className={cn('mt-2 font-display font-black leading-none', s.num)}
        aria-live="polite"
      >
        {available ? (
          <>
            {Math.round(shown)}
            <span className="text-[0.45em]">%</span>
          </>
        ) : (
          <span className="text-smoke">--</span>
        )}
      </div>

      {/* Segmented bar */}
      <div
        className={cn('mt-3 flex border-3 border-ink bg-paper p-1.5', s.gap)}
        role="meter"
        aria-valuenow={available ? Math.round(shown) : undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        {Array.from({ length: segments }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'flex-1 border border-ink transition-colors duration-100',
              s.seg,
              i < filled ? colorFor(i, segments) : 'bg-sand'
            )}
          />
        ))}
      </div>
    </div>
  );
}
