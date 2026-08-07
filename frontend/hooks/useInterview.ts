'use client';

import { useState, useEffect } from 'react';
import { getNextQuestion, resetMockSession } from '../services/api';
import {
  CandidateInfo,
  ChatMessage,
  InterviewResponse,
  SkillDetail,
  SkillStatus,
} from '../types/interview';

const DEFAULT_CANDIDATE: CandidateInfo = {
  name: 'Alex Chen',
  targetRole: 'Senior Backend Engineer',
  experienceLevel: 'Senior',
  companyMode: 'Startup (Fast & Scrappy)',
};

export function useInterview() {
  const [candidate, setCandidate] = useState<CandidateInfo>(DEFAULT_CANDIDATE);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>('session-1');
  const [currentResponse, setCurrentResponse] = useState<InterviewResponse>({
    question: 'Explain FastAPI dependency injection.',
    verifiedSkills: ['Python'],
    currentSkill: 'FastAPI',
    confidence: 34,
    interviewDNA: {
      technical: 65,
      communication: 70,
      leadership: 50,
      problemSolving: 60,
      learning: 75,
    },
    done: false,
  });

  // Hydrate candidate data from localStorage if available
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('veritas_candidate');
      if (saved) {
        try {
          setCandidate(JSON.parse(saved));
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, []);

  // Initialize first question if messages empty
  useEffect(() => {
    if (messages.length === 0) {
      const firstQuestionMsg: ChatMessage = {
        id: 'msg-0',
        sender: 'ai',
        text: currentResponse.question,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        skillTag: currentResponse.currentSkill,
      };
      setMessages([firstQuestionMsg]);
    }
  }, [messages.length, currentResponse.question, currentResponse.currentSkill]);

  const updateCandidateInfo = (info: CandidateInfo) => {
    setCandidate(info);
    if (typeof window !== 'undefined') {
      localStorage.setItem('veritas_candidate', JSON.stringify(info));
    }
  };

  const submitAnswer = async (answerText: string): Promise<InterviewResponse | null> => {
    if (!answerText.trim()) return null;

    setIsLoading(true);

    // Add candidate message to history immediately
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'candidate',
      text: answerText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      evidenceAdded: `${currentResponse.currentSkill} response submitted`,
    };

    setMessages((prev) => [...prev, userMsg]);

    try {
      // Call mock / real backend service
      const res = await getNextQuestion(sessionId, answerText);
      setCurrentResponse(res);

      // Add AI follow-up message
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: res.question,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        skillTag: res.currentSkill,
      };

      setMessages((prev) => [...prev, aiMsg]);
      setIsLoading(false);
      return res;
    } catch (err) {
      console.error('Interview turn failed:', err);
      setIsLoading(false);
      return null;
    }
  };

  const restartInterview = () => {
    const newSession = `session-${Date.now()}`;
    setSessionId(newSession);
    resetMockSession(newSession);
    setMessages([]);
    setCurrentResponse({
      question: 'Explain FastAPI dependency injection.',
      verifiedSkills: ['Python'],
      currentSkill: 'FastAPI',
      confidence: 34,
      interviewDNA: {
        technical: 65,
        communication: 70,
        leadership: 50,
        problemSolving: 60,
        learning: 75,
      },
      done: false,
    });
  };

  // Convert currentResponse into detailed skill items for UI
  const getSkillDetails = (): SkillDetail[] => {
    const allSkills = [
      { name: 'Python Core & Async', requiredConfidence: 30 },
      { name: 'FastAPI Dependency Injection', requiredConfidence: 50 },
      { name: 'Distributed Caching (Redis)', requiredConfidence: 70 },
      { name: 'Database Optimization', requiredConfidence: 80 },
      { name: 'Kubernetes Architecture', requiredConfidence: 90 },
    ];

    return allSkills.map((sk) => {
      const isVerified = currentResponse.verifiedSkills.some((vs) =>
        vs.toLowerCase().includes(sk.name.split(' ')[0].toLowerCase())
      ) || currentResponse.confidence >= sk.requiredConfidence;

      let status: SkillStatus = 'Needs More Evidence';
      let score = Math.max(20, Math.min(100, currentResponse.confidence - Math.floor(Math.random() * 10)));

      if (isVerified) {
        status = 'Verified';
        score = Math.min(98, Math.max(82, currentResponse.confidence + 5));
      } else if (currentResponse.confidence >= sk.requiredConfidence - 25) {
        status = 'Partial';
        score = Math.min(78, Math.max(50, currentResponse.confidence - 10));
      } else {
        status = 'Needs More Evidence';
        score = Math.min(45, currentResponse.confidence);
      }

      return {
        name: sk.name,
        status,
        score,
        evidenceSnippet: isVerified ? `Verified during ${sk.name} adaptive question phase.` : undefined,
      };
    });
  };

  return {
    candidate,
    updateCandidateInfo,
    messages,
    isLoading,
    currentResponse,
    submitAnswer,
    restartInterview,
    getSkillDetails,
  };
}
