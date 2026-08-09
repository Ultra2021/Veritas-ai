'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Check, Dices, FileWarning } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Box from '@/components/ui/Box';
import Reveal from '@/components/ui/Reveal';
import Magnetic from '@/components/ui/Magnetic';
import { CandidateInfo } from '@/types/interview';
import { cn } from '@/lib/utils';

type Level = CandidateInfo['experienceLevel'];
type Mode = CandidateInfo['companyMode'];

const PRESETS: {
  id: string;
  name: string;
  role: string;
  level: Level;
  mode: Mode;
  initials: string;
  bg: string;
}[] = [
  {
    id: 'CAND-001',
    name: 'Sarah Johnson',
    role: 'Senior Data Engineer',
    level: 'Senior',
    mode: 'Startup (Fast & Scrappy)',
    initials: 'SJ',
    bg: 'bg-acid',
  },
  {
    id: 'CAND-002',
    name: 'Alex Turner',
    role: 'Backend Software Engineer',
    level: 'Mid-Level',
    mode: 'OpenAI (AI Architecture & Math)',
    initials: 'AT',
    bg: 'bg-hot text-paper',
  },
  {
    id: 'CAND-003',
    name: 'Emily Chen',
    role: 'AI Engineer',
    level: 'Senior',
    mode: 'Google (Algorithms & Scale)',
    initials: 'EC',
    bg: 'bg-cobalt text-paper',
  },
];

const LEVELS: { value: Level; label: string; yrs: string }[] = [
  { value: 'Junior', label: 'JUNIOR', yrs: '0–2' },
  { value: 'Mid-Level', label: 'MID', yrs: '3–5' },
  { value: 'Senior', label: 'SENIOR', yrs: '5–8' },
  { value: 'Lead / Principal', label: 'LEAD', yrs: '8+' },
];

const MODES: { value: Mode; label: string; desc: string; bg: string }[] = [
  {
    value: 'Startup (Fast & Scrappy)',
    label: 'STARTUP',
    desc: 'Fast & scrappy. Breadth and ownership.',
    bg: 'bg-acid',
  },
  {
    value: 'Google (Algorithms & Scale)',
    label: 'GOOGLE',
    desc: 'Algorithms & scale. Systems rigour.',
    bg: 'bg-sun',
  },
  {
    value: 'Microsoft (Enterprise & Systems)',
    label: 'MICROSOFT',
    desc: 'Enterprise & systems. Maintainability.',
    bg: 'bg-mint',
  },
  {
    value: 'OpenAI (AI Architecture & Math)',
    label: 'OPENAI',
    desc: 'AI architecture & math. First principles.',
    bg: 'bg-violetPop text-paper',
  },
];

export default function CandidateSelectionPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState<CandidateInfo>({
    candidateId: 'CAND-001',
    name: 'Sarah Johnson',
    targetRole: 'Senior Data Engineer',
    experienceLevel: 'Senior',
    companyMode: 'Startup (Fast & Scrappy)',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    if (typeof window !== 'undefined') {
      localStorage.setItem('veritas_candidate', JSON.stringify(form));
      localStorage.removeItem('veritas_session_id');
      localStorage.removeItem('veritas_current_response');
      localStorage.removeItem('veritas_messages');
    }
    router.push('/interview');
  };

  const applyPreset = (p: (typeof PRESETS)[number]) => {
    setForm({
      candidateId: p.id,
      name: p.name,
      targetRole: p.role,
      experienceLevel: p.level,
      companyMode: p.mode,
    });
  };

  const randomise = () => {
    const p = PRESETS[Math.floor(Math.random() * PRESETS.length)];
    applyPreset(p);
  };

  const selectedMode = MODES.find((m) => m.value === form.companyMode) ?? MODES[0];
  const initials =
    form.name
      .split(' ')
      .filter(Boolean)
      .map((w) => w[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || '??';

  return (
    <div className="min-h-screen">
      <Navbar currentStep="select" candidateName={form.name} />

      <main id="main" className="mx-auto max-w-[1600px] px-4 py-10 sm:px-6">
        {/* Header */}
        <Reveal>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <span className="label bg-cobalt">STEP 01 / 03</span>
              <h1 className="mt-3 display text-[clamp(2.4rem,8vw,6rem)]">
                WHO&apos;S ON
                <br />
                <span className="text-hot">THE STAND?</span>
              </h1>
            </div>
            <button onClick={randomise} className="btn btn-paper text-xs">
              <Dices className="h-4 w-4" strokeWidth={3} />
              SURPRISE ME
            </button>
          </div>
        </Reveal>

        <div className="mt-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          {/* ---------- LEFT ---------- */}
          <div className="space-y-6">
            {/* Presets */}
            <Reveal>
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <span className="label">PRESETS</span>
                  <span className="font-mono text-xs font-bold text-smoke">
                    — pick a file
                  </span>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  {PRESETS.map((p, i) => {
                    const active = form.candidateId === p.id;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => applyPreset(p)}
                        aria-pressed={active}
                        className={cn(
                          'group relative border-3 border-ink p-4 text-left transition-all duration-150',
                          active
                            ? 'bg-ink text-paper shadow-brutal-lg'
                            : cn(p.bg, 'shadow-brutal hover:-translate-y-1 hover:shadow-brutal-lg'),
                          i === 1 && 'sm:rotate-1',
                          i === 2 && 'sm:-rotate-1'
                        )}
                      >
                        <div className="flex items-start justify-between">
                          <span
                            className={cn(
                              'flex h-12 w-12 items-center justify-center border-3 border-ink font-display text-lg',
                              active ? 'bg-acid text-ink' : 'bg-paper text-ink'
                            )}
                          >
                            {p.initials}
                          </span>
                          {active && (
                            <span className="border-3 border-paper bg-acid p-1">
                              <Check className="h-4 w-4 text-ink" strokeWidth={4} />
                            </span>
                          )}
                        </div>
                        <div className="mt-3 font-display text-lg leading-tight">
                          {p.name}
                        </div>
                        <div className="font-mono text-[10px] font-bold opacity-70">
                          {p.id}
                        </div>
                        <div className="mt-1 text-xs font-medium">{p.role}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </Reveal>

            {/* Form */}
            <Reveal delay={0.08}>
              <Box shadow="lg" as="section" className="p-5 sm:p-7">
                <form onSubmit={handleSubmit} className="space-y-7">
                  <div className="grid gap-5 sm:grid-cols-2">
                    <div>
                      <label htmlFor="cid" className="label mb-2 block w-fit">
                        FILE NO.
                      </label>
                      <input
                        id="cid"
                        type="text"
                        required
                        value={form.candidateId}
                        onChange={(e) => setForm({ ...form, candidateId: e.target.value })}
                        placeholder="CAND-001"
                        className="field font-mono font-bold"
                      />
                    </div>
                    <div>
                      <label htmlFor="nm" className="label mb-2 block w-fit">
                        NAME
                      </label>
                      <input
                        id="nm"
                        type="text"
                        required
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="Sarah Johnson"
                        className="field"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="role" className="label mb-2 block w-fit">
                      TARGET ROLE
                    </label>
                    <input
                      id="role"
                      type="text"
                      required
                      value={form.targetRole}
                      onChange={(e) => setForm({ ...form, targetRole: e.target.value })}
                      placeholder="Senior Data Engineer"
                      className="field"
                    />
                  </div>

                  {/* Level */}
                  <div>
                    <span className="label mb-2 block w-fit">EXPERIENCE</span>
                    <div
                      role="radiogroup"
                      aria-label="Experience level"
                      className="grid grid-cols-2 border-3 border-ink sm:grid-cols-4"
                    >
                      {LEVELS.map((l, i) => {
                        const active = form.experienceLevel === l.value;
                        return (
                          <button
                            key={l.value}
                            type="button"
                            role="radio"
                            aria-checked={active}
                            onClick={() => setForm({ ...form, experienceLevel: l.value })}
                            className={cn(
                              'px-3 py-3 text-center transition-colors duration-150',
                              i > 0 && 'border-l-3 border-ink',
                              i < 2 && 'border-b-3 border-ink sm:border-b-0',
                              active ? 'bg-ink text-paper' : 'bg-paper hover:bg-acid'
                            )}
                          >
                            <div className="font-display text-base">{l.label}</div>
                            <div className="font-mono text-[10px] font-bold opacity-70">
                              {l.yrs} yrs
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Mode */}
                  <div>
                    <span className="label mb-2 block w-fit">EVALUATION LENS</span>
                    <div
                      role="radiogroup"
                      aria-label="Company evaluation mode"
                      className="grid gap-3 sm:grid-cols-2"
                    >
                      {MODES.map((m) => {
                        const active = form.companyMode === m.value;
                        return (
                          <button
                            key={m.value}
                            type="button"
                            role="radio"
                            aria-checked={active}
                            onClick={() => setForm({ ...form, companyMode: m.value })}
                            className={cn(
                              'border-3 border-ink p-3 text-left transition-all duration-150',
                              active
                                ? 'bg-ink text-paper shadow-brutal'
                                : cn(m.bg, 'hover:-translate-y-0.5 hover:shadow-brutal')
                            )}
                          >
                            <div className="font-display text-lg">{m.label}</div>
                            <div className="mt-0.5 text-[11px] font-medium leading-snug">
                              {m.desc}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <Magnetic className="block w-full">
                    <button
                      type="submit"
                      disabled={submitting}
                      className="btn btn-hot w-full py-5 text-base"
                    >
                      {submitting ? 'OPENING FILE…' : 'BEGIN INTERROGATION'}
                      <ArrowRight className="h-5 w-5" strokeWidth={3} />
                    </button>
                  </Magnetic>
                </form>
              </Box>
            </Reveal>
          </div>

          {/* ---------- RIGHT: dossier ---------- */}
          <Reveal delay={0.14} from="right">
            <aside className="lg:sticky lg:top-28">
              <Box shadow="xl" className="overflow-hidden">
                <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
                  <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
                    CASE FILE
                  </span>
                  <span className="font-mono text-[11px] font-bold text-acid">OPEN</span>
                </div>

                <div className="space-y-4 p-5">
                  <div className="flex items-center gap-4">
                    <span className="flex h-16 w-16 shrink-0 items-center justify-center border-3 border-ink bg-acid font-display text-2xl">
                      {initials}
                    </span>
                    <div className="min-w-0">
                      <AnimatePresence mode="wait">
                        <motion.div
                          key={form.name}
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 8 }}
                          transition={{ duration: 0.18 }}
                          className="truncate font-display text-2xl leading-tight"
                        >
                          {form.name || 'UNNAMED'}
                        </motion.div>
                      </AnimatePresence>
                      <div className="truncate font-mono text-xs font-bold text-smoke">
                        {form.candidateId || '—'}
                      </div>
                    </div>
                  </div>

                  <div className="border-t-3 border-dashed border-ink pt-4">
                    <dl className="space-y-3">
                      {[
                        { k: 'ROLE', v: form.targetRole || '—' },
                        { k: 'LEVEL', v: form.experienceLevel },
                        { k: 'LENS', v: selectedMode.label },
                      ].map((row) => (
                        <div key={row.k} className="flex items-baseline justify-between gap-3">
                          <dt className="font-mono text-[10px] font-bold uppercase tracking-widest text-smoke">
                            {row.k}
                          </dt>
                          <dd className="max-w-[62%] truncate text-right font-display text-sm uppercase">
                            {row.v}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </div>

                  <div className={cn('border-3 border-ink p-3', selectedMode.bg)}>
                    <div className="font-mono text-[10px] font-bold uppercase tracking-widest">
                      POSTURE
                    </div>
                    <p className="mt-1 text-xs font-bold leading-snug">{selectedMode.desc}</p>
                  </div>

                  <div className="flex items-start gap-2 border-3 border-ink bg-sun p-3">
                    <FileWarning className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={3} />
                    <p className="text-[11px] font-bold leading-snug">
                      Starting a new file wipes the previous transcript and evidence from
                      this browser.
                    </p>
                  </div>
                </div>
              </Box>
            </aside>
          </Reveal>
        </div>
      </main>
    </div>
  );
}
