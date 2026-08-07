'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, HelpCircle, ShieldAlert, Cpu } from 'lucide-react';
import { SkillStatus } from '../types/interview';

export interface EvidenceSkillItem {
  name: string;
  status: SkillStatus;
  score: number; // 0-100
}

interface EvidenceGraphProps {
  skills: EvidenceSkillItem[];
  currentSkill?: string;
}

export default function EvidenceGraph({ skills, currentSkill }: EvidenceGraphProps) {
  const getStatusBadge = (status: SkillStatus) => {
    switch (status) {
      case 'Verified':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Verified
          </span>
        );
      case 'Partial':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            Partial
          </span>
        );
      case 'Needs More Evidence':
      default:
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 bg-slate-800/80 border border-slate-700 px-2 py-0.5 rounded-full">
            <HelpCircle className="w-3 h-3 text-slate-400" />
            Needs Evidence
          </span>
        );
    }
  };

  const getBarColor = (status: SkillStatus) => {
    switch (status) {
      case 'Verified':
        return 'from-emerald-500 to-cyan-400 shadow-emerald-500/30';
      case 'Partial':
        return 'from-amber-500 to-orange-400 shadow-amber-500/30';
      case 'Needs More Evidence':
      default:
        return 'from-slate-600 to-slate-700';
    }
  };

  return (
    <div className="glass-card rounded-2xl p-4 border border-white/10 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-200">
            Live Evidence Graph
          </h3>
        </div>
        <span className="text-[10px] text-gray-400 bg-slate-800 px-2 py-0.5 rounded-md font-mono">
          {skills.filter((s) => s.status === 'Verified').length}/{skills.length} Verified
        </span>
      </div>

      {currentSkill && (
        <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between text-xs">
          <span className="text-gray-400 font-medium">Active Evaluation:</span>
          <span className="font-semibold text-cyan-300 animate-pulse">{currentSkill}</span>
        </div>
      )}

      <div className="space-y-3.5 pt-1">
        {skills.map((skill, idx) => (
          <div key={skill.name || idx} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-gray-200 flex items-center gap-1.5">
                {skill.name}
              </span>
              {getStatusBadge(skill.status)}
            </div>

            {/* Custom ASCII style progress indicator preview + Smooth Framer Bar */}
            <div className="relative w-full h-2.5 bg-slate-900/90 rounded-full overflow-hidden border border-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${skill.score}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className={`h-full bg-gradient-to-r ${getBarColor(skill.status)} shadow-md rounded-full`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
