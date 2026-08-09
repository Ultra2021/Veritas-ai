'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CompetencyState, SkillDetail } from '@/types/interview';
import { cn } from '@/lib/utils';

interface VerifiedSkillsProps {
  competencies?: CompetencyState[];
  skills?: SkillDetail[];
}

const META: Record<
  CompetencyState['status'],
  { tag: string; bg: string; bar: string }
> = {
  verified: { tag: 'PROVEN', bg: 'bg-mint', bar: 'bg-mint' },
  needs_followup: { tag: 'SHAKY', bg: 'bg-sun', bar: 'bg-sun' },
  in_progress: { tag: 'DIGGING', bg: 'bg-cobalt text-paper', bar: 'bg-cobalt' },
  pending: { tag: 'UNTOUCHED', bg: 'bg-sand', bar: 'bg-sand' },
};

function Head({ n, total }: { n: number; total: number }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-2">
      <h3 className="display text-3xl sm:text-4xl">THE LEDGER</h3>
      <span className="border-3 border-ink bg-ink px-3 py-1 font-mono text-xs font-bold text-paper">
        {n}/{total} PROVEN
      </span>
    </div>
  );
}

export default function VerifiedSkills({ competencies, skills }: VerifiedSkillsProps) {
  const list = competencies || [];
  const proven = list.filter((c) => c.status === 'verified').length;

  // Legacy fallback when only flat skills are available.
  if (list.length === 0 && skills && skills.length > 0) {
    const n = skills.filter((s) => s.status === 'Verified').length;
    return (
      <div className="space-y-5">
        <Head n={n} total={skills.length} />
        <div className="grid gap-4 sm:grid-cols-2">
          {skills.map((s, i) => (
            <motion.div
              key={s.name}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, ease: [0.34, 1.56, 0.64, 1] }}
              className="border-3 border-ink bg-paper p-4 shadow-brutal press"
            >
              <h4 className="font-display text-lg uppercase leading-tight">{s.name}</h4>
              <div className="mt-2 h-4 border-3 border-ink bg-paper">
                <div className="h-full bg-mint" style={{ width: `${s.score}%` }} />
              </div>
              <div className="mt-1 text-right font-mono text-xs font-bold">{s.score}%</div>
              {s.evidenceSnippet && (
                <p className="mt-2 border-l-3 border-ink pl-2 text-[11px] font-medium italic">
                  &ldquo;{s.evidenceSnippet}&rdquo;
                </p>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Head n={proven} total={list.length} />

      {list.length === 0 ? (
        <div className="border-3 border-ink bg-sand p-8 text-center shadow-brutal">
          <p className="font-mono text-xs font-bold uppercase text-smoke">
            Nothing entered into the record yet
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {list.map((c, i) => {
            const m = META[c.status] ?? META.pending;
            return (
              <motion.div
                key={c.competency}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, ease: [0.34, 1.56, 0.64, 1] }}
                className="press border-3 border-ink bg-paper p-4 shadow-brutal"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-display text-lg uppercase leading-tight">
                    {c.competency}
                  </h4>
                  <span
                    className={cn(
                      'shrink-0 border-2 border-ink px-1.5 py-0.5 font-mono text-[9px] font-bold',
                      m.bg
                    )}
                  >
                    {m.tag}
                  </span>
                </div>

                <div className="mt-2 flex items-center gap-3 font-mono text-[10px] font-bold text-smoke">
                  <span>TRIES {c.attempts}</span>
                  {typeof c.day === 'number' && <span>DAY {c.day}</span>}
                </div>

                <div className="mt-2 h-4 border-3 border-ink bg-paper">
                  <motion.div
                    className={cn('h-full', m.bar)}
                    initial={{ width: 0 }}
                    animate={{ width: `${c.evidenceScore}%` }}
                    transition={{ duration: 0.7, delay: i * 0.04 }}
                  />
                </div>
                <div className="mt-1 text-right font-mono text-xs font-bold">
                  {c.evidenceScore}%
                </div>

                {c.notes?.trim() && (
                  <p className="mt-2 border-l-3 border-ink pl-2 text-[11px] font-medium italic">
                    &ldquo;{c.notes}&rdquo;
                  </p>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
