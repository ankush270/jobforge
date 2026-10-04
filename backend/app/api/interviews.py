"""Interviews API: interview prep pack generation, STAR answers, debrief."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.models import Application, Interview, Job, Resume
from app.dependencies import DB, CurrentUser
from app.schemas import InterviewRead
from app.services.intelligence.interview_prep import generate_interview_prep_pack

router = APIRouter(prefix="/interviews", tags=["interviews"])


class GenerateInterviewPrepRequest(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None
    application_id: UUID | None = None
    round: int = 1
    interview_type: str = "technical"


class UpdateInterviewRequest(BaseModel):
    prep_notes: dict | None = None
    debrief: str | None = None
    outcome: str | None = None
    red_flags: list[str] | None = None


@router.post("/prep", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
async def create_interview_prep(body: GenerateInterviewPrepRequest, user: CurrentUser, db: DB):
    """Generate role-specific interview prep pack with STAR stories & reverse questions."""
    # 1. Fetch job with company
    job = (
        await db.execute(
            select(Job).options(joinedload(Job.company)).where(Job.id == body.job_id)
        )
    ).unique().scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. Fetch resume
    if body.resume_id:
        resume = (
            await db.execute(select(Resume).where(Resume.id == body.resume_id, Resume.user_id == user.id))
        ).scalar_one_or_none()
    else:
        resume = (
            await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.is_master.desc()))
        ).scalars().first()

    if not resume:
        raise HTTPException(status_code=400, detail="No resume found. Please upload a resume first.")

    # 3. Ensure Application exists
    app_id = body.application_id
    if not app_id:
        existing_app = (
            await db.execute(select(Application).where(Application.user_id == user.id, Application.job_id == job.id))
        ).scalar_one_or_none()
        if existing_app:
            app_id = existing_app.id
        else:
            new_app = Application(user_id=user.id, job_id=job.id, status="interviewing")
            db.add(new_app)
            await db.flush()
            app_id = new_app.id

    # 4. Generate prep pack
    company_name = job.company.name if job.company else "the hiring company"
    prep_pack = await generate_interview_prep_pack(
        job_title=job.title,
        company_name=company_name,
        job_description=job.description,
        resume_content=resume.content,
    )

    # 5. Save Interview record
    interview = Interview(
        application_id=app_id,
        round=body.round,
        interview_type=body.interview_type,
        prep_notes=prep_pack,
        red_flags=prep_pack.get("culture_red_flags_to_watch", []),
    )
    db.add(interview)
    await db.flush()

    return InterviewRead.model_validate(interview)


@router.get("/", response_model=list[InterviewRead])
async def list_interviews(user: CurrentUser, db: DB):
    """List all interview preps for the current user."""
    result = await db.execute(
        select(Interview)
        .join(Application)
        .where(Application.user_id == user.id)
        .order_by(Interview.created_at.desc())
    )
    return [InterviewRead.model_validate(i) for i in result.scalars().all()]


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(interview_id: UUID, user: CurrentUser, db: DB):
    """Get interview prep details."""
    result = await db.execute(
        select(Interview)
        .join(Application)
        .where(Interview.id == interview_id, Application.user_id == user.id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview prep not found")
    return InterviewRead.model_validate(interview)


@router.patch("/{interview_id}", response_model=InterviewRead)
async def update_interview(interview_id: UUID, body: UpdateInterviewRequest, user: CurrentUser, db: DB):
    """Update debrief notes or interview outcome."""
    result = await db.execute(
        select(Interview)
        .join(Application)
        .where(Interview.id == interview_id, Application.user_id == user.id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if body.prep_notes is not None:
        interview.prep_notes = body.prep_notes
    if body.debrief is not None:
        interview.debrief = body.debrief
    if body.outcome is not None:
        interview.outcome = body.outcome
    if body.red_flags is not None:
        interview.red_flags = body.red_flags

    await db.flush()
    return InterviewRead.model_validate(interview)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(interview_id: UUID, user: CurrentUser, db: DB):
    """Delete interview record."""
    result = await db.execute(
        select(Interview)
        .join(Application)
        .where(Interview.id == interview_id, Application.user_id == user.id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    await db.delete(interview)
