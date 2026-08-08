'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldCheck, Sparkles, User, FileText, Play } from 'lucide-react';

interface NavbarProps {
  currentStep?: 'landing' | 'select' | 'interview' | 'results';
  candidateName?: string;
}

export default function Navbar({ currentStep = 'landing', candidateName }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full glass-panel border-b border-white/10 px-4 sm:px-8 py-3.5 flex items-center justify-between">
      
      {/* Brand Logo */}
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
          <div className="w-full h-full bg-[#090d16] rounded-[14px] flex items-center justify-center">
            <ShieldCheck className="w-6 h-6 text-cyan-400" />
          </div>
        </div>
        <div>
          <span className="text-lg font-black tracking-wider text-white flex items-center gap-1">
            VERITAS <span className="text-gradient-cyan font-mono text-sm font-extrabold">AI</span>
          </span>
          <span className="text-[10px] text-gray-400 block tracking-widest font-mono -mt-1 uppercase">
            Adaptive Skill Verification
          </span>
        </div>
      </Link>

      {/* Progress Flow Steps */}
      <nav className="hidden md:flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-2xl border border-white/5 text-xs font-medium">
        <Link
          href="/select"
          className={`px-3 py-1.5 rounded-xl transition-all ${
            currentStep === 'select'
              ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          1. Candidate Config
        </Link>
        <span className="text-gray-600 font-bold">•</span>
        <Link
          href="/interview"
          className={`px-3 py-1.5 rounded-xl transition-all ${
            currentStep === 'interview'
              ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          2. Live Verification
        </Link>
        <span className="text-gray-600 font-bold">•</span>
        <Link
          href="/results"
          className={`px-3 py-1.5 rounded-xl transition-all ${
            currentStep === 'results'
              ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          3. Evidence Report
        </Link>
      </nav>

      {/* Candidate Status Indicator */}
      <div className="flex items-center gap-3">
        {candidateName ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-white/10 text-xs">
            <User className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-gray-300 font-medium hidden sm:inline">Active:</span>
            <span className="font-bold text-white max-w-[120px] truncate">{candidateName}</span>
          </div>
        ) : (
          <Link
            href="/select"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition-all hover:scale-105"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Launch Flow</span>
          </Link>
        )}
      </div>
    </header>
  );
}
