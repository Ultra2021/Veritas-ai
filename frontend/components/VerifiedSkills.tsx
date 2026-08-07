'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, HelpCircle, ShieldCheck, FileCode, ArrowUpRight } from 'lucide-react';
import { SkillDetail } from '../types/interview';

interface VerifiedSkillsProps {
  skills: SkillDetail[];
}

export default function VerifiedSkills({ skills }: VerifiedSkillsProps) {
  const getBadge = (status: SkillDetail['status']) => {
    switch (status) {
      case 'Verified':
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            ✔ Verified
          </span>
        );
      case 'Partial':
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5" />
            ⚠ Partial
          </span>
        );
      case 'Needs More Evidence':
      default:
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-slate-400 bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-full">
            <HelpCircle className="w-3.5 h-3.5" />
            Needs Evidence
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Verified Skills Breakdown
        </h3>
        <span className="text-xs text-gray-400 font-mono">
          {skills.filter((s) => s.status === 'Verified').length} / {skills.length} Skills Proven
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {skills.map((skill, idx) => (
          <motion.div
            key={skill.name}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1, duration: 0.3 }}
            className="glass-card rounded-2xl p-5 border border-white/10 shadow-xl space-y-3 hover:border-indigo-500/40"
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  {skill.name}
                </h4>
                <div className="text-xs text-gray-400 mt-0.5">
                  Confidence Score: <strong className="text-cyan-300 font-mono">{skill.score}%</strong>
                </div>
              </div>
              {getBadge(skill.status)}
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-white/5">
              <div
                className={`h-full transition-all duration-500 ${
                  skill.status === 'Verified'
                    ? 'bg-gradient-to-r from-emerald-500 to-cyan-400'
                    : skill.status === 'Partial'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-400'
                    : 'bg-slate-700'
                }`}
                style={{ width: `${skill.score}%` }}
              />
            </div>

            {/* Empirical Evidence snippet */}
            {skill.evidenceSnippet && (
              <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 text-xs text-gray-300 space-y-1">
                <div className="flex items-center gap-1.5 text-[11px] font-medium text-cyan-400">
                  <FileCode className="w-3.5 h-3.5" />
                  Empirical Evidence Logged:
                </div>
                <p className="italic text-gray-400 font-mono text-[11px]">
                  &quot;{skill.evidenceSnippet}&quot;
                </p>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
