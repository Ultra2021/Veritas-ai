'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Compass, BookOpen, Target } from 'lucide-react';
import { CompetencyState } from '../types/interview';

export interface GrowthTopic {
  title: string;
  category: string;
  reasoning: string;
  difficulty: 'Intermediate' | 'Advanced' | 'Mastery';
}

interface GrowthMapProps {
  topics?: GrowthTopic[];
  competencies?: CompetencyState[];
}

export default function GrowthMap({ topics, competencies }: GrowthMapProps) {
  // Derive recommendations dynamically from real weak / needs_followup competencies if topics not explicitly passed
  let list: GrowthTopic[] = [];

  if (topics && topics.length > 0) {
    list = topics;
  } else if (competencies && competencies.length > 0) {
    list = competencies
      .filter((c) => c.status === 'needs_followup' || c.evidenceScore < 60)
      .map((c) => ({
        title: `Deep-Dive: ${c.competency}`,
        category: 'Competency Focus',
        reasoning: c.notes || `Evidence score is currently ${c.evidenceScore}%. Further practice and evidence collection recommended.`,
        difficulty: c.evidenceScore < 40 ? 'Advanced' : 'Intermediate',
      }));
  }

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

      {list.length === 0 ? (
        <div className="p-6 rounded-2xl glass-card border border-white/10 text-center text-xs text-gray-400 italic leading-relaxed">
          Targeted growth recommendations will appear after sufficient interview evidence is collected.
        </div>
      ) : (
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
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
