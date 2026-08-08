'use client';

import React, { useState, KeyboardEvent } from 'react';
import { Send, Loader2, Sparkles, Terminal, Code2 } from 'lucide-react';

interface AnswerInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export default function AnswerInput({ onSend, isLoading, disabled }: AnswerInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim() || isLoading || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const setQuickPrompt = (promptText: string) => {
    setInput((prev) => (prev ? `${prev} ${promptText}` : promptText));
  };

  return (
    <div className="w-full space-y-2.5">
      {/* Quick response helpers for seamless testing during demo */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
        <span className="text-gray-400 text-[11px] font-medium flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-amber-400" /> Demo Prompts:
        </span>
        <button
          type="button"
          disabled={isLoading || disabled}
          onClick={() => setQuickPrompt("FastAPI uses `Depends()` for dependency injection, resolving singletons and scoped dependencies automatically at request time.")}
          className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-indigo-900/40 border border-slate-700/80 hover:border-indigo-500/40 text-gray-300 text-[11px] transition-colors"
        >
          <Code2 className="w-3 h-3 inline mr-1 text-indigo-400" /> FastAPI DI Answer
        </button>
        <button
          type="button"
          disabled={isLoading || disabled}
          onClick={() => setQuickPrompt("I use async connection pools with asyncpg and Redis caching for hot queries with TTL invalidation.")}
          className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-indigo-900/40 border border-slate-700/80 hover:border-indigo-500/40 text-gray-300 text-[11px] transition-colors"
        >
          <Terminal className="w-3 h-3 inline mr-1 text-cyan-400" /> Async DB & Caching
        </button>
        <button
          type="button"
          disabled={isLoading || disabled}
          onClick={() => setQuickPrompt("We containerized services using Docker, managed HPA auto-scaling on GKE, and enforced strict canary deployments.")}
          className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-indigo-900/40 border border-slate-700/80 hover:border-indigo-500/40 text-gray-300 text-[11px] transition-colors"
        >
          K8s & Scale Strategy
        </button>
      </div>

      {/* Main Input Box */}
      <div className="relative glass-panel rounded-2xl p-2 border border-white/10 shadow-xl focus-within:border-indigo-500/50 transition-all">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || disabled}
          placeholder={disabled ? "Interview evaluation completed." : "Type your technical answer here... (Press Enter to send, Shift+Enter for new line)"}
          rows={3}
          className="w-full bg-transparent text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none p-2 rounded-xl"
        />

        <div className="flex items-center justify-between pt-1 px-2 border-t border-white/5">
          <span className="text-[11px] text-gray-400">
            {input.length} characters • Powered by Veritas Evidence Engine
          </span>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || disabled}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-xs transition-all shadow-md ${
              !input.trim() || isLoading || disabled
                ? 'bg-slate-800 text-gray-500 cursor-not-allowed border border-white/5'
                : 'bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-indigo-600/30 border border-indigo-400/30 hover:scale-[1.02]'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-cyan-300" />
                Analyzing Evidence...
              </>
            ) : (
              <>
                <span>Submit Answer</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
