'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { startInterview, submitAnswer as apiSubmitAnswer, getInterviewState, endInterview as apiEndInterview } from '../services/api';
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

  const isStartingRef = useRef<boolean>(false);
  const isInitializedRef = useRef<boolean>(false);

  // Initialize or start session for candidate
  // Initialize or start session for candidate
  const startSession = useCallback(async (candidateIdToUse?: string) => {
    if (isStartingRef.current) return;
    isStartingRef.current = true;
    setIsStarting(true);
    setIsLoading(true);
    setError(null);
    try {
      let targetCandidateId = candidateIdToUse;
      if (!targetCandidateId && typeof window !== 'undefined') {
        const saved = localStorage.getItem('veritas_candidate');
        if (saved) {
          try {
            const parsed = JSON.parse(saved);
            if (parsed.candidateId) targetCandidateId = parsed.candidateId;
          } catch (e) {}
        }
      }
      if (!targetCandidateId) {
        targetCandidateId = candidate.candidateId || 'CAND-001';
      }

      const turn = await startInterview(targetCandidateId);

      setSessionId(turn.sessionId);
      setCurrentResponse(turn);

      const firstQuestionMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'ai',
        text: turn.reply || turn.question,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        skillTag: turn.currentCompetency || undefined,
      };
      setMessages([firstQuestionMsg]);

      if (typeof window !== 'undefined') {
        localStorage.setItem('veritas_session_id', turn.sessionId);
        localStorage.setItem('veritas_current_response', JSON.stringify(turn));
        localStorage.setItem('veritas_messages', JSON.stringify([firstQuestionMsg]));
      }
    } catch (err: any) {
      console.error('Failed to start interview session:', err);
      const msg = err.response?.data?.detail || err.message || 'Unable to connect to backend server';
      setError(msg);
    } finally {
      isStartingRef.current = false;
      setIsStarting(false);
      setIsLoading(false);
    }
  }, [candidate.candidateId]);

  // Hydrate candidate data & start interview session ONCE on mount
  useEffect(() => {
    if (isInitializedRef.current) return;
    isInitializedRef.current = true;

    if (typeof window !== 'undefined') {
      let activeCandidateId = 'CAND-001';
      const savedCandidate = localStorage.getItem('veritas_candidate');
      if (savedCandidate) {
        try {
          const parsed = JSON.parse(savedCandidate);
          if (parsed.candidateId) activeCandidateId = parsed.candidateId;
          setCandidate({
            ...DEFAULT_CANDIDATE,
            ...parsed,
          });
        } catch (e) {
          console.error('Failed to parse candidate from localStorage:', e);
        }
      }

      const savedSessionId = localStorage.getItem('veritas_session_id');
      const savedResponse = localStorage.getItem('veritas_current_response');
      const savedMessages = localStorage.getItem('veritas_messages');

      let parsedResponse: InterviewTurnResponse | null = null;
      if (savedResponse) {
        try {
          parsedResponse = JSON.parse(savedResponse);
          // Invalidate cached session if it belonged to a different candidate
          if (parsedResponse?.candidateId && parsedResponse.candidateId !== activeCandidateId) {
            parsedResponse = null;
            localStorage.removeItem('veritas_session_id');
            localStorage.removeItem('veritas_current_response');
            localStorage.removeItem('veritas_messages');
          } else {
            setCurrentResponse(parsedResponse);
          }
        } catch (e) {
          console.error('Failed to parse currentResponse from localStorage:', e);
        }
      }

      if (savedSessionId && parsedResponse) {
        setSessionId(savedSessionId);
      }

      if (savedMessages && parsedResponse) {
        try {
          const parsed = JSON.parse(savedMessages);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed);
          }
        } catch (e) {
          console.error('Failed to parse messages from localStorage:', e);
        }
      } else if (parsedResponse && parsedResponse.question) {
        setMessages([
          {
            id: `msg-hydrated`,
            sender: 'ai',
            text: parsedResponse.reply || parsedResponse.question,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            skillTag: parsedResponse.currentCompetency || undefined,
          },
        ]);
      }

      if (!savedSessionId || !parsedResponse) {
        startSession(activeCandidateId);
      }
    }
  }, [startSession]);

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

    setMessages((prev) => {
      const updated = [...prev, userMsg];
      if (typeof window !== 'undefined') {
        localStorage.setItem('veritas_messages', JSON.stringify(updated));
      }
      return updated;
    });

    try {
      const turn = await apiSubmitAnswer(sessionId, answerText);
      setCurrentResponse(turn);

      // Add AI response message
      const responseText = turn.reply || turn.question;
      if (responseText) {
        const aiMsg: ChatMessage = {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          skillTag: turn.currentCompetency || undefined,
        };
        setMessages((prev) => {
          const updated = [...prev, aiMsg];
          if (typeof window !== 'undefined') {
            localStorage.setItem('veritas_messages', JSON.stringify(updated));
          }
          return updated;
        });
      }
      if (typeof window !== 'undefined') {
        localStorage.setItem('veritas_current_response', JSON.stringify(turn));
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem('veritas_session_id');
      localStorage.removeItem('veritas_current_response');
      localStorage.removeItem('veritas_messages');
    }
    setSessionId(null);
    setCurrentResponse(null);
    setMessages([]);
    setError(null);
    isStartingRef.current = false;

    let activeCid = candidate.candidateId;
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('veritas_candidate');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (parsed.candidateId) activeCid = parsed.candidateId;
        } catch (e) {}
      }
    }
    startSession(activeCid);
  };

  const finishInterview = async (): Promise<InterviewTurnResponse | null> => {
    if (!sessionId || isLoading) return null;
    setIsLoading(true);
    setError(null);
    try {
      const turn = await apiEndInterview(sessionId);
      setCurrentResponse(turn);
      if (typeof window !== 'undefined') {
        localStorage.setItem('veritas_current_response', JSON.stringify(turn));
      }
      return turn;
    } catch (err: any) {
      console.error('Ending interview failed:', err);
      if (currentResponse) {
        const fallbackTurn: InterviewTurnResponse = {
          ...currentResponse,
          done: true,
          interviewStage: 'completed',
        };
        setCurrentResponse(fallbackTurn);
        if (typeof window !== 'undefined') {
          localStorage.setItem('veritas_current_response', JSON.stringify(fallbackTurn));
        }
        return fallbackTurn;
      }
      const msg = err.response?.data?.detail || err.message || 'Error ending interview session';
      setError(msg);
      return null;
    } finally {
      setIsLoading(false);
    }
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
    finishInterview,
    restartInterview,
    getSkillDetails,
  };
}
