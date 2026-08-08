'use client';

import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { ChatMessage } from '../types/interview';
import { Bot, Sparkles, MessageSquare } from 'lucide-react';

interface ChatWindowProps {
  messages: ChatMessage[];
  isAiThinking?: boolean;
}

export default function ChatWindow({ messages, isAiThinking }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAiThinking]);

  return (
    <div className="flex-1 overflow-y-auto pr-2 space-y-4 min-h-[380px] max-h-[560px] custom-scrollbar">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-400">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
            <MessageSquare className="w-8 h-8 text-indigo-400" />
          </div>
          <h3 className="text-lg font-bold text-white mb-1">Interview Session Initialized</h3>
          <p className="text-sm text-gray-400 max-w-md">
            Veritas AI will ask targeted questions to collect evidence and verify your technical skills in real time.
          </p>
        </div>
      ) : (
        messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
      )}

      {/* Thinking Indicator */}
      {isAiThinking && (
        <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-900/60 border border-indigo-500/20 max-w-xs text-xs text-indigo-300 animate-pulse">
          <div className="w-7 h-7 rounded-lg bg-indigo-600/30 flex items-center justify-center">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-center gap-1.5 font-medium">
            <span>Evaluating answer evidence</span>
            <span className="flex gap-1 ml-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:0.4s]"></span>
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
