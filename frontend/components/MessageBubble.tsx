'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ChatMessage } from '@/types/interview';
import { useTypewriter } from '@/hooks/useTypewriter';
import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: ChatMessage;
  /** Type out the text (used for the newest AI question only). */
  typewriter?: boolean;
}

export default function MessageBubble({ message, typewriter = false }: MessageBubbleProps) {
  const isAi = message.sender === 'ai';
  const { shown, done } = useTypewriter(message.text, 14, typewriter && isAi);

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.34, 1.56, 0.64, 1] }}
      className={cn('flex w-full', isAi ? 'justify-start' : 'justify-end')}
    >
      <div className={cn('max-w-[88%]', isAi ? 'items-start' : 'items-end')}>
        {/* Speaker tag */}
        <div className={cn('mb-1.5 flex items-center gap-2', !isAi && 'justify-end')}>
          <span className={cn('label', isAi ? 'bg-cobalt' : 'bg-ink')}>
            {isAi ? 'INTERROGATOR' : 'SUBJECT'}
          </span>
          {message.timestamp && (
            <span className="font-mono text-[10px] font-bold text-smoke">
              {message.timestamp}
            </span>
          )}
        </div>

        {/* Skill under attack */}
        {isAi && message.skillTag && (
          <div className="mb-2 inline-flex max-w-full items-center gap-1.5 border-3 border-ink bg-sun px-2 py-1">
            <span className="font-mono text-[9px] font-bold uppercase tracking-widest">
              PROBING
            </span>
            <span className="truncate font-display text-xs uppercase">
              {message.skillTag}
            </span>
          </div>
        )}

        {/* Body */}
        <div
          className={cn(
            'border-3 border-ink px-4 py-3 text-sm font-medium leading-relaxed shadow-brutal',
            isAi ? 'bg-paper' : 'bg-acid'
          )}
        >
          <p className="whitespace-pre-wrap break-words">
            {typewriter && isAi ? shown : message.text}
            {typewriter && isAi && !done && (
              <span className="ml-0.5 inline-block h-4 w-2 animate-blink bg-ink align-middle" />
            )}
          </p>

          {!isAi && message.evidenceAdded && (
            <div className="mt-3 border-t-3 border-dashed border-ink pt-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wide">
                ✓ LOGGED: {message.evidenceAdded}
              </span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
