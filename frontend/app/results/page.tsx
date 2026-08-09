'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowLeft, RotateCcw } from 'lucide-react';
import Navbar from '@/components/Navbar';
import ResultsCard from '@/components/ResultsCard';
import VerifiedSkills from '@/components/VerifiedSkills';
import InterviewDNA from '@/components/InterviewDNA';
import GrowthMap from '@/components/GrowthMap';
import Reveal from '@/components/ui/Reveal';
import Counter from '@/components/ui/Counter';
import Marquee from '@/components/ui/Marquee';
import { useInterview } from '@/hooks/useInterview';
import { cn } from '@/lib/utils';

/** Confetti burst — pure CSS squares, fired once on a strong verdict. */
function Confetti({ fire }: { fire: boolean }) {
  const reduce = useReducedMotion();
  const bits = useMemo(
    () =>
      Array.from({ length: 40 }).map((_, i) => ({
        id: i,
        x: Math.random() * 100,
        delay: Math.random() * 0.4,
        dur: 1.8 + Math.random() * 1.4,
        rot: Math.random() * 720 - 360,
        color: ['bg-acid', 'bg-hot', 'bg-cobalt', 'bg-sun', 'bg-mint'][i % 5],
        size: 8 + Math.random() * 10,
      })),
    []
  );

  if (!fire || reduce) return null;

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-[60] overflow-hidden">
      {bits.map((b) => (
        <motion.span
          key={b.id}
          className={cn('absolute top-0 border-2 border-ink', b.color)}
          style={{ left: `${b.x}%`, width: b.size, height: b.size }}
          initial={{ y: -40, opacity: 1, rotate: 0 }}
          animate={{ y: '105vh', opacity: [1, 1, 0], rotate: b.rot }}
          transition={{ duration: b.dur, delay: b.delay, ease: 'linear' }}
        />
      ))}
    </div>
  );
}

export default function ResultsPage() {
  const { candidate, currentResponse, restartInterview } = useInterview();
  const [fired, setFired] = useState(false);

  const confidenceScore = currentResponse?.hiringConfidence;

  const recommendation =
    confidenceScore === null || confidenceScore === undefined
      ? 'COLLECTING EVIDENCE'
      : confidenceScore >= 85
      ? 'STRONG HIRE'
      : confidenceScore >= 65
      ? 'HIRE'
      : confidenceScore >= 45
      ? 'LEANING HIRE'
      : 'COLLECTING EVIDENCE';

  // Fire confetti once for a genuinely strong result.
  useEffect(() => {
    if (
      !fired &&
      confidenceScore !== null &&
      confidenceScore !== undefined &&
      confidenceScore >= 65
    ) {
      setFired(true);
    }
  }, [confidenceScore, fired]);

  // Findings derived from the real backend payload.
  const reasoningPoints: string[] = [];
  if (currentResponse?.evidence?.reason) {
    reasoningPoints.push(currentResponse.evidence.reason);
  }
  if (currentResponse?.evidence?.strengths?.length) {
    reasoningPoints.push(...currentResponse.evidence.strengths);
  }
  if (currentResponse?.evidence?.gaps?.length) {
    reasoningPoints.push(...currentResponse.evidence.gaps.map((g) => `Gap identified: ${g}`));
  }
  if (currentResponse?.competencies) {
    currentResponse.competencies.forEach((c) => {
      if (c.notes && c.notes.trim()) {
        reasoningPoints.push(`${c.competency}: ${c.notes}`);
      }
    });
  }

  const summary = useMemo(() => {
    const comps = currentResponse?.competencies ?? [];
    const verified = comps.filter((c) => c.status === 'verified').length;
    const followUp = comps.filter((c) => c.status === 'needs_followup').length;
    const avg = comps.length
      ? Math.round(comps.reduce((s, c) => s + (c.evidenceScore || 0), 0) / comps.length)
      : 0;
    return { verified, followUp, total: comps.length, avg };
  }, [currentResponse]);

  const stats = [
    { l: 'CLAIMS', v: summary.total, s: '', bg: 'bg-paper' },
    { l: 'PROVEN', v: summary.verified, s: '', bg: 'bg-mint' },
    { l: 'SHAKY', v: summary.followUp, s: '', bg: 'bg-sun' },
    { l: 'AVG', v: summary.avg, s: '%', bg: 'bg-cobalt text-paper' },
  ];

  return (
    <div className="min-h-screen">
      <Confetti fire={fired} />
      <Navbar currentStep="results" candidateName={candidate.name} />

      <main id="main" className="mx-auto max-w-[1600px] px-4 py-10 sm:px-6">
        {/* header */}
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Link
              href="/interview"
              className="inline-flex items-center gap-1.5 font-mono text-xs font-bold uppercase hover:text-hot"
            >
              <ArrowLeft className="h-3.5 w-3.5" strokeWidth={3} />
              BACK TO THE ROOM
            </Link>
            <h1 className="mt-3 display text-[clamp(2.4rem,8vw,6rem)]">
              THE
              <br />
              <span className="text-hot">VERDICT.</span>
            </h1>
          </div>

          <Link href="/select" onClick={restartInterview} className="btn btn-paper text-xs">
            <RotateCcw className="h-4 w-4" strokeWidth={3} />
            NEW SUBJECT
          </Link>
        </div>

        {/* verdict */}
        <div className="mt-8">
          <ResultsCard
            candidateInfo={candidate}
            confidenceScore={confidenceScore}
            sessionId={currentResponse?.sessionId}
            recommendation={recommendation}
            reasoning={reasoningPoints.length ? reasoningPoints : undefined}
          />
        </div>

        {/* stats strip */}
        <div className="mt-8 grid grid-cols-2 border-3 border-ink shadow-brutal-lg lg:grid-cols-4">
          {stats.map((s, i) => (
            <div
              key={s.l}
              className={cn(
                'border-ink p-5',
                s.bg,
                i < 3 && 'lg:border-r-3',
                i % 2 === 0 && 'border-r-3 lg:border-r-3',
                i < 2 && 'border-b-3 lg:border-b-0'
              )}
            >
              <div className="font-mono text-[10px] font-bold uppercase tracking-widest">
                {s.l}
              </div>
              <div className="font-display text-4xl leading-none sm:text-5xl">
                <Counter value={s.v} suffix={s.s} />
              </div>
            </div>
          ))}
        </div>

        {/* body */}
        <div className="mt-10 grid items-start gap-10 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-12">
            <Reveal>
              <VerifiedSkills competencies={currentResponse?.competencies} />
            </Reveal>
            <Reveal>
              <GrowthMap competencies={currentResponse?.competencies} />
            </Reveal>
          </div>

          <div className="space-y-6 lg:sticky lg:top-28">
            <Reveal from="right">
              <InterviewDNA dna={currentResponse?.interviewDNA} />
            </Reveal>

            <Reveal from="right" delay={0.08}>
              <div className="border-3 border-ink bg-acid p-5 shadow-brutal-md">
                <h4 className="font-display text-xl uppercase">NO VIBES INVOLVED</h4>
                <p className="mt-2 text-xs font-bold leading-relaxed">
                  Every number here traces to something the candidate actually said. No
                  résumé keywords, no names, no demographics.
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </main>

      <div className="mt-12 border-y-3 border-ink bg-ink py-2.5 text-paper">
        <Marquee
          items={['EVIDENCE OR IT DIDN\u2019T HAPPEN', 'RECEIPTS ONLY', 'PROVE IT']}
          speed={30}
          separator="●"
        />
      </div>

      <footer className="bg-bone">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-7 sm:px-6">
          <span className="font-display text-2xl">VERITAS</span>
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-smoke">
            Report generated from verified evidence
          </span>
        </div>
      </footer>
    </div>
  );
}
