'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  ArrowDown,
  Skull,
  Fingerprint,
  Gavel,
  Quote,
  Asterisk,
  CornerDownRight,
} from 'lucide-react';
import Navbar from '@/components/Navbar';
import Box from '@/components/ui/Box';
import Marquee from '@/components/ui/Marquee';
import Reveal from '@/components/ui/Reveal';
import Counter from '@/components/ui/Counter';
import Magnetic from '@/components/ui/Magnetic';
import { cn } from '@/lib/utils';

/* ------------------------------------------------------------------ *
 * Interrogation demo — cycles a claim being torn apart for evidence.
 * ------------------------------------------------------------------ */
const ROUNDS = [
  {
    claim: '"Expert in Kubernetes"',
    probe: 'Name the last production incident you personally debugged.',
    answer: 'Pods OOM-killed during traffic spikes. Traced a leak in the sidecar.',
    verdict: 'EVIDENCE',
    color: 'bg-mint',
    delta: '+18',
  },
  {
    claim: '"Expert in Kubernetes"',
    probe: 'What limit did you set? How did you land on that number?',
    answer: 'Profiled heap over 48h. Requests at p95, limits at p99 + 20%.',
    verdict: 'SPECIFIC',
    color: 'bg-acid',
    delta: '+12',
  },
  {
    claim: '"Expert in Kubernetes"',
    probe: 'Prove the fix held under load.',
    answer: 'Soak test at 3x peak for 6 hours. RSS flattened in Grafana.',
    verdict: 'VERIFIED',
    color: 'bg-cobalt text-paper',
    delta: '+15',
  },
];

function Interrogation() {
  const [i, setI] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const id = setInterval(() => setI((v) => (v + 1) % ROUNDS.length), 4000);
    return () => clearInterval(id);
  }, [reduce]);

  const r = ROUNDS[i];

  return (
    <Box shadow="xl" className="overflow-hidden">
      {/* title bar */}
      <div className="flex items-center justify-between border-b-3 border-ink bg-ink px-4 py-2">
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-paper">
          ► INTERROGATION LOG
        </span>
        <span className="flex gap-1.5">
          <span className="h-3 w-3 border-2 border-paper bg-blood" />
          <span className="h-3 w-3 border-2 border-paper bg-sun" />
          <span className="h-3 w-3 border-2 border-paper bg-mint" />
        </span>
      </div>

      {/* the claim under attack */}
      <div className="flex flex-wrap items-center gap-2 border-b-3 border-ink bg-sand px-4 py-3">
        <span className="label bg-blood">CLAIM</span>
        <span className="font-display text-lg line-through decoration-blood decoration-4">
          {r.claim}
        </span>
      </div>

      <div className="space-y-3 p-4">
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -18 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, ease: [0.34, 1.56, 0.64, 1] }}
          className="space-y-3"
        >
          {/* probe */}
          <div className="flex gap-2">
            <span className="label shrink-0 bg-cobalt">AI</span>
            <p className="border-3 border-ink bg-paper px-3 py-2 font-mono text-xs font-bold">
              {r.probe}
            </p>
          </div>

          {/* answer */}
          <div className="flex justify-end gap-2">
            <p className="border-3 border-ink bg-sun px-3 py-2 text-right text-xs font-medium">
              {r.answer}
            </p>
            <span className="label shrink-0">YOU</span>
          </div>

          {/* verdict */}
          <motion.div
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.25, ease: [0.34, 1.56, 0.64, 1] }}
            className={cn(
              'flex items-center justify-between border-3 border-ink px-3 py-2',
              r.color
            )}
          >
            <span className="font-display text-sm uppercase">✓ {r.verdict}</span>
            <span className="font-mono text-lg font-bold">{r.delta}</span>
          </motion.div>
        </motion.div>

        {/* round pips */}
        <div className="flex gap-1.5 pt-1">
          {ROUNDS.map((_, idx) => (
            <span
              key={idx}
              className={cn(
                'h-2 flex-1 border-2 border-ink transition-colors duration-200',
                idx <= i ? 'bg-ink' : 'bg-paper'
              )}
            />
          ))}
        </div>
      </div>
    </Box>
  );
}

/* ------------------------------------------------------------------ */

const STEPS = [
  {
    n: '01',
    icon: Fingerprint,
    title: 'PROFILE',
    body: 'Pick the role and the claims. We build a map of everything that needs proving.',
    bg: 'bg-acid',
  },
  {
    n: '02',
    icon: Skull,
    title: 'INTERROGATE',
    body: 'The agent hunts the weakest claim and digs until it hits bedrock or bluff.',
    bg: 'bg-hot text-paper',
  },
  {
    n: '03',
    icon: Gavel,
    title: 'VERDICT',
    body: 'A report where every number links back to a direct quote. No vibes.',
    bg: 'bg-cobalt text-paper',
  },
];

const STATS = [
  { v: 5, s: '', l: 'DNA vectors', bg: 'bg-acid' },
  { v: 100, s: '%', l: 'Traced to quotes', bg: 'bg-hot text-paper' },
  { v: 3, s: 'x', l: 'Deeper probing', bg: 'bg-cobalt text-paper' },
  { v: 0, s: '', l: 'Unexplained scores', bg: 'bg-sun' },
];

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const yTitle = useTransform(scrollYProgress, [0, 1], [0, -90]);
  const rotBadge = useTransform(scrollYProgress, [0, 1], [-8, 14]);

  return (
    <div className="min-h-screen">
      <Navbar currentStep="landing" />

      <main id="main">
        {/* ============ HERO ============ */}
        <section ref={heroRef} className="border-b-3 border-ink">
          <div className="mx-auto max-w-[1600px] px-4 pb-16 pt-12 sm:px-6">
            <div className="grid items-start gap-10 lg:grid-cols-[1.15fr_1fr]">
              {/* headline */}
              <motion.div style={{ y: yTitle }}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="label bg-hot">EVIDENCE ENGINE</span>
                  <span className="chip">
                    <Asterisk className="h-3 w-3" strokeWidth={3} />
                    v2.0
                  </span>
                </div>

                <h1 className="mt-5 display text-[clamp(3.2rem,11vw,9rem)]">
                  <span className="block">RÉSUMÉS</span>
                  <span className="block text-blood">LIE.</span>
                  <span className="block outline-text">EVIDENCE</span>
                  <span className="relative inline-block">
                    DOESN&apos;T.
                    <motion.span
                      aria-hidden
                      className="absolute -bottom-1 left-0 h-3 bg-acid"
                      initial={{ width: 0 }}
                      animate={{ width: '100%' }}
                      transition={{ delay: 0.6, duration: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
                    />
                  </span>
                </h1>

                <p className="mt-7 max-w-lg border-l-6 border-ink pl-4 text-base font-medium text-pretty sm:text-lg">
                  VERITAS interrogates every claim on a CV until it produces proof — or
                  collapses. Each score is chained to a direct quote.
                </p>

                <div className="mt-8 flex flex-wrap items-center gap-4">
                  <Magnetic>
                    <Link href="/select" className="btn btn-acid px-8 py-4 text-base">
                      START THE GRILLING
                      <ArrowRight className="h-5 w-5" strokeWidth={3} />
                    </Link>
                  </Magnetic>
                  <Magnetic strength={9}>
                    <Link href="/interview" className="btn btn-paper px-6 py-4 text-base">
                      SEE A DEMO
                    </Link>
                  </Magnetic>
                </div>

                {/* scroll cue */}
                <div className="mt-12 flex items-center gap-2 font-mono text-xs font-bold uppercase text-smoke">
                  <ArrowDown className="h-4 w-4 animate-bounce" strokeWidth={3} />
                  Scroll — see how it works
                </div>
              </motion.div>

              {/* demo + stickers */}
              <div className="relative">
                <motion.div
                  style={{ rotate: rotBadge }}
                  className="absolute -left-4 -top-7 z-20 hidden border-3 border-ink bg-sun px-3 py-2 shadow-brutal sm:block"
                >
                  <span className="font-display text-sm uppercase">LIVE ↯</span>
                </motion.div>

                <div className="rotate-1">
                  <Interrogation />
                </div>

                <div className="absolute -bottom-6 -right-3 z-20 hidden -rotate-6 border-3 border-ink bg-hot px-3 py-2 text-paper shadow-brutal lg:block">
                  <span className="font-display text-xs uppercase">NO BUZZWORDS</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============ MARQUEE ============ */}
        <div className="border-b-3 border-ink bg-ink py-2.5 text-paper">
          <Marquee
            items={['SHOW ME THE INCIDENT', 'WHAT WAS THE NUMBER', 'WHO ELSE WAS ON CALL', 'WHAT BROKE', 'PROVE IT']}
            reverse
            speed={34}
            separator="●"
          />
        </div>

        {/* ============ STATS ============ */}
        <section className="border-b-3 border-ink">
          <div className="mx-auto grid max-w-[1600px] grid-cols-2 lg:grid-cols-4">
            {STATS.map((s, i) => (
              <Reveal key={s.l} delay={i * 0.07}>
                <div
                  className={cn(
                    'border-ink p-6 sm:p-8',
                    s.bg,
                    i < 3 && 'lg:border-r-3',
                    i % 2 === 0 && 'border-r-3 lg:border-r-3',
                    i < 2 && 'border-b-3 lg:border-b-0'
                  )}
                >
                  <div className="font-display text-5xl leading-none sm:text-6xl">
                    <Counter value={s.v} suffix={s.s} />
                  </div>
                  <div className="mt-2 font-mono text-[11px] font-bold uppercase tracking-widest">
                    {s.l}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ============ PROCESS ============ */}
        <section className="border-b-3 border-ink bg-sand">
          <div className="mx-auto max-w-[1600px] px-4 py-20 sm:px-6">
            <Reveal>
              <h2 className="display text-[clamp(2.4rem,7vw,5.5rem)]">
                THREE MOVES.
                <br />
                <span className="text-cobalt">ZERO MERCY.</span>
              </h2>
            </Reveal>

            <div className="mt-12 grid gap-6 md:grid-cols-3">
              {STEPS.map((step, i) => (
                <Reveal key={step.n} delay={i * 0.1} from="scale">
                  <Box
                    interactive
                    shadow="lg"
                    className={cn('h-full p-6', step.bg, i === 1 && 'md:-translate-y-5')}
                  >
                    <div className="flex items-start justify-between">
                      <span className="font-display text-6xl leading-none opacity-25">
                        {step.n}
                      </span>
                      <span className="border-3 border-ink bg-paper p-2 text-ink">
                        <step.icon className="h-6 w-6" strokeWidth={2.5} />
                      </span>
                    </div>
                    <h3 className="mt-5 font-display text-3xl">{step.title}</h3>
                    <p className="mt-2.5 text-sm font-medium leading-relaxed">{step.body}</p>
                  </Box>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* ============ QUOTE ============ */}
        <section className="border-b-3 border-ink">
          <div className="mx-auto max-w-[1600px] px-4 py-20 sm:px-6">
            <Reveal>
              <div className="mx-auto max-w-4xl text-center">
                <Quote className="mx-auto h-12 w-12" strokeWidth={3} />
                <p className="mt-6 display text-[clamp(1.8rem,5vw,4rem)]">
                  &ldquo;ANYONE CAN <span className="marker">TYPE</span> A SKILL.
                  <br />
                  ALMOST NOBODY CAN <span className="text-blood">DEFEND</span> IT.&rdquo;
                </p>
              </div>
            </Reveal>
          </div>
        </section>

        {/* ============ CTA ============ */}
        <section className="bg-cobalt">
          <div className="mx-auto max-w-[1600px] px-4 py-20 text-center sm:px-6">
            <Reveal from="scale">
              <h2 className="display text-[clamp(2.5rem,8vw,6.5rem)] text-paper">
                READY TO GET
                <br />
                <span className="text-acid">CAUGHT OUT?</span>
              </h2>
              <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
                <Magnetic>
                  <Link href="/select" className="btn btn-acid px-9 py-5 text-lg">
                    RUN AN INTERVIEW
                    <CornerDownRight className="h-5 w-5" strokeWidth={3} />
                  </Link>
                </Magnetic>
                <Magnetic strength={9}>
                  <Link href="/results" className="btn btn-paper px-7 py-5 text-lg">
                    SEE A REPORT
                  </Link>
                </Magnetic>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      {/* ============ FOOTER ============ */}
      <footer className="border-t-3 border-ink bg-ink text-paper">
        <div className="mx-auto flex max-w-[1600px] flex-col items-center justify-between gap-3 px-4 py-7 sm:flex-row sm:px-6">
          <span className="font-display text-2xl">VERITAS</span>
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest">
            Evidence or it didn&apos;t happen
          </span>
        </div>
      </footer>
    </div>
  );
}
