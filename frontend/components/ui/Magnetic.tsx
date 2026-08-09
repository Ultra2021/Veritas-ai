'use client';

import React, { useRef, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface MagneticProps {
  children: React.ReactNode;
  className?: string;
  /** How far the element is pulled toward the cursor (px). */
  strength?: number;
}

/**
 * Pulls its child toward the cursor on hover. Disabled automatically for
 * coarse pointers via CSS media query check on first move.
 */
export default function Magnetic({
  children,
  className,
  strength = 14,
}: MagneticProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const handleMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const el = ref.current;
      if (!el) return;
      if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

      const rect = el.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width - 0.5;
      const relY = (e.clientY - rect.top) / rect.height - 0.5;
      setOffset({ x: relX * strength * 2, y: relY * strength * 2 });
    },
    [strength]
  );

  return (
    <div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={() => setOffset({ x: 0, y: 0 })}
      className={cn('inline-block', className)}
      style={{
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
        transition: 'transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }}
    >
      {children}
    </div>
  );
}
