'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CompetencyState } from '@/types/interview';
import { cn } from '@/lib/utils';

export interface GrowthTopic {
  title: string;
  category: string;
  reasoning: string;
  difficulty: 'Intermediate' | 'Advanced' | 'Mastery';
}

interface GrowthMapProps {
  topics?: GrowthTopic[];
  competencies?: CompetencyState[];
}

const DIFF: Record<GrowthTopic['difficulty'], string> = {
  Mastery: 'bg-violetPop text-paper',
  Advanced: 'bg-hot text-paper',
  Intermediate: 'bg-sun',
};

export default function GrowthMap({ topics, competencies }: GrowthMapProps) {
  let list: GrowthTopic[] = [];

  if (topics && topics.length > 0) {
    list = topics;
  } else if (competencies && competencies.length > 0) {
    list = competencies
      .filter((c) => c.status === 'needs_followup' || c.evidenceScore < 60)
      .map((c) => ({
        title: `Deep-Dive: ${c.competency}`,
        category: 'Competency Focus',
        reasoning:
          c.notes ||
          `Evidence score is currently ${c.evidenceScore}%. Further practice and evidence collection recommended.`,
        difficulty: c.evidenceScore < 40 ? 'Advanced' : 'Intermediate',
      }));
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h3 className="display text-3xl sm:text-4xl">HOMEWORK</h3>
        <span className="font-mono text-xs font-bold uppercase text-smoke">
          Where to dig next
        </span>
      </div>

      {list.length === 0 ? (
        <div className="border-3 border-ink bg-mint p-8 text-center shadow-brutal">
          <p className="font-display text-xl uppercase">NOTHING TO FIX</p>
          <p className="mt-1 text-xs font-bold">
            Either every claim held up, or the interrogation hasn&apos;t started.
          </p>
        </div>
      ) : (
        <ol className="space-y-4">
          {list.map((item, i) => (
            <motion.li
              key={item.title}
              initial={{ opacity: 0, x: -18 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06, ease: [0.34, 1.56, 0.64, 1] }}
              className="press flex gap-0 border-3 border-ink bg-paper shadow-brutal"
            >
              <div className="flex w-14 shrink-0 items-center justify-center border-r-3 border-ink bg-ink font-display text-2xl text-paper">
                {String(i + 1).padStart(2, '0')}
              </div>
              <div className="min-w-0 flex-1 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      'border-2 border-ink px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase',
                      DIFF[item.difficulty]
                    )}
                  >
                    {item.difficulty}
                  </span>
                  <span className="font-mono text-[10px] font-bold uppercase text-smoke">
                    {item.category}
                  </span>
                </div>
                <h4 className="mt-1.5 font-display text-lg uppercase leading-tight">
                  {item.title}
                </h4>
                <p className="mt-1 text-xs font-medium leading-relaxed">{item.reasoning}</p>
              </div>
            </motion.li>
          ))}
        </ol>
      )}
    </div>
  );
}
