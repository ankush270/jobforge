# JobForge 🚀

**AI-Powered Autonomous Job Discovery, ATS Scoring & Application Command Center**

JobForge is an end-to-end career acceleration platform designed to automatically discover, pre-filter, score, and track engineering opportunities with a primary focus on early-career (0–1 Year) Indian software and tech roles.

---

## 🌟 Key Features

- **290+ Target Company Directory (`/companies`)**:
  - Live interactive directory of 293 verified top-tier tech companies across Big Tech, Indian Unicorns, Trading/Quant firms, Fintech, Semiconductors, AI/ML, and Enterprise software.
  - 1-Click pre-filtered direct links for India + 0–1 Year Experience + Engineering roles.
  - Dynamic ATS vendor detection (Greenhouse, Ashby, Lever, Workday, Taleo, Oracle Cloud, Eightfold AI).
  - Ability to add new target companies with instant ATS discovery.

- **Automated 6-Hour Background Scanner**:
  - High-speed parallel scrapers hitting public ATS JSON APIs (Greenhouse, Lever, Ashby) without rate limits or bot blocks.
  - Multi-platform aggregator scanning (LinkedIn, Indeed, Google Jobs) via JobSpy.
  - In-flight intelligent filtering: drops irrelevant roles in memory and stores only verified 0–1 yr India tech jobs.

- **Zero-Duplicate Canonical Storage**:
  - SHA-256 fingerprinting on canonical keys (`company + title + url`) to prevent duplicate storage.
  - Lightweight PostgreSQL schema that remains lean, fast, and organized.

- **AI Resume Tailoring & ATS Scoring**:
  - Contextual STAR bullet-point tailoring aligned to job descriptions.
  - Strict anti-hallucination fact checks against the master career profile.

- **Kanban Application Pipeline & Analytics**:
  - Drag-and-drop tracker (Saved, Applied, Interviewing, Offer, Ghosted/Rejected).
  - Automatic 21-day employer silence ghosting detector.

---

## 🏗️ Architecture

```
jobforge/
├── backend/                  # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── api/              # REST Endpoints (jobs, companies, resumes, etc.)
│   │   ├── db/               # PostgreSQL asyncpg & SQLAlchemy models
│   │   ├── services/         # Scrapers, ATS scanners, AI intelligence
│   │   └── workers/          # Celery & scheduled recurring background tasks
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                 # Next.js 14+ (React, TypeScript, Tailwind)
│   ├── app/                  # App Router pages (/companies, /jobs, /resumes, etc.)
│   ├── components/           # Reusable UI components & Sidebar navigation
│   └── lib/                  # API client & authentication context
├── target_companies.json     # Master JSON registry of 293 verified companies
├── link.txt                  # Pre-filtered direct career links
└── docker-compose.yml        # Multi-container orchestration (DB, Redis, API, Worker)
```

---

## 🚀 Quickstart (Local Development)

### 1. Start Services via Docker Compose
```bash
docker-compose up -d
```

### 2. Manual Setup (Without Docker)

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to open the dashboard.

---

## ☁️ 100% Free Cloud Deployment

- **Frontend**: Deploy to [Vercel](https://vercel.com) (Root directory: `frontend`).
- **Backend**: Deploy to [Render](https://render.com) or [Koyeb](https://koyeb.com) (Root directory: `backend`).
- **Database**: Free PostgreSQL on [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com).
- **Scheduled 6h Scan**: Trigger via [Cron-job.org](https://cron-job.org) or GitHub Actions.

---

## 📄 License
MIT License.
