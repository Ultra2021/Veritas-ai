'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowDown, Crosshair } from 'lucide-react';
import MessageBubble from './MessageBubble';
import { ChatMessage } from '@/types/interview';

interface ChatWindowProps {
  messages: ChatMessage[];
  isAiThinking?: boolean;
}

export default function ChatWindow({ messages, isAiThinking }: ChatWindowProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showJump, setShowJump] = useState(false);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    bottomRef.current?.scrollIntoView({ behavior, block: 'end' });
  }, []);

  // Auto-scroll only when already near the bottom.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
    if (dist < 240) scrollToBottom();
  }, [messages, isAiThinking, scrollToBottom]);

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    setShowJump(el.scrollHeight - el.scrollTop - el.clientHeight > 260);
  }, []);

  const lastAiIndex = messages.map((m) => m.sender).lastIndexOf('ai');

  return (
    <div className="relative flex min-h-0 flex-1">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 space-y-5 overflow-y-auto p-1"
      >
        {messages.length === 0 && !isAiThinking ? (
          <div className="flex h-full min-h-[300px] flex-col items-center justify-center px-6 text-center">
            <div className="border-3 border-ink bg-sun p-4 shadow-brutal">
              <Crosshair className="h-8 w-8" strokeWidth={2.5} />
            </div>
            <h3 className="mt-5 font-display text-2xl uppercase">STANDING BY</h3>
            <p className="mt-2 max-w-sm text-sm font-medium text-smoke">
              The interrogator is loading your file. Questions incoming.
            </p>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                typewriter={i === lastAiIndex && i === messages.length - 1}
              />
            ))}
          </AnimatePresence>
        )}

        {isAiThinking && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 border-3 border-ink bg-cobalt px-4 py-3 text-paper shadow-brutal"
          >
            <span className="font-mono text-xs font-bold uppercase tracking-widest">
              WEIGHING THE EVIDENCE
            </span>
            <span className="flex gap-1">
              {[0, 0.15, 0.3].map((d) => (
                <motion.span
                  key={d}
                  className="h-2.5 w-2.5 bg-acid"
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 0.7, repeat: Infinity, delay: d }}
                />
              ))}
            </span>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      <AnimatePresence>
        {showJump && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            onClick={() => scrollToBottom()}
            className="absolute bottom-3 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1.5 border-3 border-ink bg-acid px-3 py-2 font-mono text-[10px] font-bold uppercase shadow-brutal"
          >
            <ArrowDown className="h-3.5 w-3.5" strokeWidth={3} />
            LATEST
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
