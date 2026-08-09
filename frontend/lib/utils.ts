import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge conditional class names, de-duplicating conflicting Tailwind utilities. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Clamp a number between min and max. */
export function clamp(value: number, min = 0, max = 100) {
  return Math.min(max, Math.max(min, value));
}

/** Brutalist accent palette keys. */
export type Pop = 'acid' | 'hot' | 'cobalt' | 'tangerine' | 'violetPop' | 'mint' | 'sun' | 'blood';

export const POP_HEX: Record<Pop, string> = {
  acid: '#CCFF00',
  hot: '#FF2E88',
  cobalt: '#2D4EFF',
  tangerine: '#FF6B1A',
  violetPop: '#8B3DFF',
  mint: '#00E5A0',
  sun: '#FFD600',
  blood: '#E8202A',
};

export const POP_BG: Record<Pop, string> = {
  acid: 'bg-acid text-ink',
  hot: 'bg-hot text-paper',
  cobalt: 'bg-cobalt text-paper',
  tangerine: 'bg-tangerine text-ink',
  violetPop: 'bg-violetPop text-paper',
  mint: 'bg-mint text-ink',
  sun: 'bg-sun text-ink',
  blood: 'bg-blood text-paper',
};

/** Deterministic accent from a string — keeps colours stable across renders. */
export function popFor(seed: string, palette: Pop[] = ['acid', 'hot', 'cobalt', 'tangerine', 'violetPop', 'mint']): Pop {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return palette[Math.abs(hash) % palette.length];
}

/** Map a 0-100 score to a verdict colour. */
export function popForScore(score: number | null | undefined): Pop {
  if (score === null || score === undefined) return 'cobalt';
  if (score >= 85) return 'acid';
  if (score >= 65) return 'mint';
  if (score >= 45) return 'sun';
  return 'tangerine';
}
