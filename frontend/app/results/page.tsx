'use client';

import React from 'react';
import Link from 'next/link';
import Navbar from '../../components/Navbar';
import ResultsCard from '../../components/ResultsCard';
import VerifiedSkills from '../../components/VerifiedSkills';
import InterviewDNA from '../../components/InterviewDNA';
import GrowthMap from '../../components/GrowthMap';
import { useInterview } from '../../hooks/useInterview';
import { RotateCcw, ArrowLeft, Share2, Sparkles, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ResultsPage() {
  const { candidate, currentResponse, getSkillDetails, restartInterview } = useInterview();

  const skillsList = getSkillDetails();

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
      <Navbar currentStep="results" candidateName={candidate.name} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Top Header Navigation */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link
                href="/interview"
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to Live Session
              </Link>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Evidence Verification Assessment Report
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/select"
              onClick={restartInterview}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl glass-panel hover:bg-slate-800 text-xs font-semibold text-gray-300 hover:text-white border border-white/10 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5 text-indigo-400" />
              Assess Another Candidate
            </Link>
          </div>
        </div>

        {/* 1. ResultsCard (Hiring Recommendation + Reasoning) */}
        <ResultsCard
          candidateInfo={candidate}
          confidenceScore={currentResponse.confidence}
          recommendation={
            currentResponse.confidence >= 85
              ? 'STRONG HIRE'
              : currentResponse.confidence >= 65
              ? 'HIRE'
              : 'LEANING HIRE'
          }
        />

        {/* 2 Grid Layout: Left Verified Skills & Growth Map, Right Interview DNA Radar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column (7 cols) */}
          <div className="lg:col-span-7 space-y-8">
            {/* Verified Skills Grid */}
            <VerifiedSkills skills={skillsList} />

            {/* Growth Map */}
            <GrowthMap />
          </div>

          {/* Right Column (5 cols) */}
          <div className="lg:col-span-5 space-y-6 sticky top-24">
            
            {/* 5-Axis Interview DNA Radar Chart */}
            <InterviewDNA dna={currentResponse.interviewDNA} compact={false} />

            {/* Summary Highlights Panel */}
            <div className="glass-card rounded-2xl p-5 border border-white/10 space-y-4 text-xs text-gray-300">
              <h4 className="font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Anti-Bias Evidence Guarantee
              </h4>
              <p className="leading-relaxed text-gray-400">
                All score vectors are generated strictly from transcript timestamps and empirical code answer evaluation. Zero generic resume keywords were factored into this score.
              </p>
              <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-gray-400">
                <span>Model Engine: Veritas-3.5-v2</span>
                <span className="text-emerald-400 font-bold">100% Audit Verified</span>
              </div>
            </div>

          </div>

        </div>

      </main>
    </div>
  );
}
