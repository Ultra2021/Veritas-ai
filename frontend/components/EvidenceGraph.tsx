'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { SkillStatus } from '@/types/interview';
import { cn } from '@/lib/utils';

export interface EvidenceSkillItem {
  name: string;
  status: SkillStatus;
  score: number; // 0-100
}

interface EvidenceGraphProps {
  skills: EvidenceSkillItem[];
  currentSkill?: string;
}

const STATUS: Record<SkillStatus, { tag: string; bg: string; bar: string }> = {
  Verified: { tag: 'PROVEN', bg: 'bg-mint', bar: 'bg-mint' },
  Partial: { tag: 'SHAKY', bg: 'bg-sun', bar: 'bg-sun' },
  'Needs More Evidence': { tag: 'UNPROVEN', bg: 'bg-sand', bar: 'bg-sand' },
};

export default function EvidenceGraph({ skills, currentSkill }: EvidenceGraphProps) {
  const proven = skills.filter((s) => s.status === 'Verified').length;

  return (
    <div className="border-3 border-ink bg-paper shadow-brutal-md">
      <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
          EVIDENCE LEDGER
        </span>
        <span className="font-mono text-[11px] font-bold text-acid">
          {proven}/{skills.length}
        </span>
      </div>

      <div className="divide-y-3 divide-ink">
        {skills.length === 0 && (
          <p className="p-6 text-center font-mono text-xs font-bold uppercase text-smoke">
            Nothing on record yet
          </p>
        )}

        {skills.map((skill, i) => {
          const meta = STATUS[skill.status] ?? STATUS['Needs More Evidence'];
          const active = currentSkill === skill.name;

          return (
            <div
              key={skill.name || i}
              className={cn('p-3 transition-colors', active && 'bg-acid/30')}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="min-w-0 flex-1 text-xs font-bold leading-snug">
                  {active && <span className="mr-1 animate-blink">▶</span>}
                  {skill.name}
                </span>
                <span
                  className={cn(
                    'shrink-0 border-2 border-ink px-1.5 py-0.5 font-mono text-[9px] font-bold',
                    meta.bg
                  )}
                >
                  {meta.tag}
                </span>
              </div>

              {/* stepped bar */}
              <div className="mt-2 flex h-4 gap-0.5 border-2 border-ink bg-paper p-0.5">
                {Array.from({ length: 10 }).map((_, seg) => (
                  <motion.div
                    key={seg}
                    className={cn(
                      'flex-1 border border-ink/20',
                      seg < Math.round(skill.score / 10) ? meta.bar : 'bg-transparent'
                    )}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: seg * 0.03 }}
                  />
                ))}
              </div>
              <div className="mt-1 text-right font-mono text-[10px] font-bold text-smoke">
                {skill.score}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
