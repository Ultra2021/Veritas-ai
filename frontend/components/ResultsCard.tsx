'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Printer } from 'lucide-react';
import { CandidateInfo } from '@/types/interview';
import ScoreDial from './ui/ScoreDial';
import { cn } from '@/lib/utils';

type Recommendation =
  | 'STRONG HIRE'
  | 'HIRE'
  | 'LEANING HIRE'
  | 'NO HIRE'
  | 'COLLECTING EVIDENCE';

interface ResultsCardProps {
  candidateInfo: CandidateInfo;
  confidenceScore: number | null | undefined;
  sessionId?: string | null;
  recommendation?: Recommendation;
  reasoning?: string[];
}

const REC: Record<Recommendation, { bg: string; stamp: string }> = {
  'STRONG HIRE': { bg: 'bg-acid', stamp: 'border-ink text-ink' },
  HIRE: { bg: 'bg-mint', stamp: 'border-ink text-ink' },
  'LEANING HIRE': { bg: 'bg-sun', stamp: 'border-ink text-ink' },
  'NO HIRE': { bg: 'bg-blood', stamp: 'border-paper text-paper' },
  'COLLECTING EVIDENCE': { bg: 'bg-sand', stamp: 'border-smoke text-smoke' },
};

export default function ResultsCard({
  candidateInfo,
  confidenceScore,
  sessionId,
  recommendation = 'COLLECTING EVIDENCE',
  reasoning,
}: ResultsCardProps) {
  const points = reasoning?.length ? reasoning : [];
  const style = REC[recommendation] ?? REC['COLLECTING EVIDENCE'];

  return (
    <div className="border-3 border-ink bg-paper shadow-brutal-xl">
      {/* header bar */}
      <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
          VERDICT / CASE {sessionId ? sessionId.slice(0, 8).toUpperCase() : 'N-A'}
        </span>
        <button
          onClick={() => typeof window !== 'undefined' && window.print()}
          className="flex items-center gap-1.5 border-2 border-paper bg-paper px-2 py-0.5 font-mono text-[10px] font-bold uppercase text-ink transition-colors hover:bg-acid"
        >
          <Printer className="h-3 w-3" strokeWidth={3} />
          PRINT
        </button>
      </div>

      <div className="grid lg:grid-cols-[1.2fr_1fr]">
        {/* left: identity + reasoning */}
        <div className="border-b-3 border-ink p-5 sm:p-7 lg:border-b-0 lg:border-r-3">
          <span className="label">SUBJECT</span>
          <h1 className="mt-2 display text-[clamp(2rem,6vw,4rem)] leading-[0.9]">
            {candidateInfo.name || 'UNKNOWN'}
          </h1>
          <p className="mt-2 font-mono text-xs font-bold uppercase text-smoke">
            {candidateInfo.targetRole} · {candidateInfo.experienceLevel}
          </p>
          <p className="font-mono text-xs font-bold uppercase text-smoke">
            LENS: {candidateInfo.companyMode}
          </p>

          <div className="mt-6">
            <span className="label bg-cobalt">FINDINGS</span>
            {points.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {points.map((p, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex gap-2 border-l-3 border-ink pl-3 text-xs font-medium leading-relaxed"
                  >
                    <span className="font-display">›</span>
                    {p}
                  </motion.li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 font-mono text-xs font-bold uppercase text-smoke">
                No findings recorded yet
              </p>
            )}
          </div>
        </div>

        {/* right: stamp + dial */}
        <div className={cn('relative flex flex-col justify-center p-5 sm:p-7', style.bg)}>
          <motion.div
            initial={{ scale: 1.5, opacity: 0, rotate: -22 }}
            animate={{ scale: 1, opacity: 1, rotate: -8 }}
            transition={{ delay: 0.2, ease: [0.34, 1.56, 0.64, 1], duration: 0.5 }}
            className={cn(
              'mx-auto mb-6 border-6 px-5 py-3 text-center',
              style.stamp
            )}
          >
            <div className="font-display text-[clamp(1.5rem,4vw,2.75rem)] leading-none">
              {recommendation}
            </div>
          </motion.div>

          <ScoreDial value={confidenceScore} label="Confidence" size="sm" />
        </div>
      </div>
    </div>
  );
}
