'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Check, Zap } from 'lucide-react';
import Marquee from './ui/Marquee';
import { cn } from '@/lib/utils';

export type Step = 'landing' | 'select' | 'interview' | 'results';

interface NavbarProps {
  currentStep?: Step;
  candidateName?: string;
}

const STEPS: { id: Exclude<Step, 'landing'>; href: string; label: string; n: string }[] = [
  { id: 'select', href: '/select', label: 'SETUP', n: '01' },
  { id: 'interview', href: '/interview', label: 'GRILL', n: '02' },
  { id: 'results', href: '/results', label: 'VERDICT', n: '03' },
];

const TICKER = [
  'RÉSUMÉS LIE',
  'EVIDENCE DOESN\u2019T',
  'PROVE IT',
  'NO BUZZWORDS',
  'RECEIPTS ONLY',
  'SHOW YOUR WORK',
];

export default function Navbar({ currentStep = 'landing', candidateName }: NavbarProps) {
  const [open, setOpen] = useState(false);
  const activeIndex = STEPS.findIndex((s) => s.id === currentStep);

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <>
      {/* Ticker strip */}
      <div className="border-b-3 border-ink bg-acid py-1.5">
        <Marquee items={TICKER} speed={30} />
      </div>

      <header className="sticky top-0 z-50 border-b-3 border-ink bg-paper">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6">
          {/* Wordmark */}
          <Link href="/" className="group flex shrink-0 items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center border-3 border-ink bg-ink text-paper transition-colors duration-150 group-hover:bg-acid group-hover:text-ink">
              <Zap className="h-5 w-5" strokeWidth={3} />
            </span>
            <span className="font-display text-2xl leading-none tracking-tighter">
              VERITAS
            </span>
          </Link>

          {/* Desktop steps */}
          <nav aria-label="Progress" className="hidden items-stretch border-3 border-ink lg:flex">
            {STEPS.map((step, i) => {
              const isActive = currentStep === step.id;
              const isDone = activeIndex > -1 && i < activeIndex;
              return (
                <Link
                  key={step.id}
                  href={step.href}
                  aria-current={isActive ? 'step' : undefined}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2.5 font-mono text-xs font-bold uppercase transition-colors duration-150',
                    i > 0 && 'border-l-3 border-ink',
                    isActive
                      ? 'bg-cobalt text-paper'
                      : isDone
                      ? 'bg-mint text-ink hover:bg-acid'
                      : 'bg-paper text-ink hover:bg-sand'
                  )}
                >
                  <span className="opacity-70">{step.n}</span>
                  {step.label}
                  {isDone && <Check className="h-3.5 w-3.5" strokeWidth={4} />}
                </Link>
              );
            })}
          </nav>

          {/* Right */}
          <div className="flex items-center gap-2">
            <AnimatePresence mode="wait" initial={false}>
              {candidateName ? (
                <motion.div
                  key="who"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  className="hidden items-center gap-2 border-3 border-ink bg-sun px-3 py-2 sm:flex"
                >
                  <span className="h-2.5 w-2.5 animate-pulse bg-ink" />
                  <span className="max-w-[140px] truncate font-mono text-xs font-bold uppercase">
                    {candidateName}
                  </span>
                </motion.div>
              ) : (
                <motion.div
                  key="cta"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                >
                  <Link href="/select" className="btn btn-hot hidden px-4 py-2 text-xs sm:inline-flex">
                    START
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>

            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-label={open ? 'Close menu' : 'Open menu'}
              aria-expanded={open}
              className="flex h-10 w-10 items-center justify-center border-3 border-ink bg-paper transition-colors hover:bg-acid lg:hidden"
            >
              {open ? <X className="h-5 w-5" strokeWidth={3} /> : <Menu className="h-5 w-5" strokeWidth={3} />}
            </button>
          </div>
        </div>

        {/* Progress bar */}
        {activeIndex > -1 && (
          <div className="h-2 border-t-3 border-ink bg-sand">
            <motion.div
              className="h-full bg-hot"
              initial={{ width: 0 }}
              animate={{ width: `${((activeIndex + 1) / STEPS.length) * 100}%` }}
              transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
            />
          </div>
        )}
      </header>

      {/* Mobile sheet */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-40 bg-ink/40 lg:hidden"
          >
            <motion.nav
              initial={{ y: -24, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -24, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.34, 1.56, 0.64, 1] }}
              onClick={(e) => e.stopPropagation()}
              className="mt-[6.5rem] space-y-3 border-b-3 border-ink bg-paper p-4"
            >
              {STEPS.map((step, i) => {
                const isActive = currentStep === step.id;
                const isDone = activeIndex > -1 && i < activeIndex;
                return (
                  <Link
                    key={step.id}
                    href={step.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      'flex items-center gap-3 border-3 border-ink px-4 py-3 font-display text-lg uppercase shadow-brutal',
                      isActive ? 'bg-cobalt text-paper' : isDone ? 'bg-mint' : 'bg-paper'
                    )}
                  >
                    <span className="font-mono text-xs opacity-70">{step.n}</span>
                    {step.label}
                  </Link>
                );
              })}
              <Link
                href="/select"
                onClick={() => setOpen(false)}
                className="btn btn-hot w-full"
              >
                START NEW
              </Link>
            </motion.nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
