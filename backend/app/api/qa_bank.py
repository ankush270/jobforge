"""Master QA Bank & Recruiter Email Drafts API."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import Job, QABankEntry, Resume
from app.dependencies import DB, CurrentUser
from app.schemas import QABankEntryCreate, QABankEntryRead
from app.services.intelligence.qa_bank import generate_form_answer, generate_recruiter_email_reply

router = APIRouter(prefix="/qa-bank", tags=["qa-bank"])


class GenerateAnswerRequest(BaseModel):
    question: str
    job_id: UUID | None = None
    resume_id: UUID | None = None
    save_to_bank: bool = True


class ReplyDraftRequest(BaseModel):
    incoming_email: str
    intent: Literal["schedule_interview", "negotiate", "decline", "follow_up"] = "schedule_interview"


@router.get("/", response_model=list[QABankEntryRead])
async def list_qa_entries(user: CurrentUser, db: DB):
    """List all saved answers in the user's master QA Bank."""
    result = await db.execute(
        select(QABankEntry).where(QABankEntry.user_id == user.id).order_by(QABankEntry.created_at.desc())
    )
    return [QABankEntryRead.model_validate(e) for e in result.scalars().all()]


@router.post("/", response_model=QABankEntryRead, status_code=status.HTTP_201_CREATED)
async def create_qa_entry(body: QABankEntryCreate, user: CurrentUser, db: DB):
    """Manually add an answer to the QA Bank."""
    entry = QABankEntry(
        user_id=user.id,
        question_key=body.question_key,
        answer=body.answer,
        context=body.context,
        is_default=body.is_default,
    )
    db.add(entry)
    await db.flush()
    return QABankEntryRead.model_validate(entry)


@router.post("/generate")
async def generate_custom_answer(body: GenerateAnswerRequest, user: CurrentUser, db: DB):
    """Generate an answer to a job application question based on user's resume."""
    # Fetch resume
    if body.resume_id:
        resume = (
            await db.execute(select(Resume).where(Resume.id == body.resume_id, Resume.user_id == user.id))
        ).scalar_one_or_none()
    else:
        resume = (
            await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.is_master.desc()))
        ).scalars().first()

    resume_content = resume.content if resume else {"contact": {"name": user.name or "Candidate"}, "skills": []}

    # Fetch job description if provided
    jd = None
    if body.job_id:
        job = (await db.execute(select(Job).where(Job.id == body.job_id))).scalar_one_or_none()
        if job:
            jd = job.description

    answer = await generate_form_answer(
        question=body.question,
        resume_content=resume_content,
        job_description=jd,
    )

    if body.save_to_bank:
        q_key = body.question[:80]
        existing = (
            await db.execute(
                select(QABankEntry).where(
                    QABankEntry.user_id == user.id,
                    QABankEntry.question_key == q_key,
                    QABankEntry.context == body.question,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.answer = answer
        else:
            entry = QABankEntry(
                user_id=user.id,
                question_key=q_key,
                answer=answer,
                context=body.question,
            )
            db.add(entry)
        await db.flush()

    return {
        "question": body.question,
        "answer": answer,
        "saved": body.save_to_bank,
    }


@router.post("/reply-draft")
async def draft_recruiter_reply(body: ReplyDraftRequest, user: CurrentUser):
    """Draft an instant reply to a recruiter or interview scheduling email."""
    draft = await generate_recruiter_email_reply(
        incoming_email=body.incoming_email,
        intent=body.intent,
        candidate_name=user.name or "Candidate",
    )
    return {
        "intent": body.intent,
        "email_draft": draft,
    }


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qa_entry(entry_id: UUID, user: CurrentUser, db: DB):
    """Delete an entry from the QA Bank."""
    entry = (
        await db.execute(select(QABankEntry).where(QABankEntry.id == entry_id, QABankEntry.user_id == user.id))
    ).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
