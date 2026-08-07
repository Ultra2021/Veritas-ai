import axios from 'axios';
import { InterviewResponse } from '../types/interview';

// Default mock response as per prompt spec
export const mockResponse: InterviewResponse = {
  question: "Explain FastAPI dependency injection and how it differs from traditional class-based DI frameworks.",
  verifiedSkills: ["Python"],
  currentSkill: "FastAPI",
  confidence: 68,
  interviewDNA: {
    technical: 82,
    communication: 76,
    leadership: 61,
    problemSolving: 90,
    learning: 79
  },
  done: false
};

// Stateful mock interview sequence for live demo experience
const mockInterviewSteps: InterviewResponse[] = [
  {
    question: "Welcome! To begin, explain FastAPI dependency injection and how it helps write testable, decoupled Python microservices.",
    verifiedSkills: ["Python Basics"],
    currentSkill: "FastAPI",
    confidence: 34,
    interviewDNA: { technical: 65, communication: 70, leadership: 50, problemSolving: 60, learning: 75 },
    done: false,
  },
  {
    question: "Great evidence on FastAPI `Depends()`. Now, how do you handle asynchronous database sessions with SQLAlchemy 2.0 in Python to avoid connection pooling bottlenecks?",
    verifiedSkills: ["Python Basics", "FastAPI DI"],
    currentSkill: "Async I/O & Databases",
    confidence: 58,
    interviewDNA: { technical: 78, communication: 75, leadership: 55, problemSolving: 80, learning: 82 },
    done: false,
  },
  {
    question: "Impressive depth on async event loops! In a high-traffic system, how would you design distributed caching using Redis and manage race conditions when multiple workers update hot keys?",
    verifiedSkills: ["Python Basics", "FastAPI DI", "Async I/O"],
    currentSkill: "Distributed Caching (Redis)",
    confidence: 76,
    interviewDNA: { technical: 88, communication: 82, leadership: 65, problemSolving: 89, learning: 85 },
    done: false,
  },
  {
    question: "Walk me through how you lead system design trade-offs when migrating a monolithic Python backend to containerized Kubernetes microservices under tight deadlines.",
    verifiedSkills: ["Python Basics", "FastAPI DI", "Async I/O", "Redis Caching"],
    currentSkill: "Kubernetes & Leadership",
    confidence: 89,
    interviewDNA: { technical: 92, communication: 88, leadership: 84, problemSolving: 91, learning: 89 },
    done: false,
  },
  {
    question: "Evaluation Complete! Veritas AI has successfully verified your skills with empirical evidence across 5 key dimensions.",
    verifiedSkills: ["Python Basics", "FastAPI DI", "Async I/O", "Redis Caching", "System Architecture & K8s"],
    currentSkill: "Full Assessment Verified",
    confidence: 94,
    interviewDNA: { technical: 94, communication: 90, leadership: 86, problemSolving: 93, learning: 92 },
    done: true,
  }
];

// Memory store for tracking session step in mock mode
const sessionSteps: Record<string, number> = {};

/**
 * Get the next question from the interview engine.
 * Swap mock implementation with real backend Axios endpoint when ready.
 */
export async function getNextQuestion(sessionId: string, answer: string): Promise<InterviewResponse> {
  // UNCOMMENT FOR REAL BACKEND CALL:
  // const res = await axios.post("/api/interview", { sessionId, answer });
  // return res.data;

  // Progressive Mock implementation for dynamic live demo:
  if (!answer || answer.trim() === '') {
    return mockInterviewSteps[0];
  }

  const currentStep = sessionSteps[sessionId] ?? 0;
  const nextStepIndex = Math.min(currentStep + 1, mockInterviewSteps.length - 1);
  sessionSteps[sessionId] = nextStepIndex;

  // Simulate network latency for realistic feel (400ms delay)
  await new Promise(resolve => setTimeout(resolve, 400));

  return mockInterviewSteps[nextStepIndex];
}

/**
 * Reset mock interview session state
 */
export function resetMockSession(sessionId: string): void {
  sessionSteps[sessionId] = 0;
}
