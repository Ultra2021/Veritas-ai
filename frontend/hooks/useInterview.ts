'use client';

import { useState, useEffect, useCallback } from 'react';
import { startInterview, submitAnswer as apiSubmitAnswer, getInterviewState } from '../services/api';
import {
  CandidateInfo,
  ChatMessage,
  InterviewTurnResponse,
  SkillDetail,
  SkillStatus,
  CompetencyState,
} from '../types/interview';

const DEFAULT_CANDIDATE: CandidateInfo = {
  candidateId: 'CAND-001',
  name: 'Sarah Johnson',
  targetRole: 'Senior Data Engineer',
  experienceLevel: 'Senior',
  companyMode: 'Startup (Fast & Scrappy)',
};

export function useInterview() {
  const [candidate, setCandidate] = useState<CandidateInfo>(DEFAULT_CANDIDATE);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = useState<InterviewTurnResponse | null>(null);

  // Hydrate candidate data from localStorage if available
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('veritas_candidate');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setCandidate({
            ...DEFAULT_CANDIDATE,
            ...parsed,
          });
        } catch (e) {
          console.error('Failed to parse candidate from localStorage:', e);
        }
      }
    }
  }, []);

  // Initialize or start session for candidate
  const startSession = useCallback(async (candidateIdToUse?: string) => {
    const targetCandidateId = candidateIdToUse || candidate.candidateId || 'CAND-001';
    setIsStarting(true);
    setIsLoading(true);
    setError(null);
    try {
      const turn = await startInterview(targetCandidateId);
      setSessionId(turn.sessionId);
      setCurrentResponse(turn);

      const firstQuestionMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'ai',
        text: turn.question,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        skillTag: turn.currentCompetency || undefined,
      };
      setMessages([firstQuestionMsg]);
    } catch (err: any) {
      console.error('Failed to start interview session:', err);
      const msg = err.response?.data?.detail || err.message || 'Unable to connect to backend server at http://localhost:8000';
      setError(msg);
    } finally {
      setIsStarting(false);
      setIsLoading(false);
    }
  }, [candidate.candidateId]);

  // Automatically start interview if no active session
  useEffect(() => {
    if (!sessionId && !isStarting && !currentResponse) {
      startSession();
    }
  }, [sessionId, isStarting, currentResponse, startSession]);

  const updateCandidateInfo = (info: CandidateInfo) => {
    setCandidate(info);
    if (typeof window !== 'undefined') {
      localStorage.setItem('veritas_candidate', JSON.stringify(info));
    }
  };

  const submitAnswer = async (answerText: string): Promise<InterviewTurnResponse | null> => {
    if (!answerText.trim() || !sessionId || isLoading) return null;

    setIsLoading(true);
    setError(null);

    // Add candidate message to history immediately
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'candidate',
      text: answerText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      evidenceAdded: currentResponse?.currentCompetency
        ? `${currentResponse.currentCompetency} response submitted`
        : 'Response submitted',
    };

    setMessages((prev) => [...prev, userMsg]);

    try {
      const turn = await apiSubmitAnswer(sessionId, answerText);
      setCurrentResponse(turn);

      // Add AI response message
      if (turn.question) {
        const aiMsg: ChatMessage = {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: turn.question,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          skillTag: turn.currentCompetency || undefined,
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
      return turn;
    } catch (err: any) {
      console.error('Interview turn failed:', err);
      const msg = err.response?.data?.detail || err.message || 'Error submitting answer to backend service';
      setError(msg);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const restartInterview = () => {
    setSessionId(null);
    setCurrentResponse(null);
    setMessages([]);
    setError(null);
    startSession(candidate.candidateId);
  };

  // Convert backend competencies array into detailed skill items for UI
  const getSkillDetails = (): SkillDetail[] => {
    if (!currentResponse || !currentResponse.competencies || currentResponse.competencies.length === 0) {
      return [];
    }

    return currentResponse.competencies.map((comp: CompetencyState) => {
      let status: SkillStatus = 'Needs More Evidence';
      if (comp.status === 'verified') {
        status = 'Verified';
      } else if (comp.status === 'in_progress' || comp.status === 'needs_followup') {
        status = 'Partial';
      }

      return {
        name: comp.competency,
        status,
        score: comp.evidenceScore,
        evidenceSnippet: comp.notes || (currentResponse.evidence?.competency === comp.competency ? currentResponse.evidence.reason : undefined),
      };
    });
  };

  return {
    candidate,
    updateCandidateInfo,
    messages,
    isLoading,
    isStarting,
    sessionId,
    error,
    currentResponse,
    startSession,
    submitAnswer,
    restartInterview,
    getSkillDetails,
  };
}
