'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InterviewDNA as InterviewDNAType } from '@/types/interview';
import { cn } from '@/lib/utils';

interface InterviewDNAProps {
  dna: InterviewDNAType | null | undefined;
  compact?: boolean;
}

const VECTORS = [
  { key: 'technicalKnowledge', label: 'TECHNICAL', bg: 'bg-cobalt' },
  { key: 'communication', label: 'COMMS', bg: 'bg-hot' },
  { key: 'problemSolving', label: 'PROBLEM', bg: 'bg-acid' },
  { key: 'leadership', label: 'LEADERSHIP', bg: 'bg-sun' },
  { key: 'learningAbility', label: 'LEARNING', bg: 'bg-mint' },
] as const;

export default function InterviewDNA({ dna, compact = false }: InterviewDNAProps) {
  const values = {
    technicalKnowledge: dna?.technicalKnowledge ?? 0,
    communication: dna?.communication ?? 0,
    problemSolving: dna?.problemSolving ?? 0,
    leadership: dna?.leadership ?? 0,
    learningAbility: dna?.learningAbility ?? 0,
  };

  return (
    <div className="border-3 border-ink bg-paper shadow-brutal-md">
      <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
          DNA / 5 VECTORS
        </span>
        {!dna && <span className="font-mono text-[11px] font-bold text-sun">NO DATA</span>}
      </div>

      {!dna ? (
        <p className="p-6 text-center font-mono text-xs font-bold uppercase text-smoke">
          Builds as evidence lands
        </p>
      ) : (
        <div className={cn('space-y-3', compact ? 'p-3' : 'p-5')}>
          {VECTORS.map((v, i) => {
            const val = values[v.key];
            return (
              <div key={v.key}>
                <div className="flex items-baseline justify-between">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-widest">
                    {v.label}
                  </span>
                  <span className="font-display text-lg leading-none">{val}</span>
                </div>
                <div className="mt-1 h-5 border-3 border-ink bg-paper">
                  <motion.div
                    className={cn('h-full border-r-3 border-ink', v.bg)}
                    initial={{ width: 0 }}
                    animate={{ width: `${val}%` }}
                    transition={{
                      duration: 0.7,
                      delay: i * 0.07,
                      ease: [0.34, 1.56, 0.64, 1],
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
