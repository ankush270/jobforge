# JobForge Browser Extension (Clipper & Autofill)

This extension provides 1-click job clipping, ghost-job signal inspection, and form autofill directly inside Chrome, Edge, and Firefox.

## Features
- **One-Click Job Clip**: Extract job title, company, description, and source URL from LinkedIn, Indeed, Greenhouse, Lever, Ashby, and custom ATS portals and send to `POST /api/jobs/clip`.
- **Match Score & 8-Block Signal Preview**: View real-time match scoring and company intel directly in the browser side panel.
- **Smart Autofill**: Auto-populates standard ATS forms (Greenhouse, Lever, Workday) using your JobForge profile and tailored CV information.

## Setup & Running

1. **Install Dependencies**:
```bash
npm install
```

2. **Run in Development Mode**:
```bash
npm run dev
```
This launches a browser instance with the extension hot-reloaded.

3. **Build for Production**:
```bash
npm run build
```
The output directory `.output/chrome-mv3` can be loaded into Chrome as an unpacked extension via `chrome://extensions` (Enable "Developer mode" -> "Load unpacked").

## Configuration
- Default backend URL: `http://localhost:8000` (FastAPI JobForge server) or `http://localhost:3000` (JobForge Next.js UI).
- Set `WXT_HIRE_ORIGIN=http://localhost:8000` in `.env.local` to point directly to your backend instance.
