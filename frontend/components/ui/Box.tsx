'use client';

import React from 'react';
import { cn } from '@/lib/utils';

type Accent =
  | 'paper'
  | 'acid'
  | 'hot'
  | 'cobalt'
  | 'tangerine'
  | 'violetPop'
  | 'mint'
  | 'sun'
  | 'ink';

const BG: Record<Accent, string> = {
  paper: 'bg-paper text-ink',
  acid: 'bg-acid text-ink',
  hot: 'bg-hot text-paper',
  cobalt: 'bg-cobalt text-paper',
  tangerine: 'bg-tangerine text-ink',
  violetPop: 'bg-violetPop text-paper',
  mint: 'bg-mint text-ink',
  sun: 'bg-sun text-ink',
  ink: 'bg-ink text-paper',
};

const SHADOW = {
  none: '',
  sm: 'shadow-brutal-sm',
  md: 'shadow-brutal-md',
  lg: 'shadow-brutal-lg',
  xl: 'shadow-brutal-xl',
};

interface BoxProps extends React.HTMLAttributes<HTMLElement> {
  accent?: Accent;
  shadow?: keyof typeof SHADOW;
  /** Lift + deepen shadow on hover. */
  interactive?: boolean;
  as?: 'div' | 'section' | 'article' | 'aside' | 'li';
  children?: React.ReactNode;
}

/** The fundamental brutalist container: thick black border + hard offset shadow. */
export default function Box({
  accent = 'paper',
  shadow = 'md',
  interactive = false,
  as: Tag = 'div',
  className,
  children,
  ...rest
}: BoxProps) {
  return (
    <Tag
      className={cn(
        'border-3 border-ink',
        BG[accent],
        SHADOW[shadow],
        interactive && 'press',
        className
      )}
      {...(rest as React.HTMLAttributes<HTMLElement>)}
    >
      {children}
    </Tag>
  );
}

export type { Accent };
