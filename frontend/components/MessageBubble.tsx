'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Bot, User, CheckCircle, Sparkles } from 'lucide-react';
import { ChatMessage } from '../types/interview';

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isAi = message.sender === 'ai';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-3.5 max-w-3xl ${isAi ? 'self-start' : 'self-end flex-row-reverse'} w-full mb-4`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-lg ${
          isAi
            ? 'bg-gradient-to-br from-indigo-600 via-indigo-700 to-cyan-500 text-white border border-cyan-400/30'
            : 'bg-gradient-to-br from-slate-700 to-slate-900 text-cyan-300 border border-white/10'
        }`}
      >
        {isAi ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
      </div>

      {/* Message Card */}
      <div className={`flex flex-col ${isAi ? 'items-start' : 'items-end'} max-w-[88%]`}>

        {/* Sender Name & Meta */}
        <div className="flex items-center gap-2 mb-1.5 px-1">
          <span className="text-xs font-semibold text-gray-300">
            {isAi ? 'Veritas Evaluator AI' : 'Candidate Answer'}
          </span>
          <span className="text-[10px] text-gray-500">{message.timestamp}</span>
        </div>

        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-md transition-all ${
            isAi
              ? 'bg-slate-900/80 text-slate-100 border border-indigo-500/20 rounded-tl-none shadow-indigo-950/20'
              : 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white border border-indigo-400/30 rounded-tr-none shadow-indigo-900/30'
          }`}
        >
          {/* Skill Tag Callout for AI Questions */}
          {isAi && message.skillTag && (
            <div className="mb-2.5 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-[11px] text-cyan-300 font-medium">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              Target Skill: <span className="font-semibold text-white">{message.skillTag}</span>
            </div>
          )}

          <p className="whitespace-pre-wrap">{message.text}</p>

          {/* Verification Highlight Badge for Candidate Responses */}
          {!isAi && message.evidenceAdded && (
            <div className="mt-2.5 pt-2 border-t border-white/15 flex items-center gap-1.5 text-[11px] text-emerald-300 font-medium">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              Evidence Logged: <span className="text-white underline decoration-emerald-400/50">{message.evidenceAdded}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
