"""Pydantic schemas for request/response validation.

Mirrors the ORM models but strictly separates input (Create/Update)
from output (Read) shapes. Frontend TypeScript types are generated from these.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ══════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    email: str
    name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ══════════════════════════════════════════════════
# Career Profile
# ══════════════════════════════════════════════════


class CareerProfileCreate(BaseModel):
    profile_json: dict[str, Any]
    raw_text: str | None = None


class CareerProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    profile_json: dict[str, Any]
    raw_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════
# Resume
# ══════════════════════════════════════════════════


class ResumeSection(BaseModel):
    """A single resume section (experience, education, etc.)."""
    section_type: str  # summary | workExperience | education | skills | projects | custom
    title: str | None = None
    items: list[dict[str, Any]] = []


class ResumeCreate(BaseModel):
    content: dict[str, Any]
    content_md: str | None = None
    is_master: bool = False
    filename: str | None = None


class ResumeUpdate(BaseModel):
    content: dict[str, Any] | None = None
    content_md: str | None = None
    is_default: bool | None = None


class ResumeRead(BaseModel):
    id: UUID
    user_id: UUID
    content: dict[str, Any]
    content_md: str | None
    is_master: bool
    is_default: bool
    parent_id: UUID | None
    filename: str | None
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    resume: ResumeRead
    career_profile: CareerProfileRead | None = None
    message: str = "Resume parsed successfully"


# ══════════════════════════════════════════════════
# Company
# ══════════════════════════════════════════════════


class CompanyRead(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None
    ats_vendor: str | None
    tier: str | None
    company_info: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class TargetCompanyCreate(BaseModel):
    name: str
    careers_url: str
    category: str = "Tech / Product"
    locations_in_india: list[str] = ["India / Remote"]


class TargetCompanyRead(BaseModel):
    name: str
    category: str
    careers_url: str
    ats_or_portal: str | None = "Direct Portal"
    locations_in_india: list[str] = ["India / Remote"]
    status: str = "verified"


# ══════════════════════════════════════════════════
# Job
# ══════════════════════════════════════════════════


class JobCreate(BaseModel):
    title: str
    company_name: str
    description: str
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "INR"
    job_type: str | None = None
    remote_type: str | None = None
    source_platform: str = "manual"
    source_url: str | None = None


class JobRead(BaseModel):
    id: UUID
    company_id: UUID | None
    canonical_key: str
    title: str
    description: str
    location: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    job_type: str | None
    remote_type: str | None
    source_platform: str
    source_url: str | None
    posted_at: datetime | None
    is_ghost: bool
    ghost_signals: list
    is_alive: bool
    keywords: dict[str, Any]
    enrichment: dict[str, Any]
    created_at: datetime
    company: CompanyRead | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobRead]
    total: int
    page: int
    page_size: int


class JobScrapeRequest(BaseModel):
    """Trigger a scraping run."""
    platforms: list[str] = ["linkedin", "indeed"]
    search_query: str
    location: str | None = "India"
    results_wanted: int = 25
    filter_entry_india: bool = True
    scan_target_companies: bool = False


class JobClipRequest(BaseModel):
    """Browser extension job clip."""
    title: str
    company_name: str
    description: str
    source_url: str
    source_platform: str = "linkedin"
    location: str | None = None
    salary_text: str | None = None


# ══════════════════════════════════════════════════
# ATS Score & Tailoring
# ══════════════════════════════════════════════════


class ATSScoreResponse(BaseModel):
    overall_score: float
    sub_scores: dict[str, float]
    missing_keywords: list[str]
    injectable_keywords: list[str]
    recommendations: list[str]


class TailorRequest(BaseModel):
    resume_id: UUID
    job_id: UUID


class TailoredResumeRead(BaseModel):
    id: UUID
    user_id: UUID
    source_resume_id: UUID
    job_id: UUID
    content: dict[str, Any]
    content_md: str | None
    ats_score: float | None
    ats_breakdown: dict | None
    missing_keywords: list[str] | None
    injectable_keywords: list[str] | None
    recommendations: list[str] | None
    preservation_log: dict | None
    fact_check_status: str
    improvements: list
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════
# Application / Kanban
# ══════════════════════════════════════════════════


class AppStatusEnum(str, Enum):
    saved = "saved"
    evaluating = "evaluating"
    tailoring = "tailoring"
    ready = "ready"
    applied = "applied"
    screening = "screening"
    interview_scheduled = "interview_scheduled"
    interviewing = "interviewing"
    offer_received = "offer_received"
    negotiating = "negotiating"
    accepted = "accepted"
    rejected = "rejected"
    ghosted = "ghosted"
    withdrawn = "withdrawn"
    archived = "archived"


class ApplicationCreate(BaseModel):
    job_id: UUID
    tailored_resume_id: UUID | None = None
    cover_letter_id: UUID | None = None
    status: AppStatusEnum = AppStatusEnum.saved
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: AppStatusEnum | None = None
    notes: str | None = None
    position: int | None = None
    tailored_resume_id: UUID | None = None
    cover_letter_id: UUID | None = None


class ApplicationRead(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    tailored_resume_id: UUID | None
    cover_letter_id: UUID | None
    status: str
    applied_at: datetime | None
    notes: str | None
    position: int
    created_at: datetime
    updated_at: datetime
    job: JobRead | None = None

    model_config = {"from_attributes": True}


class KanbanBoardResponse(BaseModel):
    columns: dict[str, list[ApplicationRead]]
    stats: dict[str, int]


# ══════════════════════════════════════════════════
# Cover Letter
# ══════════════════════════════════════════════════


class CoverLetterCreate(BaseModel):
    job_id: UUID
    content: str | None = None  # If None, auto-generate


class CoverLetterRead(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    content: str
    format: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════
# Interview
# ══════════════════════════════════════════════════


class InterviewCreate(BaseModel):
    application_id: UUID
    round: int = 1
    interview_type: str | None = None
    scheduled_at: datetime | None = None


class InterviewRead(BaseModel):
    id: UUID
    application_id: UUID
    round: int
    interview_type: str | None
    scheduled_at: datetime | None
    prep_notes: dict | None
    debrief: str | None
    outcome: str | None
    red_flags: list
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════
# Analytics
# ══════════════════════════════════════════════════


class FunnelStats(BaseModel):
    total_applied: int = 0
    saved: int = 0
    screening: int = 0
    interviewing: int = 0
    offers: int = 0
    rejected: int = 0
    ghosted: int = 0
    screen_rate: float | None = None
    offer_rate: float | None = None
    avg_days_to_screen: float | None = None
    avg_days_to_reject: float | None = None
    ghost_risk_count: int = 0


class QABankEntryCreate(BaseModel):
    question_key: str
    answer: str
    context: str | None = None
    is_default: bool = False


class QABankEntryRead(BaseModel):
    id: UUID
    question_key: str
    answer: str
    context: str | None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    name: str
    company_id: UUID | None = None
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    source: str | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID | None
    company_name: str | None = None
    name: str
    title: str | None
    email: str | None
    linkedin_url: str | None
    source: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

