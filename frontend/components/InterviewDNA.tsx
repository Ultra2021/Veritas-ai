'use client';

import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { InterviewDNA as InterviewDNAType } from '../types/interview';
import { Dna, Sparkles } from 'lucide-react';

interface InterviewDNAProps {
  dna: InterviewDNAType;
  compact?: boolean;
}

export default function InterviewDNA({ dna, compact = false }: InterviewDNAProps) {
  const chartData = [
    { axis: 'Technical Knowledge', value: dna.technical, fullMark: 100 },
    { axis: 'Communication', value: dna.communication, fullMark: 100 },
    { axis: 'Problem Solving', value: dna.problemSolving, fullMark: 100 },
    { axis: 'Leadership', value: dna.leadership, fullMark: 100 },
    { axis: 'Learning Agility', value: dna.learning, fullMark: 100 },
  ];

  return (
    <div className={`glass-card rounded-2xl ${compact ? 'p-3.5' : 'p-6'} border border-white/10 shadow-xl space-y-3`}>
      <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
        <div className="flex items-center gap-2">
          <Dna className="w-4 h-4 text-violet-400" />
          <h3 className={`${compact ? 'text-xs' : 'text-sm'} font-bold uppercase tracking-wider text-gray-200`}>
            Interview DNA Matrix
          </h3>
        </div>
        <span className="text-[10px] text-violet-300 font-medium px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/30">
          5-Vector Analysis
        </span>
      </div>

      {/* Radar Chart Container */}
      <div className={`w-full ${compact ? 'h-48' : 'h-72'} flex items-center justify-center`}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius={compact ? '65%' : '75%'} data={chartData}>
            <PolarGrid stroke="rgba(255, 255, 255, 0.15)" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="axis"
              tick={{ fill: '#cbd5e1', fontSize: compact ? 10 : 12, fontWeight: 500 }}
            />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 9 }} />
            <Radar
              name="Candidate Score"
              dataKey="value"
              stroke="#818cf8"
              fill="url(#radarGradient)"
              fillOpacity={0.6}
            />
            <defs>
              <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                borderColor: 'rgba(255, 255, 255, 0.15)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '12px',
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {!compact && (
        <div className="grid grid-cols-5 gap-2 pt-2 border-t border-white/10 text-center">
          <div>
            <div className="text-[10px] text-gray-400">Technical</div>
            <div className="text-sm font-extrabold text-indigo-400">{dna.technical}%</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-400">Comm.</div>
            <div className="text-sm font-extrabold text-cyan-400">{dna.communication}%</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-400">Problem</div>
            <div className="text-sm font-extrabold text-emerald-400">{dna.problemSolving}%</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-400">Leadership</div>
            <div className="text-sm font-extrabold text-amber-400">{dna.leadership}%</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-400">Learning</div>
            <div className="text-sm font-extrabold text-violet-400">{dna.learning}%</div>
          </div>
        </div>
      )}
    </div>
  );
}
