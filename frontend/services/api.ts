import axios from 'axios';
import { InterviewTurnResponse, InterviewState } from '../types/interview';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Start a new interview session for a candidate.
 * POST /api/interview/start
 */
export async function startInterview(candidateId: string): Promise<InterviewTurnResponse> {
  const res = await api.post<InterviewTurnResponse>('/api/interview/start', { candidateId });
  return res.data;
}

/**
 * Submit candidate answer and retrieve next turn evaluation.
 * POST /api/interview/answer
 */
export async function submitAnswer(sessionId: string, answer: string): Promise<InterviewTurnResponse> {
  const res = await api.post<InterviewTurnResponse>('/api/interview/answer', {
    sessionId,
    answer,
  });
  return res.data;
}

/**
 * Fetch current stored state for an interview session.
 * GET /api/interview/{session_id}
 */
export async function getInterviewState(sessionId: string): Promise<InterviewState> {
  const res = await api.get<InterviewState>(`/api/interview/${sessionId}`);
  return res.data;
}

/**
 * End an active interview session early.
 * POST /api/interview/end
 */
export async function endInterview(sessionId: string): Promise<InterviewTurnResponse> {
  const res = await api.post<InterviewTurnResponse>('/api/interview/end', { sessionId });
  return res.data;
}

