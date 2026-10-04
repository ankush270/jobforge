'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Layers,
  Search,
  FileText,
  Kanban,
  Target,
  ShieldCheck,
  Zap,
  ArrowRight,
  CheckCircle2,
  Mic,
  DollarSign,
  Mail,
  Ghost,
  ChevronDown,
  ChevronUp,
  BarChart3,
  BookOpen,
  Code2,
  Terminal,
  Cpu,
  Database,
  ArrowUpRight,
} from 'lucide-react';

export default function LandingPage() {
  const [activeStep, setActiveStep] = useState(1);
  const [faqOpen, setFaqOpen] = useState<number | null>(null);

  const toggleFaq = (idx: number) => {
    setFaqOpen(faqOpen === idx ? null : idx);
  };

  const steps = [
    {
      step: 1,
      tag: '01 / INGEST',
      title: 'Upload & Parse Master Resume',
      subtitle: 'Extract JSON schema and immutable career facts',
      icon: FileText,
      description:
        'Upload your existing PDF or DOCX file. The parsing pipeline extracts structured JSON across contact info, work history, skill taxonomy, and project metrics. This data forms your immutable master profile.',
      exampleBefore: 'Handled database maintenance and updated backend APIs.',
      exampleAfter:
        'Architected PostgreSQL connection pooling and indexing, decreasing P95 query latency by 43% across 12M daily queries.',
      bullets: [
        'Deterministic parsing into structured Pydantic / JSON schema',
        'Skills taxonomy classification across 200+ technical categories',
        'Ground-truth facts preserved for the Anti-Hallucination Guard',
      ],
      actionText: 'Open Master Resumes',
      actionHref: '/resumes',
    },
    {
      step: 2,
      tag: '02 / DISCOVER',
      title: 'Scrape Direct ATS Portals',
      subtitle: 'Index verified openings & flag ghost reposts',
      icon: Search,
      description:
        'Query live career endpoints across Greenhouse, Lever, Ashby, Workable, LinkedIn, and Indeed. Canonical fingerprinting deduplicates identical cross-board postings, while the repost detector flags roles idle for >60 days.',
      bullets: [
        'Direct company ATS endpoint verification (no aggregator lag)',
        'Canonical hash deduplication across multiple job boards',
        'Ghost job heuristic scoring based on posting age and repost history',
      ],
      actionText: 'Open Jobs Feed',
      actionHref: '/jobs',
    },
    {
      step: 3,
      tag: '03 / TAILOR',
      title: 'STAR Bullet Optimization',
      subtitle: 'Target ATS keywords with verified metrics',
      icon: Code2,
      description:
        'Select a master resume and target job description. The tailoring engine extracts required skill tokens, computes a multi-factor ATS match score (0-100%), and rewrites generic bullets into structured STAR accomplishment statements.',
      bullets: [
        'Anti-Hallucination Guard prevents fabrication of unverified skills',
        'Token density and semantic relevance analysis against target JD',
        'Dual compilation: ATS-clean PDF and raw compile-ready LaTeX export',
      ],
      actionText: 'Launch Resume Tailor',
      actionHref: '/tailor',
    },
    {
      step: 4,
      tag: '04 / OUTREACH',
      title: 'Targeted Letters & Recruiter Cadences',
      subtitle: 'Evidence-based writing and follow-up schedule',
      icon: Mail,
      description:
        'Generate focused cover letters connecting your past deliverables directly to the engineering team’s stated requirements. Automatically construct 3-step recruiter cold email cadences with recommended send intervals.',
      bullets: [
        'Style matching based on team structure (Enterprise, Startup, Series A-C)',
        '3-step recruiter email sequence with contextual follow-up hooks',
        'Technical QA Bank for custom application screening questionnaires',
      ],
      actionText: 'Generate Cover Letter',
      actionHref: '/cover-letter',
    },
    {
      step: 5,
      tag: '05 / TRACK',
      title: 'Kanban Pipeline Tracking',
      subtitle: 'Stage velocity and lead activity tracking',
      icon: Kanban,
      description:
        'Manage opportunities across five distinct pipeline stages: Saved, Applied, Screening, Interviewing, and Offers. Monitor real-time screen rates, response time metrics, and follow-up deadlines.',
      bullets: [
        'Structured kanban columns matching real recruitment lifecycles',
        'Funnel conversion analytics measuring screen-to-interview rates',
        'Stale lead reminders for applications pending >30 days',
      ],
      actionText: 'View Kanban Board',
      actionHref: '/applications',
    },
    {
      step: 6,
      tag: '06 / NEGOTIATE',
      title: 'Interview STAR Bank & Comp Benchmarks',
      subtitle: 'Role questions and compensation data',
      icon: DollarSign,
      description:
        'Practice role-specific technical and behavioral questions derived directly from your tailored resume bullets. Benchmark compensation percentiles (25th, 50th, 75th, 90th) and review tactical negotiation playbooks.',
      bullets: [
        'Behavioral questions paired with your verified STAR evidence',
        'Compensation percentiles partitioned by role seniority and location',
        'Scripts for equity grants, sign-on adjustments, and counter-offers',
      ],
      actionText: 'Open Interview Prep',
      actionHref: '/interview-prep',
    },
  ];

  const features = [
    {
      icon: Search,
      title: 'Direct ATS Crawler',
      category: 'Ingestion Engine',
      description:
        'Queries Greenhouse, Lever, Ashby, and Workable career boards directly. Eliminates aggregator noise and expired listings.',
    },
    {
      icon: ShieldCheck,
      title: 'Anti-Hallucination Guard',
      category: 'Data Integrity',
      description:
        'Restricts AI generation to your verified master resume JSON. Ensures zero fabricated tools, metrics, or credentials.',
    },
    {
      icon: Code2,
      title: 'STAR Bullet Reformulator',
      category: 'Tailoring Core',
      description:
        'Transforms responsibilities into Situation-Task-Action-Result statements calibrated to target ATS keyword density.',
    },
    {
      icon: Ghost,
      title: 'Ghost Job Detector',
      category: 'Market Filter',
      description:
        'Calculates posting velocity and repost cadence to identify perpetually open roles that rarely result in interviews.',
    },
    {
      icon: Kanban,
      title: 'Kanban Stage Tracker',
      category: 'Pipeline Manager',
      description:
        'Monitors application movement through Saved, Applied, Screening, Interviewing, and Offers with conversion stats.',
    },
    {
      icon: Mail,
      title: 'Outreach Cadence Builder',
      category: 'Recruiter Outreach',
      description:
        'Constructs structured 3-touch cold email sequences mapped to hiring managers and technical recruiters.',
    },
    {
      icon: Mic,
      title: 'Resume STAR Question Bank',
      category: 'Interview Engine',
      description:
        'Generates behavioral and situational interview questions grounded in your specific tailored accomplishment points.',
    },
    {
      icon: DollarSign,
      title: 'Compensation Benchmarks',
      category: 'Salary Intelligence',
      description:
        'Provides salary percentiles and counter-offer scripts for base salary, equity vesting, and sign-on incentives.',
    },
  ];

  const faqs = [
    {
      q: 'How does the Anti-Hallucination Guard ensure factual correctness?',
      a: 'Generic LLMs often fabricate skills or past company experiences to maximize keyword matching. JobForge validates all generated text against your immutable parsed master resume JSON. If a skill, company, or metric does not exist in your source profile, it cannot be injected into your tailored documents.',
    },
    {
      q: 'Which applicant tracking systems (ATS) are directly supported?',
      a: 'The scraping and parsing engines directly interface with Greenhouse, Lever, Ashby, Workable, SmartRecruiters, LinkedIn, and Indeed endpoints. ATS score algorithms simulate standard keyword parsing and token density rules.',
    },
    {
      q: 'What formats can I export tailored resumes to?',
      a: 'You can export resumes as clean, standard-compliant ATS PDFs or download full LaTeX (.tex) source files ready for compilation in your local TeX environment or Overleaf.',
    },
    {
      q: 'How does the Ghost Job Detector work?',
      a: 'The detector evaluates the job listing posting timestamp, historical repost cadence, company turnover signals, and cross-platform duplication. Listings that remain open for extended durations without hiring are flagged with a ghost indicator.',
    },
  ];

  return (
    <div className="landing-page-root">
      {/* ── Top Navigation Bar ── */}
      <header className="landing-header">
        <div className="landing-nav-container">
          <Link href="/" className="landing-brand">
            <div className="topbar-logo-icon">
              <Layers size={14} />
            </div>
            <span className="landing-brand-text">JobForge</span>
            <span className="topbar-badge">DOCUMENTATION</span>
          </Link>

          <nav className="landing-nav-links">
            <a href="#how-to-use" className="landing-nav-link">
              Workflow Guide
            </a>
            <a href="#features" className="landing-nav-link">
              Architecture
            </a>
            <a href="#comparison" className="landing-nav-link">
              Specifications
            </a>
            <a href="#faq" className="landing-nav-link">
              FAQ
            </a>
          </nav>

          <div className="landing-header-actions">
            <Link href="/" className="btn btn-secondary btn-sm">
              Command Center
            </Link>
            <Link href="/jobs" className="btn btn-primary btn-sm">
              <span>Jobs Feed</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </header>

      {/* ── Technical Overview Hero ── */}
      <section className="landing-hero-section">
        <div className="landing-hero-content">
          <div className="page-badge">
            <Terminal size={12} style={{ color: 'var(--accent)' }} />
            <span>OPERATIONAL SPECIFICATIONS &middot; ARCHITECTURE</span>
          </div>

          <h1 className="landing-hero-title">
            Direct ATS Search &amp; <br />
            Targeted Resume Optimization
          </h1>

          <p className="landing-hero-subtitle">
            JobForge connects directly to company job boards (Greenhouse, Lever, Ashby), checks job posting
            liveness, and tailors STAR bullet points to match ATS keywords without hallucinating unverified
            experience.
          </p>

          <div className="landing-hero-cta-group">
            <Link href="/" className="btn btn-primary">
              <Terminal size={14} />
              <span>Launch Command Center</span>
            </Link>
            <a href="#how-to-use" className="btn btn-secondary">
              <BookOpen size={14} />
              <span>Read Workflow Manual</span>
            </a>
          </div>

          {/* Metrics Overview */}
          <div className="landing-metrics-bar">
            <div className="landing-metric-item">
              <span className="landing-metric-num">100+</span>
              <span className="landing-metric-label">Direct ATS Endpoints</span>
            </div>
            <div className="landing-metric-divider" />
            <div className="landing-metric-item">
              <span className="landing-metric-num">0%</span>
              <span className="landing-metric-label">Hallucinated Facts</span>
            </div>
            <div className="landing-metric-divider" />
            <div className="landing-metric-item">
              <span className="landing-metric-num">0–100%</span>
              <span className="landing-metric-label">ATS Scoring Matrix</span>
            </div>
            <div className="landing-metric-divider" />
            <div className="landing-metric-item">
              <span className="landing-metric-num">5 Stages</span>
              <span className="landing-metric-label">Kanban Tracking</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── "HOW TO USE" STEP-BY-STEP WORKFLOW ── */}
      <section id="how-to-use" className="landing-section">
        <div className="landing-section-header">
          <div className="page-badge">
            <Target size={12} style={{ color: 'var(--accent)' }} />
            <span>WORKFLOW MANUAL</span>
          </div>
          <h2 className="landing-section-title">End-to-End Application Workflow</h2>
          <p className="landing-section-desc">
            How to operate JobForge from initial resume ingestion through ATS keyword alignment to offer
            negotiation.
          </p>
        </div>

        <div className="landing-steps-container">
          {/* Step Selector List */}
          <div className="landing-steps-nav">
            {steps.map((s) => {
              const Icon = s.icon;
              const isSelected = activeStep === s.step;
              return (
                <button
                  key={s.step}
                  type="button"
                  className={`landing-step-tab ${isSelected ? 'active' : ''}`}
                  onClick={() => setActiveStep(s.step)}
                >
                  <div className="landing-step-tab-num">{s.step}</div>
                  <div className="landing-step-tab-info">
                    <span className="landing-step-tab-title">{s.title}</span>
                    <span className="landing-step-tab-sub">{s.subtitle}</span>
                  </div>
                  <Icon size={15} className="landing-step-tab-icon" />
                </button>
              );
            })}
          </div>

          {/* Active Step Documentation Card */}
          {(() => {
            const current = steps.find((s) => s.step === activeStep) || steps[0];
            const StepIcon = current.icon;
            return (
              <div className="landing-step-card">
                <div className="landing-step-card-header">
                  <div className="landing-step-card-badge">
                    <StepIcon size={13} style={{ color: 'var(--accent)' }} />
                    <span>{current.tag}</span>
                  </div>
                  <span className="landing-step-card-indicator">Step {current.step} / 6</span>
                </div>

                <h3 className="landing-step-card-title">{current.title}</h3>
                <p className="landing-step-card-desc">{current.description}</p>

                {/* Concrete transformation example if available */}
                {current.exampleBefore && (
                  <div className="landing-step-example-box">
                    <div className="landing-example-row">
                      <span className="landing-example-tag before">Standard Input</span>
                      <p className="landing-example-text">{current.exampleBefore}</p>
                    </div>
                    <div className="landing-example-row">
                      <span className="landing-example-tag after">STAR Optimized</span>
                      <p className="landing-example-text">{current.exampleAfter}</p>
                    </div>
                  </div>
                )}

                <div className="landing-step-card-bullets">
                  <div className="landing-step-card-bullets-label">Operational Requirements:</div>
                  {current.bullets.map((b, i) => (
                    <div key={i} className="landing-step-bullet-row">
                      <CheckCircle2 size={14} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: '2px' }} />
                      <span>{b}</span>
                    </div>
                  ))}
                </div>

                <div className="landing-step-card-footer">
                  <Link href={current.actionHref} className="btn btn-primary btn-sm">
                    <span>{current.actionText}</span>
                    <ArrowRight size={13} />
                  </Link>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setActiveStep((prev) => (prev > 1 ? prev - 1 : 6))}
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setActiveStep((prev) => (prev < 6 ? prev + 1 : 1))}
                    >
                      Next Step
                    </button>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      </section>

      {/* ── ARCHITECTURAL SYSTEMS ── */}
      <section id="features" className="landing-section">
        <div className="landing-section-header">
          <div className="page-badge">
            <Cpu size={12} style={{ color: 'var(--accent)' }} />
            <span>CORE SUBSYSTEMS</span>
          </div>
          <h2 className="landing-section-title">System Architecture</h2>
          <p className="landing-section-desc">
            Eight functional modules built to execute scraping, parsing, tailoring, and pipeline management.
          </p>
        </div>

        <div className="landing-features-grid">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="landing-feature-card">
                <div className="landing-feature-header">
                  <div className="landing-feature-icon-wrap">
                    <Icon size={16} />
                  </div>
                  <span className="sidebar-pill-badge neutral">{feat.category}</span>
                </div>
                <h3 className="landing-feature-title">{feat.title}</h3>
                <p className="landing-feature-desc">{feat.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── TECHNICAL COMPARISON ── */}
      <section id="comparison" className="landing-section">
        <div className="landing-section-header">
          <div className="page-badge">
            <Database size={12} style={{ color: 'var(--accent)' }} />
            <span>OPERATIONAL SPECIFICATIONS</span>
          </div>
          <h2 className="landing-section-title">Feature Comparison</h2>
          <p className="landing-section-desc">
            Direct comparison between generic aggregator searching and JobForge structured workflows.
          </p>
        </div>

        <div className="landing-table-wrap">
          <table className="landing-table">
            <thead>
              <tr>
                <th>Workflow Component</th>
                <th>Standard Job Searching</th>
                <th className="highlight-col">JobForge Engine</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="row-title">Job Ingestion</td>
                <td className="dim-text">Manual portal scraping with 30%+ expired ghost listings.</td>
                <td className="highlight-col">Direct ATS board query with canonical deduplication and liveness verification.</td>
              </tr>
              <tr>
                <td className="row-title">Resume Customization</td>
                <td className="dim-text">One generic PDF sent broadly, or slow manual rewriting per listing.</td>
                <td className="highlight-col">STAR bullet reformulator matching target JD token frequency.</td>
              </tr>
              <tr>
                <td className="row-title">Factual Integrity</td>
                <td className="dim-text">LLM prompts that invent skills, tools, and employment dates.</td>
                <td className="highlight-col">Anti-Hallucination Guard constrained by master resume JSON.</td>
              </tr>
              <tr>
                <td className="row-title">Application Lifecycle</td>
                <td className="dim-text">Disconnected spreadsheets with untracked follow-up intervals.</td>
                <td className="highlight-col">Visual Kanban tracking screen rate conversion and 30-day stale lead alerts.</td>
              </tr>
              <tr>
                <td className="row-title">Interview Readiness</td>
                <td className="dim-text">Uncorrelated generic questions found through web searches.</td>
                <td className="highlight-col">Behavioral question bank derived directly from your tailored bullets.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section id="faq" className="landing-section">
        <div className="landing-section-header">
          <div className="page-badge">
            <BookOpen size={12} style={{ color: 'var(--accent)' }} />
            <span>TECHNICAL FAQ</span>
          </div>
          <h2 className="landing-section-title">Frequently Asked Questions</h2>
          <p className="landing-section-desc">
            Architecture details regarding parsing integrity, ATS scoring, and export formats.
          </p>
        </div>

        <div className="landing-faq-list">
          {faqs.map((faq, idx) => {
            const isOpen = faqOpen === idx;
            return (
              <div key={idx} className={`landing-faq-item ${isOpen ? 'open' : ''}`}>
                <button
                  type="button"
                  className="landing-faq-question"
                  onClick={() => toggleFaq(idx)}
                >
                  <span>{faq.q}</span>
                  {isOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </button>
                {isOpen && <div className="landing-faq-answer">{faq.a}</div>}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── BOTTOM CTA ── */}
      <section className="landing-cta-banner">
        <div className="landing-cta-content">
          <h2 className="landing-cta-title">Access JobForge Command Center</h2>
          <p className="landing-cta-subtitle">
            Begin indexing openings, auditing ATS fit scores, and managing your active pipeline.
          </p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link href="/" className="btn btn-primary">
              <span>Open Command Center</span>
              <ArrowRight size={13} />
            </Link>
            <Link href="/resumes" className="btn btn-secondary">
              <span>Upload Master Resume</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="landing-footer">
        <div className="landing-footer-container">
          <div className="landing-footer-brand">
            <div className="topbar-logo-icon">
              <Layers size={13} />
            </div>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>JobForge</span>
          </div>
          <p className="landing-footer-text">
            Autonomous career intelligence and ATS application engine.
          </p>
          <div className="landing-footer-links">
            <Link href="/" className="landing-footer-link">
              Command Center
            </Link>
            <Link href="/jobs" className="landing-footer-link">
              Jobs Feed
            </Link>
            <Link href="/tailor" className="landing-footer-link">
              STAR Tailor
            </Link>
            <Link href="/applications" className="landing-footer-link">
              Kanban
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
