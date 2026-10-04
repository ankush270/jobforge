"""Contacts & Recruiter Finder API (Feature #12).

Manages recruiter/hiring manager network, seeds LinkedIn messages,
and links recruiters to job applications and companies.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.models import Company, Contact
from app.dependencies import DB, CurrentUser
from app.schemas import ContactCreate, ContactRead
from app.ai.llm_router import complete
from app.services.intelligence.tailor import sanitize_ai_text

router = APIRouter(prefix="/contacts", tags=["contacts"])


class RecruiterPitchRequest(BaseModel):
    contact_name: str
    contact_title: str | None = None
    company_name: str
    target_role: str
    candidate_skills: list[str] | None = None


@router.get("/", response_model=list[ContactRead])
async def list_contacts(
    user: CurrentUser,
    db: DB,
    company_id: UUID | None = Query(None),
):
    """List recruiter and hiring manager contacts."""
    query = (
        select(Contact)
        .options(joinedload(Contact.company))
        .where(Contact.user_id == user.id)
    )
    if company_id:
        query = query.where(Contact.company_id == company_id)
    query = query.order_by(Contact.created_at.desc())

    result = await db.execute(query)
    contacts_list = result.unique().scalars().all()
    return [
        ContactRead(
            id=c.id,
            user_id=c.user_id,
            company_id=c.company_id,
            company_name=c.company.name if c.company else None,
            name=c.name,
            title=c.title,
            email=c.email,
            linkedin_url=c.linkedin_url,
            source=c.source,
            notes=c.notes,
            created_at=c.created_at,
        )
        for c in contacts_list
    ]


@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactCreate, user: CurrentUser, db: DB):
    """Add a recruiter, hiring manager, or insider connection."""
    contact = Contact(
        user_id=user.id,
        company_id=body.company_id,
        name=body.name,
        title=body.title,
        email=body.email,
        linkedin_url=body.linkedin_url,
        source=body.source or "manual",
        notes=body.notes,
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact, attribute_names=["company"])
    return ContactRead(
        id=contact.id,
        user_id=contact.user_id,
        company_id=contact.company_id,
        company_name=contact.company.name if contact.company else None,
        name=contact.name,
        title=contact.title,
        email=contact.email,
        linkedin_url=contact.linkedin_url,
        source=contact.source,
        notes=contact.notes,
        created_at=contact.created_at,
    )


@router.post("/draft-pitch")
async def draft_recruiter_pitch(body: RecruiterPitchRequest, user: CurrentUser):
    """Draft a high-conversion, concise (under 300 characters) LinkedIn InMail or connection note."""
    skills_text = ", ".join(body.candidate_skills[:3]) if body.candidate_skills else "software engineering"

    system_prompt = (
        "You are an executive talent strategist drafting high-converting recruiter messages.\n"
        "Draft a crisp LinkedIn connection message under 300 characters total. "
        "Do NOT use buzzwords like 'spearheaded' or 'synergized'. No em dashes."
    )

    prompt = f"""Recruiter: {body.contact_name} ({body.contact_title or 'Recruiter'}) at {body.company_name}
Target Role: {body.target_role}
Candidate Name: {user.name or 'Candidate'}
Candidate Strengths: {skills_text}

Draft:
1. Short LinkedIn Connection Note (strictly under 300 characters)
2. InMail / Email Version (under 100 words)
"""

    try:
        draft = await complete(prompt=prompt, system=system_prompt, temperature=0.3)
        return {
            "pitch_text": sanitize_ai_text(draft),
            "contact_name": body.contact_name,
            "company_name": body.company_name,
        }
    except Exception as e:
        return {
            "pitch_text": (
                f"Hi {body.contact_name}, I saw your work hiring at {body.company_name} and wanted to connect! "
                f"With strong experience in {skills_text}, I'm following the {body.target_role} opening and would love to stay in touch."
            ),
            "contact_name": body.contact_name,
            "company_name": body.company_name,
        }


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: UUID, user: CurrentUser, db: DB):
    """Delete a recruiter contact."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
