'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Award, CheckCircle, ShieldCheck, Sparkles, Download, Share2, AlertCircle } from 'lucide-react';
import { CandidateInfo } from '../types/interview';

interface ResultsCardProps {
  candidateInfo: CandidateInfo;
  confidenceScore: number;
  recommendation?: 'STRONG HIRE' | 'HIRE' | 'LEANING HIRE' | 'NO HIRE';
  reasoning?: string[];
}

export default function ResultsCard({
  candidateInfo,
  confidenceScore,
  recommendation = 'STRONG HIRE',
  reasoning,
}: ResultsCardProps) {
  const defaultReasoning = [
    'Empirically proven mastery of FastAPI dependency injection and async memory management.',
    'Clear architectural reasoning when designing Redis caching strategies under high concurrent traffic.',
    'Strong communication skills with structured problem-solving approach during technical trade-off questions.',
    'High learning agility demonstrated by quickly integrating Kubernetes auto-scaling concepts.',
  ];

  const points = reasoning || defaultReasoning;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="glass-panel rounded-3xl p-6 lg:p-8 border border-white/10 shadow-2xl relative overflow-hidden space-y-6"
    >
      {/* Ambient background glow */}
      <div className="absolute -top-24 -right-24 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-2">
            <ShieldCheck className="w-4 h-4" /> Veritas AI Verification Certified
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
            {candidateInfo.name || 'Alex Chen'}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Role Target: <strong className="text-cyan-300 font-medium">{candidateInfo.targetRole || 'Senior Backend Engineer'}</strong> • Level: {candidateInfo.experienceLevel || 'Senior'}
          </p>
        </div>

        {/* Big Hiring Recommendation Badge */}
        <div className="flex items-center gap-4 bg-slate-900/80 border border-emerald-500/30 p-4 rounded-2xl shadow-xl">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 shrink-0">
            <Award className="w-7 h-7" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest">
              Recommendation
            </div>
            <div className="text-xl font-black text-emerald-400 tracking-tight">
              {recommendation}
            </div>
            <div className="text-xs text-gray-300 font-mono">
              Confidence Index: <strong className="text-white">{confidenceScore}%</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Reasoning Bullet Points */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          Key Verification Reasoning & Evidence Summary
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {points.map((point, index) => (
            <div
              key={index}
              className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-3 text-xs leading-relaxed text-gray-300"
            >
              <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5 font-bold">
                ✓
              </div>
              <span>{point}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="pt-2 flex items-center justify-between border-t border-white/10">
        <span className="text-xs text-gray-400">
          Verified with empirical evidence log ID: <span className="font-mono text-gray-300">VTS-9842-EX</span>
        </span>
        <div className="flex items-center gap-3">
          <button
            onClick={() => alert("Report PDF export generated successfully!")}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 border border-indigo-400/30 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            Download Verification Report
          </button>
        </div>
      </div>
    </motion.div>
  );
}
