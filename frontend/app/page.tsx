'use client';

import React from 'react';
import Link from 'next/link';
import Navbar from '../components/Navbar';
import { ShieldCheck, Sparkles, Cpu, Award, ArrowRight, Dna, CheckCircle2, Play, Users, BarChart3, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
      <Navbar currentStep="landing" />

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 flex flex-col items-center justify-center text-center relative overflow-hidden">

        {/* Background Glow Orbs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-600/20 via-cyan-500/15 to-violet-600/20 rounded-full blur-[120px] pointer-events-none" />

        {/* Hero Pill Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-card border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-6 shadow-lg shadow-indigo-500/10"
        >
          <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span>The Next Generation of Technical Recruitment</span>
        </motion.div>

        {/* Heading & Subtitle */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-black text-white tracking-tight max-w-5xl leading-[1.1]"
        >
          VERITAS <span className="text-gradient-cyan">AI</span>
        </motion.h1>

        <motion.h2
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-xl sm:text-2xl font-bold text-gray-300 mt-3 tracking-wide"
        >
          Evidence-Driven AI Interview Platform
        </motion.h2>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-lg sm:text-xl text-indigo-200/90 font-medium italic mt-4 max-w-2xl"
        >
          &quot;Don&apos;t just evaluate answers. Verify skills with evidence.&quot;
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-8 flex flex-col sm:flex-row items-center gap-4"
        >
          <Link
            href="/select"
            className="w-full sm:w-auto flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-base shadow-xl shadow-indigo-600/30 border border-indigo-300/30 transition-all hover:scale-[1.03] group"
          >
            <Play className="w-5 h-5 fill-white" />
            <span>Start Interview</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>

          <Link
            href="/interview"
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-4 rounded-2xl glass-panel hover:bg-slate-800/80 text-gray-300 hover:text-white font-semibold text-base border border-white/10 transition-all"
          >
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Try Live Demo Interview</span>
          </Link>
        </motion.div>

        {/* Live Concept Feature Card Grid */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-16 w-full grid grid-cols-1 md:grid-cols-3 gap-6 text-left"
        >
          {/* Card 1: Adaptive Verification */}
          <div className="glass-card rounded-3xl p-6 border border-white/10 shadow-xl hover:border-cyan-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Adaptive Evidence Engine</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Veritas AI conducts dynamic multi-turn conversations that deep-dive into candidate responses, asking targeted follow-ups to prove real technical mastery.
            </p>
            <div className="pt-2 flex items-center gap-2 text-xs text-cyan-400 font-medium">
              <span>Live Skill Bars & Logs</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Card 2: 5-Vector Interview DNA */}
          <div className="glass-card rounded-3xl p-6 border border-white/10 shadow-xl hover:border-violet-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-500/10 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <Dna className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">5-Vector Interview DNA</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Generates a holistic radar score across Technical Depth, Communication, Problem Solving, Leadership, and Learning Agility.
            </p>
            <div className="pt-2 flex items-center gap-2 text-xs text-violet-400 font-medium">
              <span>Radar Visualization</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Card 3: Real Recruiter Confidence */}
          <div className="glass-card rounded-3xl p-6 border border-white/10 shadow-xl hover:border-emerald-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Award className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Hiring Confidence Index</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Eliminates bias with smooth, data-backed confidence score tracking that updates after every single answer with evidence-backed reasoning.
            </p>
            <div className="pt-2 flex items-center gap-2 text-xs text-emerald-400 font-medium">
              <span>Verified Recommendation</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </motion.div>

        {/* Floating Demo Banner */}
        <div className="mt-12 w-full p-4 rounded-2xl glass-panel border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-300">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
            <span className="text-left">
              <strong>Hackathon Ready:</strong> Communicates skill verification clearly through live animations and real-time evidence sidebars.
            </span>
          </div>
          <Link
            href="/select"
            className="shrink-0 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-md"
          >
            Launch Interview Flow →
          </Link>
        </div>

      </main>
    </div>
  );
}
