'use client';

import { useEffect, useState } from 'react';

/**
 * Reveals `text` character by character. Respects reduced-motion by showing
 * the full string immediately. Returns the visible slice and a done flag.
 */
export function useTypewriter(text: string, speed = 16, enabled = true) {
  const [shown, setShown] = useState(enabled ? '' : text);
  const [done, setDone] = useState(!enabled);

  useEffect(() => {
    if (!enabled) {
      setShown(text);
      setDone(true);
      return;
    }

    if (
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      setShown(text);
      setDone(true);
      return;
    }

    setShown('');
    setDone(false);

    let i = 0;
    // Reveal a few chars per tick so long questions don't crawl.
    const step = Math.max(1, Math.round(text.length / 220));
    const id = setInterval(() => {
      i += step;
      if (i >= text.length) {
        setShown(text);
        setDone(true);
        clearInterval(id);
      } else {
        setShown(text.slice(0, i));
      }
    }, speed);

    return () => clearInterval(id);
  }, [text, speed, enabled]);

  return { shown, done };
}
