# AI Usage Log

This log discloses how AI tools were used during development, per hackathon transparency requirements.

---

## AI Tools Used

| Tool | Purpose |
|------|---------|
| Claude (Anthropic) | Project planning, architecture decisions, prompt engineering, debugging guidance, git/workflow troubleshooting |
| Gemini (via Antigravity IDE) | Code generation for frontend pages/components based on detailed human-written specifications |

---

## How AI Was Used

### 1. Concept & Architecture Planning
Used Claude to refine the initial hackathon idea from a generic "AI interviewer" into a differentiated concept: an evidence-driven interview platform using a two-agent architecture (Interview Director + Evidence Engine) that verifies resume claims rather than just scoring answers.

### 2. Tech Stack Decisions
Used Claude to evaluate and simplify the proposed tech stack for a 2-day build — decisions included dropping LangGraph in favor of a direct agent-handoff loop, and avoiding an ORM (SQLAlchemy) in favor of lighter state management, to reduce implementation risk given the time constraint.

### 3. Frontend Code Generation
Used Gemini (Antigravity IDE) to generate the Next.js/TypeScript/Tailwind frontend, based on a detailed specification written by the human team (page layouts, component list, exact API contract, design direction). The specification was written by the team; the agent generated the implementation.

Pages and components generated: Landing page, Candidate Selection page, Interview page (chat interface, evidence sidebar, hiring confidence indicator, interview DNA radar chart), Results page (results card, verified skills grid, growth map).

### 4. Mock Data Layer
Used Gemini to build a stateful mock API (services/api.ts) matching an agreed InterviewResponse contract, allowing frontend development to proceed in parallel with backend development before real integration.

### 5. Integration Debugging
Used Claude to diagnose integration issues between the independently-developed frontend and backend — including a Network Error caused by the backend server not running locally, and a data provenance issue where the Results page contained hardcoded/fabricated fallback content (fake confidence percentages, fake model names, fake technical claims) instead of real backend evidence data.

### 6. Data Provenance Cleanup
Used Gemini, guided by a specification co-written with the backend teammate, to remove all fabricated/hardcoded content from the Results page (fake hiring confidence values, fake audit/model claims, fake growth map recommendations) and replace with real backend fields or honest "not yet available" states where the backend does not yet provide certain data.

### 7. Git/Workflow Support
Used Claude for git troubleshooting throughout development — repository setup, .gitignore configuration, branch management, and diagnosing merge/integration issues between team members' work.

---

## What Was NOT AI-Generated
- The core product concept and differentiation strategy were human-directed, with AI used to refine and pressure-test the idea rather than originate it.
- All architectural tradeoff decisions (e.g. dropping LangGraph, avoiding ORM, resolving the API contract mismatch) were made by the human team; AI provided analysis and options, not final decisions.
- Backend interview logic, scoring logic, and the AI agent orchestration itself (Interview Director + Evidence Engine) were built by the backend teammate — not detailed in this log, which covers the frontend contributor's AI usage.

---

## Human Oversight
All AI-generated code was reviewed by the team before being committed. Frontend changes were manually tested end-to-end (clicking through the live application) rather than relying solely on the AI agent's self-reported build/test results. Data provenance issues were caught by human review specifically because automated build success did not guarantee the absence of fabricated content.

---

## Key Highlights & Coverage Summary

- **3 LLM providers:** Groq (primary, openai/gpt-oss-20b), Gemini (gemini-2.0-flash), and deterministic fallback
- **2 core AI features:** Question generation (Interview Director) and answer evaluation (Evidence Engine)
- **System prompts:** Standardized prompts used for each agent
- **Structured output schemas:** Enforced via JSON schemas and Pydantic validation
- **Data flow diagrams:** Context tracking sent to the AI per request
- **Security measures:** Prompt injection guards, input sandboxing, and score normalization
- **Fallback behavior:** Comprehensive handling for every failure mode (no API key, API failure, invalid JSON, etc.)
- **Per-request AI call counts:** 1–2 LLM calls per API request
- **Architecture pattern:** Strategy Pattern with automatic deterministic fallbacks

---

*This log covers AI usage on the frontend side of the project as of the current development state. Update before final submission if additional AI-assisted work occurs.*
