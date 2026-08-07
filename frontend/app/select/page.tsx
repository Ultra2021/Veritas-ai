'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/Navbar';
import { User, Briefcase, Award, Building2, Play, Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import { CandidateInfo } from '../../types/interview';

export default function CandidateSelectionPage() {
  const router = useRouter();

  const [form, setForm] = useState<CandidateInfo>({
    name: 'Alex Chen',
    targetRole: 'Senior Full-Stack Engineer',
    experienceLevel: 'Senior',
    companyMode: 'Startup (Fast & Scrappy)',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== 'undefined') {
      localStorage.setItem('veritas_candidate', JSON.stringify(form));
    }
    router.push('/interview');
  };

  const applyPreset = (role: string, level: CandidateInfo['experienceLevel'], company: CandidateInfo['companyMode']) => {
    setForm((prev) => ({
      ...prev,
      targetRole: role,
      experienceLevel: level,
      companyMode: company,
    }));
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col">
      <Navbar currentStep="select" />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 flex flex-col justify-center w-full">
        
        {/* Page Title */}
        <div className="text-center space-y-2 mb-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Step 1 of 3: Assessment Configuration
          </motion.div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Configure Candidate Verification
          </h1>
          <p className="text-sm text-gray-400 max-w-md mx-auto">
            Set target role parameters and evaluation mode for adaptive AI skill verification.
          </p>
        </div>

        {/* Quick Demo Presets */}
        <div className="mb-6 space-y-2">
          <div className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Demo Quick Presets:
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => applyPreset('Senior Backend Engineer', 'Senior', 'Startup (Fast & Scrappy)')}
              className="glass-card p-3 rounded-xl border border-white/10 text-left hover:border-indigo-500/40 transition-all text-xs"
            >
              <div className="font-bold text-white">Startup Backend Lead</div>
              <div className="text-[11px] text-gray-400">FastAPI • Async • Redis</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('AI Infrastructure Engineer', 'Senior', 'OpenAI (AI Architecture & Math)')}
              className="glass-card p-3 rounded-xl border border-white/10 text-left hover:border-violet-500/40 transition-all text-xs"
            >
              <div className="font-bold text-white">AI Systems Specialist</div>
              <div className="text-[11px] text-gray-400">Python • PyTorch • GPU Scale</div>
            </button>

            <button
              type="button"
              onClick={() => applyPreset('Staff Distributed Systems Engineer', 'Lead / Principal', 'Google (Algorithms & Scale)')}
              className="glass-card p-3 rounded-xl border border-white/10 text-left hover:border-cyan-500/40 transition-all text-xs"
            >
              <div className="font-bold text-white">Google Scale Principal</div>
              <div className="text-[11px] text-gray-400">Distributed • K8s • Microservices</div>
            </button>
          </div>
        </div>

        {/* Form Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass-panel rounded-3xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6"
        >
          <form onSubmit={handleSubmit} className="space-y-5">
            
            {/* Candidate Name */}
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <User className="w-4 h-4 text-indigo-400" />
                Candidate Name
              </label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Alex Chen"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-white/15 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm transition-all"
              />
            </div>

            {/* Target Role */}
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-cyan-400" />
                Target Role
              </label>
              <input
                type="text"
                required
                value={form.targetRole}
                onChange={(e) => setForm({ ...form, targetRole: e.target.value })}
                placeholder="e.g. Senior Backend Engineer"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-white/15 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm transition-all"
              />
            </div>

            {/* Grid for Dropdowns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Experience Level */}
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                  <Award className="w-4 h-4 text-emerald-400" />
                  Experience Level
                </label>
                <select
                  value={form.experienceLevel}
                  onChange={(e) =>
                    setForm({ ...form, experienceLevel: e.target.value as CandidateInfo['experienceLevel'] })
                  }
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-white/15 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all"
                >
                  <option value="Junior">Junior (0-2 years)</option>
                  <option value="Mid-Level">Mid-Level (3-5 years)</option>
                  <option value="Senior">Senior (5-8 years)</option>
                  <option value="Lead / Principal">Lead / Principal (8+ years)</option>
                </select>
              </div>

              {/* Company Mode */}
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-violet-400" />
                  Company Evaluation Mode (Optional)
                </label>
                <select
                  value={form.companyMode}
                  onChange={(e) =>
                    setForm({ ...form, companyMode: e.target.value as CandidateInfo['companyMode'] })
                  }
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-white/15 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all"
                >
                  <option value="Startup (Fast & Scrappy)">Startup (Fast & Scrappy)</option>
                  <option value="Google (Algorithms & Scale)">Google (Algorithms & Scale)</option>
                  <option value="Microsoft (Enterprise & Systems)">Microsoft (Enterprise & Systems)</option>
                  <option value="OpenAI (AI Architecture & Math)">OpenAI (AI Architecture & Math)</option>
                </select>
              </div>

            </div>

            {/* Start Button */}
            <div className="pt-4">
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-3 py-4 px-6 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-extrabold text-base shadow-xl shadow-indigo-600/30 border border-indigo-400/30 transition-all hover:scale-[1.01]"
              >
                <Play className="w-5 h-5 fill-white" />
                <span>Start Adaptive AI Interview</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>

          </form>
        </motion.div>
      </main>
    </div>
  );
}
