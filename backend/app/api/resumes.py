"""Resume CRUD API: upload, parse, list, update, delete."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.db.models import CareerProfile, Resume
from app.dependencies import DB, CurrentUser
from app.schemas import (
    CareerProfileRead,
    ResumeCreate,
    ResumeRead,
    ResumeUpdate,
    ResumeUploadResponse,
)
from app.services.intelligence.parser import parse_resume_file

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile, user: CurrentUser, db: DB):
    """Upload a PDF/DOCX resume → parse to structured JSON → store as master resume."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content_bytes = await file.read()
    parsed = await parse_resume_file(content_bytes, ext)

    # Create the resume record
    resume = Resume(
        user_id=user.id,
        content=parsed["structured"],
        content_md=parsed.get("markdown"),
        is_master=True,
        is_default=True,
        filename=file.filename,
        processing_status="done",
    )
    db.add(resume)

    # Upsert the career profile (master source of truth for anti-hallucination)
    result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        profile.profile_json = parsed["structured"]
        profile.raw_text = parsed.get("raw_text", "")
    else:
        profile = CareerProfile(
            user_id=user.id,
            profile_json=parsed["structured"],
            raw_text=parsed.get("raw_text", ""),
        )
        db.add(profile)

    await db.flush()

    return ResumeUploadResponse(
        resume=ResumeRead.model_validate(resume),
        career_profile=CareerProfileRead.model_validate(profile),
    )


@router.post("/", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume(body: ResumeCreate, user: CurrentUser, db: DB):
    """Create a resume from structured JSON (no file upload)."""
    resume = Resume(
        user_id=user.id,
        content=body.content,
        content_md=body.content_md,
        is_master=body.is_master,
        filename=body.filename,
        processing_status="done",
    )
    db.add(resume)
    await db.flush()
    return ResumeRead.model_validate(resume)


@router.get("/", response_model=list[ResumeRead])
async def list_resumes(user: CurrentUser, db: DB):
    """List all resumes for the current user."""
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
    )
    return [ResumeRead.model_validate(r) for r in result.scalars().all()]


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(resume_id: UUID, user: CurrentUser, db: DB):
    """Get a single resume by ID."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeRead.model_validate(resume)


@router.patch("/{resume_id}", response_model=ResumeRead)
async def update_resume(resume_id: UUID, body: ResumeUpdate, user: CurrentUser, db: DB):
    """Update resume content or settings."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if body.content is not None:
        resume.content = body.content
    if body.content_md is not None:
        resume.content_md = body.content_md
    if body.is_default is not None:
        resume.is_default = body.is_default

    await db.flush()
    return ResumeRead.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: UUID, user: CurrentUser, db: DB):
    """Delete a resume."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    await db.delete(resume)


@router.get("/{resume_id}/pdf")
async def download_resume_pdf(resume_id: UUID, user: CurrentUser, db: DB):
    """Generate and download ATS-compliant PDF for a resume."""
    from fastapi.responses import Response
    from app.services.intelligence.pdf_generator import build_ats_pdf, verify_ats_pdf

    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    pdf_bytes = build_ats_pdf(resume.content)
    verification = verify_ats_pdf(pdf_bytes)

    filename = f"Resume_{(resume.filename or 'Master').replace(' ', '_').split('.')[0]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-ATS-Verification": verification["ats_compatibility"],
            "X-ATS-Pages": str(verification["page_count"]),
        },
    )


@router.get("/{resume_id}/latex")
async def download_resume_latex(resume_id: UUID, user: CurrentUser, db: DB):
    """Generate and download executive-grade LaTeX source code (.tex) for Overleaf/pdflatex."""
    from fastapi.responses import Response
    from app.services.intelligence.latex_generator import generate_latex_resume

    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    tex_code = generate_latex_resume(resume.content)
    filename = f"Resume_{(resume.filename or 'Master').replace(' ', '_').split('.')[0]}.tex"
    return Response(
        content=tex_code,
        media_type="text/x-tex",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{resume_id}/latex-pdf")
async def download_resume_latex_pdf(resume_id: UUID, user: CurrentUser, db: DB):
    """Compile and download LaTeX PDF if compiler is installed, or fallback to .tex download."""
    from fastapi.responses import Response
    from app.services.intelligence.latex_generator import compile_latex_to_pdf, generate_latex_resume

    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    tex_code = generate_latex_resume(resume.content)
    pdf_bytes, status_msg = compile_latex_to_pdf(tex_code)

    if pdf_bytes:
        filename = f"Resume_LaTeX_{(resume.filename or 'Master').replace(' ', '_').split('.')[0]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Fallback to .tex source code download with header explanation
    filename = f"Resume_{(resume.filename or 'Master').replace(' ', '_').split('.')[0]}.tex"
    return Response(
        content=tex_code,
        media_type="text/x-tex",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-LaTeX-Compiler-Status": status_msg,
        },
    )


