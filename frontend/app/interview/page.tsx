'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, AlertTriangle, ArrowRight, X, BarChart3 } from 'lucide-react';
import Navbar from '@/components/Navbar';
import ChatWindow from '@/components/ChatWindow';
import AnswerInput from '@/components/AnswerInput';
import EvidenceGraph from '@/components/EvidenceGraph';
import HiringConfidence from '@/components/HiringConfidence';
import InterviewDNA from '@/components/InterviewDNA';
import { useInterview } from '@/hooks/useInterview';
import { cn } from '@/lib/utils';

type Tab = 'score' | 'ledger' | 'dna';

const TABS: { id: Tab; label: string }[] = [
  { id: 'score', label: 'SCORE' },
  { id: 'ledger', label: 'LEDGER' },
  { id: 'dna', label: 'DNA' },
];

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

  const [tab, setTab] = useState<Tab>('score');
  const [panelOpen, setPanelOpen] = useState(false);

  const skills = getSkillDetails();
  const busy = isLoading || isStarting;
  const done = !!currentResponse?.done;
  const evidence = currentResponse?.evidence;

  const stats = useMemo(() => {
    const comps = currentResponse?.competencies ?? [];
    const verified = comps.filter((c) => c.status === 'verified').length;
    return {
      verified,
      total: comps.length,
      pct: comps.length ? Math.round((verified / comps.length) * 100) : 0,
      answers: messages.filter((m) => m.sender === 'candidate').length,
    };
  }, [currentResponse, messages]);

  const panel = (
    <div className="space-y-4">
      {/* tabs */}
      <div className="flex border-3 border-ink">
        {TABS.map((t, i) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            aria-pressed={tab === t.id}
            className={cn(
              'flex-1 px-3 py-2.5 font-display text-sm uppercase transition-colors duration-150',
              i > 0 && 'border-l-3 border-ink',
              tab === t.id ? 'bg-ink text-paper' : 'bg-paper hover:bg-acid'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.2 }}
          className="space-y-4"
        >
          {tab === 'score' && (
            <>
              <HiringConfidence confidence={currentResponse?.hiringConfidence} />

              <div className="grid grid-cols-2 gap-3">
                {[
                  { l: 'ANSWERS', v: stats.answers, bg: 'bg-sun' },
                  { l: 'PROVEN', v: `${stats.verified}/${stats.total}`, bg: 'bg-mint' },
                ].map((s) => (
                  <div key={s.l} className={cn('border-3 border-ink p-3 shadow-brutal', s.bg)}>
                    <div className="font-mono text-[10px] font-bold uppercase tracking-widest">
                      {s.l}
                    </div>
                    <div className="font-display text-3xl leading-none">{s.v}</div>
                  </div>
                ))}
              </div>

              {/* last ruling */}
              {evidence && (
                <div className="border-3 border-ink bg-paper shadow-brutal-md">
                  <div className="border-b-3 border-ink bg-ink px-4 py-2">
                    <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
                      LAST RULING
                    </span>
                  </div>
                  <div className="space-y-3 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-display text-sm uppercase">
                        {evidence.competency}
                      </span>
                      <span
                        className={cn(
                          'shrink-0 border-2 border-ink px-2 py-0.5 font-mono text-[9px] font-bold',
                          evidence.verified ? 'bg-mint' : 'bg-sun'
                        )}
                      >
                        {evidence.verified ? 'PROVEN' : 'NOT YET'}
                      </span>
                    </div>

                    <p className="border-l-3 border-ink pl-2 text-[11px] font-medium leading-snug">
                      {evidence.reason}
                    </p>

                    <div className="grid grid-cols-4 gap-1.5">
                      {[
                        { l: 'TECH', v: evidence.technicalScore },
                        { l: 'LOGIC', v: evidence.reasoningScore },
                        { l: 'FULL', v: evidence.completenessScore },
                        { l: 'COMM', v: evidence.communicationScore },
                      ].map((m) => (
                        <div key={m.l} className="border-2 border-ink bg-sand p-1.5 text-center">
                          <div className="font-mono text-[8px] font-bold">{m.l}</div>
                          <div className="font-display text-base leading-none">{m.v}</div>
                        </div>
                      ))}
                    </div>

                    {evidence.strengths?.length > 0 && (
                      <ul className="space-y-1">
                        {evidence.strengths.slice(0, 3).map((s, i) => (
                          <li key={i} className="text-[11px] font-medium">
                            <span className="font-bold">+</span> {s}
                          </li>
                        ))}
                      </ul>
                    )}
                    {evidence.gaps?.length > 0 && (
                      <ul className="space-y-1">
                        {evidence.gaps.slice(0, 3).map((g, i) => (
                          <li key={i} className="text-[11px] font-medium text-blood">
                            <span className="font-bold">−</span> {g}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {tab === 'ledger' && (
            <EvidenceGraph
              skills={skills.map((s) => ({
                name: s.name,
                status: s.status,
                score: s.score,
              }))}
              currentSkill={currentResponse?.currentCompetency || undefined}
            />
          )}

          {tab === 'dna' && <InterviewDNA dna={currentResponse?.interviewDNA} compact />}
        </motion.div>
      </AnimatePresence>

      {done && (
        <button onClick={() => router.push('/results')} className="btn btn-acid w-full py-4">
          SEE THE VERDICT
          <ArrowRight className="h-4 w-4" strokeWidth={3} />
        </button>
      )}
    </div>
  );

  return (
    <div className="min-h-screen">
      <Navbar currentStep="interview" candidateName={candidate.name} />

      <main
        id="main"
        className="mx-auto grid max-w-[1600px] items-start gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[1.5fr_1fr]"
      >
        {/* ---------- transcript ---------- */}
        <section className="flex h-[calc(100vh-11rem)] min-h-[560px] flex-col border-3 border-ink bg-paper shadow-brutal-lg">
          {/* header */}
          <header className="flex items-start justify-between gap-3 border-b-3 border-ink bg-ink px-4 py-3 text-paper">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="truncate font-display text-lg uppercase leading-none">
                  {candidate.targetRole}
                </h1>
                <span className="border-2 border-paper bg-acid px-1.5 py-0.5 font-mono text-[9px] font-bold text-ink">
                  {candidate.experienceLevel}
                </span>
              </div>
              <p className="mt-1 truncate font-mono text-[10px] font-bold uppercase tracking-wide opacity-70">
                {candidate.name} · {candidate.candidateId}
              </p>
            </div>

            <div className="flex shrink-0 gap-2">
              <button
                onClick={() => setPanelOpen(true)}
                className="flex items-center gap-1.5 border-3 border-paper bg-cobalt px-2.5 py-1.5 font-mono text-[10px] font-bold uppercase lg:hidden"
              >
                <BarChart3 className="h-3.5 w-3.5" strokeWidth={3} />
                STATS
              </button>
              <button
                onClick={restartInterview}
                title="Restart"
                aria-label="Restart session"
                className="flex h-9 w-9 items-center justify-center border-3 border-paper bg-blood text-paper transition-transform hover:rotate-180 duration-300"
              >
                <RotateCcw className="h-4 w-4" strokeWidth={3} />
              </button>
            </div>
          </header>

          {/* progress */}
          {stats.total > 0 && (
            <div className="flex items-center gap-2 border-b-3 border-ink bg-sand px-4 py-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest">
                PROGRESS
              </span>
              <div className="flex h-3 flex-1 gap-0.5 border-2 border-ink bg-paper p-0.5">
                {Array.from({ length: Math.max(stats.total, 1) }).map((_, i) => (
                  <div
                    key={i}
                    className={cn('flex-1', i < stats.verified ? 'bg-mint' : 'bg-sand')}
                  />
                ))}
              </div>
              <span className="font-mono text-[10px] font-bold">
                {stats.verified}/{stats.total}
              </span>
            </div>
          )}

          {/* banners */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b-3 border-ink bg-blood px-4 py-3 text-paper">
                  <span className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase">
                    <AlertTriangle className="h-4 w-4" strokeWidth={3} />
                    {error}
                  </span>
                  <button
                    onClick={restartInterview}
                    className="border-3 border-paper bg-paper px-3 py-1 font-mono text-[10px] font-bold uppercase text-ink"
                  >
                    RETRY
                  </button>
                </div>
              </motion.div>
            )}

            {done && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b-3 border-ink bg-acid px-4 py-3">
                  <span className="font-display text-sm uppercase">
                    ✓ INTERROGATION COMPLETE
                  </span>
                  <button
                    onClick={() => router.push('/results')}
                    className="border-3 border-ink bg-ink px-3 py-1 font-mono text-[10px] font-bold uppercase text-paper"
                  >
                    VERDICT →
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* messages */}
          <div className="flex min-h-0 flex-1 flex-col px-3 py-3">
            <ChatWindow messages={messages} isAiThinking={busy} />
          </div>

          {/* composer */}
          <AnswerInput
            onSubmit={(text) => {
              void submitAnswer(text);
            }}
            disabled={busy || done || !!error}
            placeholder={
              done
                ? 'Interrogation closed.'
                : 'Give specifics. Numbers, names, what broke…'
            }
          />
        </section>

        {/* ---------- desktop panel ---------- */}
        <aside className="hidden max-h-[calc(100vh-11rem)] overflow-y-auto pr-1 lg:block">
          {panel}
        </aside>
      </main>

      {/* ---------- mobile drawer ---------- */}
      <AnimatePresence>
        {panelOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setPanelOpen(false)}
            className="fixed inset-0 z-50 flex items-end bg-ink/50 lg:hidden"
          >
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
              onClick={(e) => e.stopPropagation()}
              className="max-h-[86vh] w-full overflow-y-auto border-t-3 border-ink bg-bone p-4"
            >
              <div className="mb-4 flex items-center justify-between">
                <span className="font-display text-xl uppercase">LIVE STATS</span>
                <button
                  onClick={() => setPanelOpen(false)}
                  aria-label="Close"
                  className="flex h-9 w-9 items-center justify-center border-3 border-ink bg-blood text-paper"
                >
                  <X className="h-4 w-4" strokeWidth={3} />
                </button>
              </div>
              {panel}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
