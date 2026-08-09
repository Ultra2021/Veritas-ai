'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Send, CornerDownLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnswerInputProps {
  onSubmit: (answer: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const MIN_STRONG = 140;

export default function AnswerInput({
  onSubmit,
  disabled = false,
  placeholder = 'Give specifics. Numbers, names, what broke…',
}: AnswerInputProps) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  // Grow to fit content, capped.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue('');
  }, [value, disabled, onSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      submit();
    }
  };

  const chars = value.trim().length;
  const strength = Math.min(100, (chars / MIN_STRONG) * 100);
  const canSend = chars > 0 && !disabled;

  return (
    <div
      className={cn(
        'border-t-3 border-ink bg-sand p-4 transition-colors duration-150',
        focused && 'bg-paper'
      )}
    >
      {/* strength meter */}
      <div className="mb-2 flex items-center gap-3">
        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-smoke">
          DETAIL
        </span>
        <div className="flex h-2.5 flex-1 border-2 border-ink bg-paper">
          <motion.div
            className={cn(
              'h-full',
              strength < 34 ? 'bg-blood' : strength < 70 ? 'bg-sun' : 'bg-mint'
            )}
            animate={{ width: `${strength}%` }}
            transition={{ duration: 0.25 }}
          />
        </div>
        <span className="font-mono text-[10px] font-bold tabular-nums text-smoke">
          {chars}
        </span>
      </div>

      <div className="flex items-end gap-3">
        <label htmlFor="answer" className="sr-only">
          Your answer
        </label>
        <textarea
          id="answer"
          ref={ref}
          rows={2}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="field flex-1 resize-none text-sm leading-relaxed disabled:cursor-not-allowed disabled:bg-sand disabled:opacity-60"
        />

        <button
          type="button"
          onClick={submit}
          disabled={!canSend}
          aria-label="Submit answer"
          className={cn(
            'flex h-[52px] w-[52px] shrink-0 items-center justify-center border-3 border-ink transition-all duration-150',
            canSend
              ? 'bg-hot text-paper shadow-brutal hover:-translate-y-0.5 hover:shadow-brutal-md active:translate-x-1 active:translate-y-1 active:shadow-none'
              : 'cursor-not-allowed bg-sand text-smoke'
          )}
        >
          <Send className="h-5 w-5" strokeWidth={3} />
        </button>
      </div>

      <div className="mt-2 flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase tracking-wide text-smoke">
        <kbd className="border-2 border-ink bg-paper px-1.5 py-0.5">⌘</kbd>
        <span>+</span>
        <kbd className="flex items-center gap-1 border-2 border-ink bg-paper px-1.5 py-0.5">
          <CornerDownLeft className="h-2.5 w-2.5" strokeWidth={3} />
        </kbd>
        <span className="ml-1">to fire</span>
      </div>
    </div>
  );
}
