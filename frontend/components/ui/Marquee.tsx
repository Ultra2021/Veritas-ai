'use client';

import { cn } from '@/lib/utils';

interface MarqueeProps {
  items: string[];
  /** Scroll direction. */
  reverse?: boolean;
  className?: string;
  /** Seconds for one full loop. */
  speed?: number;
  separator?: string;
}

/**
 * Infinite horizontal ticker. The item list is duplicated and the track is
 * translated -50%, so the loop is seamless.
 */
export default function Marquee({
  items,
  reverse = false,
  className,
  speed = 26,
  separator = '✦',
}: MarqueeProps) {
  const doubled = [...items, ...items];

  return (
    <div className={cn('relative flex overflow-hidden', className)}>
      <div
        className={cn(
          'flex w-max shrink-0 items-center',
          reverse ? 'animate-marquee-rev' : 'animate-marquee'
        )}
        style={{ animationDuration: `${speed}s` }}
      >
        {doubled.map((item, i) => (
          <span key={i} className="flex items-center whitespace-nowrap">
            <span className="px-5 font-display text-sm font-black uppercase tracking-tight sm:text-base">
              {item}
            </span>
            <span aria-hidden className="text-xs opacity-60">
              {separator}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
