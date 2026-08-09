'use client';

import React, { useRef } from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface RevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  from?: 'bottom' | 'left' | 'right' | 'scale';
  once?: boolean;
}

/** Snappy overshoot entrance — brutalist UI shouldn't fade, it should SNAP. */
export default function Reveal({
  children,
  className,
  delay = 0,
  from = 'bottom',
  once = true,
}: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once, margin: '-60px' });
  const reduce = useReducedMotion();

  const initial =
    from === 'left'
      ? { opacity: 0, x: -40 }
      : from === 'right'
      ? { opacity: 0, x: 40 }
      : from === 'scale'
      ? { opacity: 0, scale: 0.85 }
      : { opacity: 0, y: 40 };

  return (
    <motion.div
      ref={ref}
      className={cn(className)}
      initial={reduce ? { opacity: 0 } : initial}
      animate={inView ? { opacity: 1, x: 0, y: 0, scale: 1 } : undefined}
      transition={{
        duration: reduce ? 0.2 : 0.55,
        delay,
        ease: [0.34, 1.56, 0.64, 1], // overshoot
      }}
    >
      {children}
    </motion.div>
  );
}
