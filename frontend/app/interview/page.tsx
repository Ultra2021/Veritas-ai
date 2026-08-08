'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/Navbar';
import ChatWindow from '../../components/ChatWindow';
import AnswerInput from '../../components/AnswerInput';
import EvidenceGraph from '../../components/EvidenceGraph';
import HiringConfidence from '../../components/HiringConfidence';
import InterviewDNA from '../../components/InterviewDNA';
import { useInterview } from '../../hooks/useInterview';
import { ShieldCheck, CheckCircle2, ArrowRight, RotateCcw, AlertCircle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

export default function InterviewPage() {
  const router = useRouter();
  const {
    candidate,
    messages,
    isLoading,
    isStarting,
    error,
    currentResponse,
    submitAnswer,
    restartInterview,
    getSkillDetails,
  } = useInterview();

  const handleAnswerSubmit = async (answerText: string) => {
    await submitAnswer(answerText);
  };

  const handleFinishAndSeeResults = () => {
    router.push('/results');
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
      <Navbar currentStep="interview" candidateName={candidate.name} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* CENTER & LEFT: Chat Interface (7 or 8 columns on large screens) */}
        <section className="lg:col-span-7 xl:col-span-8 flex flex-col h-[calc(100vh-120px)] min-h-[620px] glass-panel rounded-3xl p-4 sm:p-6 border border-white/10 shadow-2xl relative">

          {/* Header Banner */}
          <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-white">{candidate.targetRole} Verification</h2>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {candidate.experienceLevel}
                  </span>
                </div>
                <p className="text-xs text-gray-400">
                  Target Candidate: <strong className="text-gray-200">{candidate.name}</strong> ({candidate.candidateId}) • Mode: {candidate.companyMode}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={restartInterview}
                title="Restart Session"
                className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-gray-400 hover:text-white border border-white/10 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Backend Error Banner */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between gap-4 text-rose-300 text-xs shadow-lg shadow-rose-500/10"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                <span>
                  <strong>API Error:</strong> {error}
                </span>
              </div>
              <button
                onClick={restartInterview}
                className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shadow-md transition-all text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry
              </button>
            </motion.div>
          )}

          {/* If interview completed banner */}
          {currentResponse?.done && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between gap-4 text-emerald-300 text-xs shadow-lg shadow-emerald-500/10"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>
                  <strong>Assessment Completed!</strong> Veritas AI has accumulated sufficient evidence to verify your skill spectrum.
                </span>
              </div>
              <button
                onClick={handleFinishAndSeeResults}
                className="shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold shadow-md transition-all"
              >
                <span>View Full Results Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}

          {/* Conversation History Window */}
          <ChatWindow messages={messages} isAiThinking={isLoading || isStarting} />

          {/* Bottom Answer Input */}
          <div className="pt-3 border-t border-white/10 mt-auto">
            <AnswerInput
              onSend={handleAnswerSubmit}
              isLoading={isLoading || isStarting}
              disabled={currentResponse?.done || !!error}
            />
          </div>
        </section>

        {/* RIGHT: Live Evidence & Confidence Sidebar (4 or 5 columns) */}
        <aside className="lg:col-span-5 xl:col-span-4 space-y-5 overflow-y-auto max-h-[calc(100vh-120px)] custom-scrollbar pr-1">

          {/* 1. Live Hiring Confidence Gauge */}
          <HiringConfidence confidence={currentResponse?.hiringConfidence} />

          {/* 2. Live Skill Competency Bars */}
          <EvidenceGraph
            skills={getSkillDetails().map((s) => ({
              name: s.name,
              status: s.status,
              score: s.score,
            }))}
            currentSkill={currentResponse?.currentCompetency || undefined}
          />

          {/* 3. Live 5-Axis Interview DNA Preview */}
          <InterviewDNA dna={currentResponse?.interviewDNA} compact={true} />

          {/* View Full Assessment Button if done */}
          {currentResponse?.done && (
            <button
              onClick={handleFinishAndSeeResults}
              className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-black text-sm shadow-xl shadow-emerald-500/20 transition-all hover:scale-[1.02]"
            >
              <span>Explore Final Assessment Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </aside>

      </main>
    </div>
  );
}
