export interface InterviewDNA {
  technical: number;
  communication: number;
  leadership: number;
  problemSolving: number;
  learning: number;
}

export interface InterviewResponse {
  question: string;
  verifiedSkills: string[];
  currentSkill: string;
  confidence: number;
  interviewDNA: InterviewDNA;
  done: boolean;
}

export type SkillStatus = 'Verified' | 'Partial' | 'Needs More Evidence';

export interface SkillDetail {
  name: string;
  status: SkillStatus;
  score: number; // 0-100
  evidenceSnippet?: string;
}

export interface CandidateInfo {
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
