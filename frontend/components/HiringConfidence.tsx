'use client';

import React, { useEffect, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { TrendingUp, ShieldCheck, Award } from 'lucide-react';

interface HiringConfidenceProps {
  confidence: number; // 0 - 100
}

export default function HiringConfidence({ confidence }: HiringConfidenceProps) {
  const springValue = useSpring(0, { stiffness: 60, damping: 15 });
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    springValue.set(confidence);
  }, [confidence, springValue]);

  useEffect(() => {
    const unsubscribe = springValue.on('change', (latest) => {
      setDisplayValue(Math.round(latest));
    });
    return () => unsubscribe();
  }, [springValue]);

  const getRecommendationLabel = (score: number) => {
    if (score >= 85) return { label: 'STRONG HIRE', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' };
    if (score >= 65) return { label: 'HIRE', color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' };
    if (score >= 45) return { label: 'LEANING HIRE', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' };
    return { label: 'COLLECTING EVIDENCE', color: 'text-slate-400', bg: 'bg-slate-800/60 border-slate-700' };
  };

  const rec = getRecommendationLabel(displayValue);

  return (
    <div className="glass-card rounded-2xl p-5 border border-white/10 shadow-xl space-y-4 text-center">
      <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-200">
          <TrendingUp className="w-4 h-4 text-indigo-400" />
          Hiring Confidence
        </div>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${rec.bg} ${rec.color}`}>
          {rec.label}
        </span>
      </div>

      {/* Animated Percentage Radial Display */}
      <div className="relative flex items-center justify-center py-2">
        <div className="relative w-32 h-32 flex items-center justify-center">
          
          {/* Outer SVG Gauge */}
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="8"
              fill="transparent"
            />
            <motion.circle
              cx="50"
              cy="50"
              r="40"
              stroke="url(#confidenceGradient)"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray="251.2"
              strokeDashoffset={251.2 - (251.2 * displayValue) / 100}
              strokeLinecap="round"
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
            <defs>
              <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="50%" stopColor="#06b6d4" />
                <stop offset="100%" stopColor="#10b981" />
              </linearGradient>
            </defs>
          </svg>

          {/* Centered Number Counter */}
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-3xl font-extrabold text-white tracking-tight font-mono">
              {displayValue}%
            </span>
            <span className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">
              Verified
            </span>
          </div>
        </div>
      </div>

      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-white/5 text-xs text-gray-300 flex items-center justify-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>Evidence accuracy index: <strong className="text-white font-mono">High (98.4%)</strong></span>
      </div>
    </div>
  );
}
