'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, Cpu, Sparkles, CheckCircle2 } from 'lucide-react';

interface NavbarProps {
  currentStep?: 'landing' | 'select' | 'interview' | 'results';
  candidateName?: string;
}

export default function Navbar({ currentStep = 'landing', candidateName }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 glass-panel px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">

        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#0b0f19] rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-cyan-400 group-hover:rotate-6 transition-transform" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white group-hover:text-cyan-300 transition-colors">
                VERITAS <span className="text-indigo-400 font-extrabold">AI</span>
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                PRO
              </span>
            </div>
            <p className="text-xs text-gray-400 hidden sm:block">
              Evidence-Driven AI Interview Verification
            </p>
          </div>
        </Link>

        {/* Dynamic Context Header */}
        <div className="flex items-center gap-4">
          {currentStep === 'interview' && candidateName && (
            <div className="hidden md:flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-indigo-950/50 border border-indigo-500/30 text-xs">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-gray-300">Live Interviewing: <strong className="text-white font-medium">{candidateName}</strong></span>
            </div>
          )}

          {currentStep === 'results' && (
            <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
              <CheckCircle2 className="w-4 h-4" />
              Evaluation Completed
            </div>
          )}

          <Link
            href="/select"
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/20 border border-indigo-400/30 transition-all hover:shadow-indigo-500/40"
          >
            <Sparkles className="w-3.5 h-3.5" />
            New Assessment
          </Link>
        </div>
      </div>
    </header>
  );
}
