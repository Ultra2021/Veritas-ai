'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, HelpCircle, ShieldCheck, FileCode, Clock } from 'lucide-react';
import { CompetencyState, SkillDetail } from '../types/interview';

interface VerifiedSkillsProps {
  competencies?: CompetencyState[];
  skills?: SkillDetail[];
}

export default function VerifiedSkills({ competencies, skills }: VerifiedSkillsProps) {
  // If competencies are provided, use them directly; otherwise fall back to skills prop if available
  const list = competencies || [];
  const verifiedCount = list.filter((c) => c.status === 'verified').length;
  const totalCount = list.length;

  const getStatusBadge = (status: CompetencyState['status']) => {
    switch (status) {
      case 'verified':
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Verified
          </span>
        );
      case 'needs_followup':
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5" />
            Needs Follow-up
          </span>
        );
      case 'in_progress':
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-1 rounded-full">
            <Clock className="w-3.5 h-3.5" />
            In Progress
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="flex items-center gap-1 text-xs font-bold text-slate-400 bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-full">
            <HelpCircle className="w-3.5 h-3.5" />
            Pending
          </span>
        );
    }
  };

  if (list.length === 0 && skills && skills.length > 0) {
    // Legacy fallback for skills prop if competencies array is empty
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
                    Evidence Score: <strong className="text-cyan-300 font-mono">{skill.score}%</strong>
                  </div>
                </div>
              </div>

              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-500"
                  style={{ width: `${skill.score}%` }}
                />
              </div>

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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Verified Competencies Breakdown
        </h3>
        <span className="text-xs text-gray-400 font-mono">
          {verifiedCount} / {totalCount} Skills Proven
        </span>
      </div>

      {list.length === 0 ? (
        <div className="p-6 rounded-2xl glass-card border border-white/10 text-center text-xs text-gray-400 italic">
          No competency evaluations logged yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {list.map((comp, idx) => (
            <motion.div
              key={comp.competency}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05, duration: 0.3 }}
              className="glass-card rounded-2xl p-5 border border-white/10 shadow-xl space-y-3 hover:border-indigo-500/40"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    {comp.competency}
                  </h4>
                  <div className="text-xs text-gray-400 mt-0.5 flex items-center gap-3">
                    <span>
                      Evidence Score: <strong className="text-cyan-300 font-mono">{comp.evidenceScore}%</strong>
                    </span>
                    <span>
                      Attempts: <strong className="text-gray-200 font-mono">{comp.attempts}</strong>
                    </span>
                  </div>
                </div>
                {getStatusBadge(comp.status)}
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-white/5">
                <div
                  className={`h-full transition-all duration-500 ${
                    comp.status === 'verified'
                      ? 'bg-gradient-to-r from-emerald-500 to-cyan-400'
                      : comp.status === 'needs_followup'
                      ? 'bg-gradient-to-r from-amber-500 to-orange-400'
                      : comp.status === 'in_progress'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-500'
                      : 'bg-slate-700'
                  }`}
                  style={{ width: `${comp.evidenceScore}%` }}
                />
              </div>

              {/* Competency Notes if present */}
              {comp.notes && comp.notes.trim().length > 0 && (
                <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 text-xs text-gray-300 space-y-1">
                  <div className="flex items-center gap-1.5 text-[11px] font-medium text-cyan-400">
                    <FileCode className="w-3.5 h-3.5" />
                    Evaluator Notes:
                  </div>
                  <p className="italic text-gray-400 font-mono text-[11px]">
                    &quot;{comp.notes}&quot;
                  </p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
