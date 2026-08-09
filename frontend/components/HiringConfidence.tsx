'use client';

import React from 'react';
import ScoreDial from './ui/ScoreDial';
import { cn } from '@/lib/utils';

interface HiringConfidenceProps {
  confidence: number | null | undefined; // 0-100 or null
}

function verdict(score: number | null | undefined) {
  if (score === null || score === undefined)
    return { label: 'PENDING', bg: 'bg-sand', note: 'Not enough evidence yet' };
  if (score >= 85)
    return { label: 'STRONG HIRE', bg: 'bg-acid', note: 'Claims held up under pressure' };
  if (score >= 65)
    return { label: 'HIRE', bg: 'bg-mint', note: 'Solid proof on the core claims' };
  if (score >= 45)
    return { label: 'LEANING HIRE', bg: 'bg-sun', note: 'Some claims still unproven' };
  return { label: 'COLLECTING', bg: 'bg-tangerine', note: 'Evidence is thin so far' };
}

export default function HiringConfidence({ confidence }: HiringConfidenceProps) {
  const v = verdict(confidence);

  return (
    <div className="border-3 border-ink bg-paper shadow-brutal-md">
      <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
          THE NUMBER
        </span>
      </div>

      <div className="p-4">
        <ScoreDial value={confidence} label="Confidence" size="md" />

        <div className={cn('mt-4 border-3 border-ink p-3', v.bg)}>
          <div className="font-display text-2xl uppercase leading-none">{v.label}</div>
          <p className="mt-1 text-[11px] font-bold">{v.note}</p>
        </div>
      </div>
    </div>
  );
}
