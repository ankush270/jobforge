"""SQLAlchemy ORM models for JobForge.

Unified data model covering: users, career profiles, resumes, jobs,
companies, evaluations, tailored resumes, applications, contacts,
cover letters, interviews, follow-ups, and QA bank.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid4()


# ══════════════════════════════════════════════════════════════
# Base
# ══════════════════════════════════════════════════════════════


class Base(DeclarativeBase):
    """Declarative base shared by every table."""


# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════


class AppStatus(str, enum.Enum):
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


class FactCheckStatus(str, enum.Enum):
    pending = "pending"
    passed = "passed"
    failed = "failed"
    review_required = "review_required"


# ══════════════════════════════════════════════════════════════
# USERS & PROFILES
# ══════════════════════════════════════════════════════════════


class User(Base):
    __tablename__ = "users"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    career_profile: Mapped[CareerProfile | None] = relationship(back_populates="user", uselist=False)
    resumes: Mapped[list[Resume]] = relationship(back_populates="user")
    applications: Mapped[list[Application]] = relationship(back_populates="user")


class CareerProfile(Base):
    """Master career profile — the single source of truth for anti-hallucination."""

    __tablename__ = "career_profiles"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    # {contact, summary, experience[], education[], skills[], projects[]}
    profile_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(back_populates="career_profile")


# ══════════════════════════════════════════════════════════════
# RESUMES
# ══════════════════════════════════════════════════════════════


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # Structured sections
    content_md: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    is_master: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    processing_status: Mapped[str] = mapped_column(String, default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(back_populates="resumes")
    tailored_resumes: Mapped[list[TailoredResume]] = relationship(
        back_populates="source_resume", foreign_keys="TailoredResume.source_resume_id"
    )

    __table_args__ = (
        Index(
            "ux_one_default_master",
            "user_id",
            unique=True,
            postgresql_where=text("is_default = true AND is_master = true"),
        ),
    )


# ══════════════════════════════════════════════════════════════
# COMPANIES & JOBS
# ══════════════════════════════════════════════════════════════


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    ats_vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    ats_url: Mapped[str | None] = mapped_column(String, nullable=True)
    tier: Mapped[str | None] = mapped_column(String, nullable=True)  # faang | unicorn | series_b | startup
    company_info: Mapped[dict] = mapped_column(JSON, default=dict)  # Funding, glassdoor, culture
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    jobs: Mapped[list[Job]] = relationship(back_populates="company")
    contacts: Mapped[list[Contact]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    company_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    canonical_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String, default="INR")
    job_type: Mapped[str | None] = mapped_column(String, nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String, nullable=True)
    source_platform: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Ghost/repost detection
    is_ghost: Mapped[bool] = mapped_column(Boolean, default=False)
    ghost_signals: Mapped[list] = mapped_column(JSON, default=list)
    repost_of: Mapped[Any | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    # Extracted keywords
    keywords: Mapped[dict] = mapped_column(JSON, default=dict)
    enrichment: Mapped[dict] = mapped_column(JSON, default=dict)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    company: Mapped[Company | None] = relationship(back_populates="jobs")
    evaluations: Mapped[list[JobEvaluation]] = relationship(back_populates="job")

    __table_args__ = (
        Index("idx_jobs_company", "company_id"),
        Index("idx_jobs_source", "source_platform"),
        Index("idx_jobs_created", "created_at"),
    )


# ══════════════════════════════════════════════════════════════
# EVALUATIONS & TAILORING
# ══════════════════════════════════════════════════════════════


class JobEvaluation(Base):
    """8-block A–H evaluation from oferta.md."""

    __tablename__ = "job_evaluations"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    role_match: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cv_fit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    level_strategy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    comp_research: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    personalization: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interview_prep_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    legitimacy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    work_auth: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[Any | None] = mapped_column(Numeric(5, 2), nullable=True)
    tier: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[Job] = relationship(back_populates="evaluations")

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_eval_user_job"),)


class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    source_resume_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"))
    job_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    ats_score: Mapped[Any | None] = mapped_column(Numeric(5, 2), nullable=True)
    ats_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    injectable_keywords: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    recommendations: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    preservation_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fact_check_status: Mapped[FactCheckStatus] = mapped_column(
        Enum(FactCheckStatus), default=FactCheckStatus.pending
    )
    improvements: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    source_resume: Mapped[Resume] = relationship(back_populates="tailored_resumes", foreign_keys=[source_resume_id])


# ══════════════════════════════════════════════════════════════
# APPLICATION LIFECYCLE
# ══════════════════════════════════════════════════════════════


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    tailored_resume_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tailored_resumes.id"), nullable=True
    )
    cover_letter_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cover_letters.id"), nullable=True
    )
    status: Mapped[AppStatus] = mapped_column(Enum(AppStatus), default=AppStatus.saved)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship()
    tailored_resume: Mapped[TailoredResume | None] = relationship()
    cover_letter: Mapped[CoverLetter | None] = relationship()
    status_changes: Mapped[list[StatusChange]] = relationship(back_populates="application")
    follow_ups: Mapped[list[FollowUp]] = relationship(back_populates="application")
    interviews: Mapped[list[Interview]] = relationship(back_populates="application")

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),)


class StatusChange(Base):
    __tablename__ = "status_changes"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    application_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    from_status: Mapped[AppStatus | None] = mapped_column(Enum(AppStatus), nullable=True)
    to_status: Mapped[AppStatus] = mapped_column(Enum(AppStatus), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[Application] = relationship(back_populates="status_changes")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    application_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    day_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    template_used: Mapped[str | None] = mapped_column(String, nullable=True)
    email_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")

    application: Mapped[Application] = relationship(back_populates="follow_ups")


# ══════════════════════════════════════════════════════════════
# CONTACTS & COMMUNICATION
# ══════════════════════════════════════════════════════════════


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    company: Mapped[Company | None] = relationship(back_populates="contacts")


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String, default="text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class QABankEntry(Base):
    __tablename__ = "qa_bank"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    question_key: Mapped[str] = mapped_column(String, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint("user_id", "question_key", "context", name="uq_qa_user_key_ctx"),)


# ══════════════════════════════════════════════════════════════
# INTERVIEW & SALARY
# ══════════════════════════════════════════════════════════════


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    application_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"))
    round: Mapped[int] = mapped_column(Integer, default=1)
    interview_type: Mapped[str | None] = mapped_column(String, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    prep_notes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    debrief: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    red_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    application: Mapped[Application] = relationship(back_populates="interviews")


class SalaryBenchmark(Base):
    __tablename__ = "salary_benchmarks"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    role: Mapped[str] = mapped_column(String, nullable=False)
    experience_yrs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String, default="INR")
    p25: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p50: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p75: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p90: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
