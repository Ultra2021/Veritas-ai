'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * Custom brutalist cursor: a hard black square that inverts and grows over
 * interactive elements. Renders nothing on touch devices or when the user
 * prefers reduced motion.
 */
export default function Cursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [hot, setHot] = useState(false);
  const [down, setDown] = useState(false);

  useEffect(() => {
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!fine || reduce) return;

    setEnabled(true);
    document.documentElement.classList.add('cursor-none-fine');

    // Trailing ring uses lerp for a slight lag behind the dot.
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX;
    let ringY = mouseY;
    let raf = 0;

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${mouseX - 4}px, ${mouseY - 4}px, 0)`;
      }

      const el = e.target as HTMLElement | null;
      setHot(
        !!el?.closest(
          'a, button, input, textarea, select, [role="button"], [data-cursor="hot"]'
        )
      );
    };

    const loop = () => {
      ringX += (mouseX - ringX) * 0.18;
      ringY += (mouseY - ringY) * 0.18;
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ringX - 18}px, ${ringY - 18}px, 0)`;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    const onDown = () => setDown(true);
    const onUp = () => setDown(false);

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mousedown', onDown);
    window.addEventListener('mouseup', onUp);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('mouseup', onUp);
      document.documentElement.classList.remove('cursor-none-fine');
    };
  }, []);

  if (!enabled) return null;

  return (
    <>
      <div
        ref={dotRef}
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9999] h-2 w-2 bg-ink"
        style={{ willChange: 'transform' }}
      />
      <div
        ref={ringRef}
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9998] border-3 border-ink transition-[width,height,background-color,border-radius] duration-200"
        style={{
          width: hot ? 52 : 36,
          height: hot ? 52 : 36,
          marginLeft: hot ? -8 : 0,
          marginTop: hot ? -8 : 0,
          backgroundColor: hot ? '#CCFF00' : 'transparent',
          mixBlendMode: hot ? 'normal' : 'difference',
          transform: 'translate3d(-100px,-100px,0)',
          scale: down ? '0.8' : '1',
          willChange: 'transform',
        }}
      />
    </>
  );
}
