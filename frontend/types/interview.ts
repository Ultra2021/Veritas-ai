export interface InterviewDNA {
  technicalKnowledge: number;
  communication: number;
  problemSolving: number;
  leadership: number;
  learningAbility: number;
}

export type NextAction = 'FOLLOW_UP' | 'VERIFY' | 'NEXT_COMPETENCY';

export interface EvidenceEvaluation {
  competency: string;
  evidenceScore: number;
  technicalScore: number;
  reasoningScore: number;
  completenessScore: number;
  communicationScore: number;
  verified: boolean;
  followUpRequired: boolean;
  nextAction: NextAction;
  reason: string;
  strengths: string[];
  gaps: string[];
  questionId: string;
  question: string;
}

export type CompetencyStatus = 'pending' | 'in_progress' | 'verified' | 'needs_followup';

export interface CompetencyState {
  competency: string;
  status: CompetencyStatus;
  evidenceScore: number;
  attempts: number;
  notes: string;
}

export type InterviewStage = 'initialized' | 'interviewing' | 'evaluating' | 'completed';

export interface InterviewTurnResponse {
  sessionId: string;
  questionId: string;
  question: string;
  currentCompetency: string | null;
  interviewStage: InterviewStage;
  evidence: EvidenceEvaluation | null;
  competencies: CompetencyState[];
  hiringConfidence: number | null;
  interviewDNA: InterviewDNA | null;
  done: boolean;
}

export type ConversationRole = 'system' | 'interviewer' | 'candidate' | 'evaluator';

export interface ConversationMessage {
  role: ConversationRole;
  message: string;
  timestamp: string;
}

export interface InterviewMetadata {
  startedAt: string;
  lastInteractionAt: string;
  totalQuestionsAsked: number;
  totalFollowUps: number;
  interviewDurationSeconds: number;
}

export interface InterviewState {
  sessionId: string;
  candidateId: string;
  currentCompetency: string | null;
  currentQuestionId: string;
  currentQuestion: string;
  currentAnswer: string | null;
  conversationHistory: ConversationMessage[];
  competencies: CompetencyState[];
  evidenceEvaluations: EvidenceEvaluation[];
  hiringConfidence: number | null;
  interviewDNA: InterviewDNA;
  interviewStage: InterviewStage;
  metadata: InterviewMetadata;
  completed: boolean;
  createdAt: string;
  updatedAt: string;
}

export type SkillStatus = 'Verified' | 'Partial' | 'Needs More Evidence';

export interface SkillDetail {
  name: string;
  status: SkillStatus;
  score: number; // 0-100
  evidenceSnippet?: string;
}

export interface CandidateInfo {
  candidateId: string;
  name: string;
  targetRole: string;
  experienceLevel: 'Junior' | 'Mid-Level' | 'Senior' | 'Lead / Principal';
  companyMode: 'Startup (Fast & Scrappy)' | 'Google (Algorithms & Scale)' | 'Microsoft (Enterprise & Systems)' | 'OpenAI (AI Architecture & Math)';
}

export interface ChatMessage {
  id: string;
  sender: 'ai' | 'candidate';
  text: string;
  timestamp: string;
  skillTag?: string;
  evidenceAdded?: string;
}
