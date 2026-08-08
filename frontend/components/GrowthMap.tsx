'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Compass, BookOpen, ArrowRight, Zap, Target } from 'lucide-react';

export interface GrowthTopic {
  title: string;
  category: string;
  reasoning: string;
  difficulty: 'Intermediate' | 'Advanced' | 'Mastery';
}

interface GrowthMapProps {
  topics?: GrowthTopic[];
}

export default function GrowthMap({ topics }: GrowthMapProps) {
  const defaultTopics: GrowthTopic[] = [
    {
      title: 'Advanced Kubernetes Custom Resource Definitions (CRDs)',
      category: 'DevOps & Scale',
      reasoning: 'Demonstrated solid Docker containerization, but could expand into writing custom operators for stateful services.',
      difficulty: 'Advanced',
    },
    {
      title: 'Distributed Transactions & Saga Pattern in Microservices',
      category: 'System Architecture',
      reasoning: 'Verified strong FastAPI DI and database queries; recommended for handling dual-write consistency across microservices.',
      difficulty: 'Mastery',
    },
    {
      title: 'Distributed Lock Mutual Exclusion with Redlock',
      category: 'Concurrency',
      reasoning: 'Candidate knows basic Redis caching; deep-dive into distributed locks will strengthen high-throughput synchronization.',
      difficulty: 'Intermediate',
    },
  ];

  const list = topics || defaultTopics;

  const getDifficultyColor = (diff: GrowthTopic['difficulty']) => {
    switch (diff) {
      case 'Mastery':
        return 'text-violet-400 bg-violet-500/10 border-violet-500/30';
      case 'Advanced':
        return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
      case 'Intermediate':
      default:
        return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Compass className="w-5 h-5 text-violet-400" />
          Candidate Growth Map
        </h3>
        <span className="text-xs text-gray-400">
          Targeted Upskilling Roadmap
        </span>
      </div>

      <div className="space-y-3">
        {list.map((item, idx) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1, duration: 0.3 }}
            className="glass-card rounded-2xl p-4 border border-white/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:border-violet-500/40"
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getDifficultyColor(item.difficulty)}`}>
                  {item.difficulty}
                </span>
                <span className="text-xs font-semibold text-gray-400 flex items-center gap-1">
                  <Target className="w-3 h-3 text-violet-400" /> {item.category}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-400 shrink-0" />
                {item.title}
              </h4>
              <p className="text-xs text-gray-400 leading-relaxed">
                {item.reasoning}
              </p>
            </div>

            <button className="shrink-0 flex items-center gap-1.5 text-xs font-medium text-cyan-300 hover:text-cyan-200 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 px-3.5 py-2 rounded-xl transition-all">
              <span>View Resource</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
