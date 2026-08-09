# 🛡️ VERITAS AI — Evidence-Driven Technical Interrogation Platform

> **Résumés lie. Evidence doesn't.**  
> VERITAS AI is an adaptive AI technical interviewer that probes candidate CV claims, extracts concrete empirical quotes, dynamically updates hiring confidence matrices, and generates evidence-backed assessment reports.

---

## ✨ Features

- **⚡ Adaptive Technical Interrogation Engine**  
  Dynamically targets candidate claims (e.g., *“Kubernetes Expert”*, *“Distributed Systems Architecture”*) and probes recursively until concrete incident logs, metrics, or architectural trade-offs are provided.
  
- **🎨 Neo-Brutalist High-Impact UI**  
  Built with Next.js 15, Framer Motion, custom brutalist cursor physics, magnetic button pulls, live interrogation logs, and high-contrast color theory.

- **📊 Real-Time Skill & Telemetry Matrix**  
  - **Hiring Confidence Gauge:** Dynamic score tracking (0–100%).
  - **5-Axis Interview DNA:** Multi-dimensional radar breakdown across Technical Depth, Reasoning, Completeness, Communication, and Problem Solving.
  - **Competency Verification Graph:** Live evidence tagging (*Verified*, *Partial*, *Needs Evidence*).

- **📄 Printable Assessment Reports**  
  Generates comprehensive evaluation summaries linked directly to candidate quote snippets, complete with strengths, gaps, and hiring recommendations.

- **🐳 Production-Ready Containerization**  
  Single multi-stage `Dockerfile` serving Next.js 15 frontend and FastAPI backend behind a unified proxy for seamless Dokploy / Cloud deployment.

- **🤖 100% Vibe-Coded with Full AI Transcripts**  
  Built entirely with AI Agent trajectory logs ([Google DeepMind Antigravity AI](https://github.com/Ultra2021/Veritas-ai/blob/main/antigravity-transcripts.md) & [OpenCode AI](https://github.com/Ultra2021/Veritas-ai/blob/main/session-ses_022d.md)).

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend Framework** | Next.js 15 (App Router), React 19, TypeScript |
| **Styling & Motion** | TailwindCSS, Framer Motion, Lucide Icons, Custom Physics |
| **Backend Framework** | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| **AI Integration** | Google Gemini 3.6 / Groq / OpenAI LLM Providers |
| **Deployment** | Docker (Multi-stage Build), Dokploy, Shell Proxying |

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Node.js `20.x` or higher
- Python `3.11` or higher
- `npm` or `yarn`

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment & activate
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env  # Or populate GEMINI_API_KEY / GROQ_API_KEY

# Run FastAPI backend server (Port 8000)
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server (Port 3000)
npm run dev
```

Open [http://localhost:3000](http.localhost:3000) in your browser.

---

## 🐳 Running with Docker

You can build and run the entire unified stack (Frontend + Backend) in Docker:

```bash
# Build Docker image
docker build -t veritas-ai .

# Run Docker container
docker run -p 3000:3000 \
  -e GEMINI_API_KEY="your_api_key_here" \
  veritas-ai
```

Access the platform at `http://localhost:3000`.

---

## 🔌 API Specification

Veritas AI exposes the standard interview agent interface:

### `POST /api/interview`

#### 1. Start Interview Session
```json
POST /api/interview

{
  "sessionId": "ses_022d53da8ffe3b",
  "candidate": {
    "candidateId": "CAND-001",
    "name": "Sarah Johnson",
    "targetRole": "Senior Data Engineer",
    "experienceLevel": "Senior",
    "companyMode": "Startup (Fast & Scrappy)"
  }
}
```

#### Response:
```json
{
  "reply": "Welcome Sarah. Let's begin your technical verification. Name the last production data pipeline failure you personally debugged.",
  "done": false
}
```

#### 2. Conversation Turn
```json
POST /api/interview

{
  "sessionId": "ses_022d53da8ffe3b",
  "message": "Spark executor OOM due to skewed partition keys during peak ingestion."
}
```

---

## 📂 Project Structure

```
Veritas-ai/
├── backend/                  # FastAPI Python Backend
│   ├── config.py             # Environment configuration & CORS
│   ├── main.py               # FastAPI application entry point
│   ├── routes/               # Health check & Interview API routes
│   ├── services/             # Interview, Candidate, and Session logic
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js 15 App Router Frontend
│   ├── app/                  # Pages (/select, /interview, /results)
│   ├── components/           # Neo-brutalist UI components & widgets
│   ├── hooks/                # Custom React state hooks (useInterview)
│   └── types/                # TypeScript interface definitions
├── candidates.json           # Candidate profile configurations
├── curriculum.json           # Competency evaluation rubrics
├── Dockerfile                # Production multi-stage Docker build
├── start.sh                  # Dual-service startup script
├── PROMPTS.md                # AI Vibe-Coding Master Log & Trajectory
├── antigravity-transcripts.md# DeepMind Antigravity AI transcript log
└── session-ses_022d.md       # OpenCode AI session transcript log
```

---

## 📜 AI Usage & Vibe-Coding Transcripts

This project was **100% vibe-coded** using autonomous AI agents. All prompt logs, step-by-step tool executions, architectural decisions, and visual refactor sessions are tracked in:

- 📋 **Master AI Usage Log:** [`PROMPTS.md`](./PROMPTS.md)
- 🤖 **Antigravity AI Session Log:** [`antigravity-transcripts.md`](./antigravity-transcripts.md)
- ⚡ **OpenCode AI Session Log:** [`session-ses_022d.md`](./session-ses_022d.md)

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for details.
