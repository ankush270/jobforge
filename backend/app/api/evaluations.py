"""Evaluations API: ATS scoring, job fit evaluation, tailoring trigger."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.models import Job, JobEvaluation, Resume, TailoredResume
from app.dependencies import DB, CurrentUser
from app.schemas import ATSScoreResponse, TailoredResumeRead, TailorRequest
from app.services.intelligence.ats_scorer import (
    compute_ats_score,
    extract_keywords_from_jd,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/ats-score", response_model=ATSScoreResponse)
async def score_resume_against_job(
    resume_id: UUID,
    job_id: UUID,
    user: CurrentUser,
    db: DB,
):
    """Compute ATS compatibility score between a resume and a job."""
    # Fetch resume
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Fetch job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract keywords from JD if not already cached
    job_keywords = job.keywords
    if not job_keywords or not job_keywords.get("required_skills"):
        job_keywords = extract_keywords_from_jd(job.description)
        job.keywords = job_keywords
        await db.flush()

    # Compute ATS score
    score = compute_ats_score(resume.content, job_keywords)

    return ATSScoreResponse(**score)


@router.post("/tailor", response_model=TailoredResumeRead)
async def tailor_resume(body: TailorRequest, user: CurrentUser, db: DB):
    """Tailor a resume for a specific job.

    Pipeline: keyword extraction → bullet selection → ATS scoring → store.
    Full AI tailoring (STAR rewrite, refinement) will be added in Phase 3.
    """
    # Fetch resume
    result = await db.execute(
        select(Resume).where(Resume.id == body.resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Fetch job
    result = await db.execute(select(Job).where(Job.id == body.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract keywords from JD
    job_keywords = job.keywords
    if not job_keywords or not job_keywords.get("required_skills"):
        job_keywords = extract_keywords_from_jd(job.description)
        job.keywords = job_keywords

    from app.services.intelligence.tailor import tailor_resume_pipeline

    # Execute full AI tailoring pipeline (STAR bullets, keyword injection, anti-hallucination)
    tailor_result = await tailor_resume_pipeline(
        master_resume_content=resume.content,
        job_description=job.description,
        job_keywords=job_keywords,
    )

    tailored = TailoredResume(
        user_id=user.id,
        source_resume_id=resume.id,
        job_id=job.id,
        content=tailor_result["content"],
        content_md=tailor_result["content_md"],
        ats_score=tailor_result["ats_score"],
        ats_breakdown=tailor_result["ats_breakdown"],
        missing_keywords=tailor_result["missing_keywords"],
        injectable_keywords=tailor_result["injectable_keywords"],
        recommendations=tailor_result["recommendations"],
        fact_check_status=tailor_result["fact_check_status"],
    )
    db.add(tailored)
    await db.flush()

    return TailoredResumeRead.model_validate(tailored)


@router.get("/job/{job_id}", response_model=dict)
async def get_job_evaluation(job_id: UUID, user: CurrentUser, db: DB):
    """Get the full evaluation for a job (or compute a quick one)."""
    result = await db.execute(
        select(JobEvaluation).where(
            JobEvaluation.user_id == user.id,
            JobEvaluation.job_id == job_id,
        )
    )
    evaluation = result.scalar_one_or_none()

    if evaluation:
        rec = "APPLY_IMMEDIATELY"
        if evaluation.overall_score:
            score_val = float(evaluation.overall_score)
            rec = "APPLY_IMMEDIATELY" if score_val >= 75 else ("TAILOR_AND_APPLY" if score_val >= 50 else "LOW_PRIORITY")
        if evaluation.role_match and isinstance(evaluation.role_match, dict) and evaluation.role_match.get("recommendation"):
            rec = evaluation.role_match["recommendation"]

        return {
            "id": str(evaluation.id),
            "overall_score": float(evaluation.overall_score) if evaluation.overall_score else None,
            "recommendation": rec,
            "tier": evaluation.tier,
            "block_a_role_match": evaluation.role_match,
            "block_b_cv_fit": evaluation.cv_fit,
            "block_c_level_strategy": evaluation.level_strategy,
            "block_d_compensation": evaluation.comp_research,
            "block_e_personalization_angle": evaluation.personalization,
            "block_f_interview_prep": evaluation.interview_prep_data,
            "block_g_legitimacy_check": evaluation.legitimacy,
            "block_h_location_auth": evaluation.work_auth,
            "created_at": evaluation.created_at.isoformat(),
        }

    from sqlalchemy.orm import joinedload
    from app.services.intelligence.evaluator import run_full_ah_evaluation

    # Fetch job with company
    result = await db.execute(
        select(Job).options(joinedload(Job.company)).where(Job.id == job_id)
    )
    job = result.unique().scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch user master resume
    resume = (
        await db.execute(
            select(Resume).where(Resume.user_id == user.id).order_by(Resume.is_master.desc())
        )
    ).scalars().first()

    resume_content = resume.content if resume else {"skills": [], "workExperience": []}
    company_name = job.company.name if job.company else "Target Company"

    ah_result = await run_full_ah_evaluation(
        job_title=job.title,
        company_name=company_name,
        job_description=job.description,
        location=job.location,
        resume_content=resume_content,
        is_ghost=job.is_ghost,
        ghost_signals=job.ghost_signals,
    )

    evaluation = JobEvaluation(
        user_id=user.id,
        job_id=job.id,
        overall_score=ah_result.get("overall_fit_score"),
        tier=job.company.tier if job.company else None,
        role_match=ah_result.get("block_a_role_match"),
        cv_fit=ah_result.get("block_b_cv_fit"),
        level_strategy=ah_result.get("block_c_level_strategy"),
        comp_research=ah_result.get("block_d_compensation"),
        personalization=ah_result.get("block_e_personalization_angle"),
        interview_prep_data=ah_result.get("block_f_interview_prep"),
        legitimacy=ah_result.get("block_g_legitimacy_check"),
        work_auth=ah_result.get("block_h_location_auth"),
    )
    db.add(evaluation)
    await db.flush()

    return {
        "id": str(evaluation.id),
        "overall_score": float(evaluation.overall_score) if evaluation.overall_score else None,
        "recommendation": ah_result.get("recommendation"),
        "tier": evaluation.tier,
        "block_a_role_match": evaluation.role_match,
        "block_b_cv_fit": evaluation.cv_fit,
        "block_c_level_strategy": evaluation.level_strategy,
        "block_d_compensation": evaluation.comp_research,
        "block_e_personalization_angle": evaluation.personalization,
        "block_f_interview_prep": evaluation.interview_prep_data,
        "block_g_legitimacy_check": evaluation.legitimacy,
        "block_h_location_auth": evaluation.work_auth,
        "created_at": evaluation.created_at.isoformat(),
    }



@router.post("/upskill-gap")
async def get_upskill_gap_analysis(
    resume_id: UUID,
    job_id: UUID,
    user: CurrentUser,
    db: DB,
):
    """Analyze missing skills, portfolio project recommendations, and learning roadmap."""
    from app.services.intelligence.upskill import generate_upskill_roadmap

    resume = (
        await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    ).scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return await generate_upskill_roadmap(
        resume_content=resume.content,
        job_description=job.description,
        job_keywords=job.keywords,
    )


@router.get("/tailored/{tailored_id}/pdf")
async def download_tailored_pdf(tailored_id: UUID, user: CurrentUser, db: DB):
    """Generate and download ATS-compliant PDF for a tailored resume."""
    from fastapi.responses import Response
    from app.services.intelligence.pdf_generator import build_ats_pdf, verify_ats_pdf

    result = await db.execute(
        select(TailoredResume).where(TailoredResume.id == tailored_id, TailoredResume.user_id == user.id)
    )
    tailored = result.scalar_one_or_none()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    pdf_bytes = build_ats_pdf(tailored.content)
    verification = verify_ats_pdf(pdf_bytes)

    filename = f"Tailored_Resume_{str(tailored.id)[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-ATS-Verification": verification["ats_compatibility"],
            "X-ATS-Score": str(tailored.ats_score or 0),
        },
    )


@router.get("/tailored/{tailored_id}/latex")
async def download_tailored_latex(tailored_id: UUID, user: CurrentUser, db: DB):
    """Generate and download LaTeX source code (.tex) for a tailored resume."""
    from fastapi.responses import Response
    from app.services.intelligence.latex_generator import generate_latex_resume

    result = await db.execute(
        select(TailoredResume).where(TailoredResume.id == tailored_id, TailoredResume.user_id == user.id)
    )
    tailored = result.scalar_one_or_none()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    tex_code = generate_latex_resume(tailored.content)
    filename = f"Tailored_Resume_{str(tailored.id)[:8]}.tex"
    return Response(
        content=tex_code,
        media_type="text/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tailored/{tailored_id}/latex-pdf")
async def download_tailored_latex_pdf(tailored_id: UUID, user: CurrentUser, db: DB):
    """Compile tailored LaTeX source to PDF, or fallback to .tex download."""
    from fastapi.responses import Response
    from app.services.intelligence.latex_generator import compile_latex_to_pdf, generate_latex_resume

    result = await db.execute(
        select(TailoredResume).where(TailoredResume.id == tailored_id, TailoredResume.user_id == user.id)
    )
    tailored = result.scalar_one_or_none()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    tex_code = generate_latex_resume(tailored.content)
    pdf_bytes, status_msg = compile_latex_to_pdf(tex_code)

    if pdf_bytes:
        filename = f"Tailored_Resume_LaTeX_{str(tailored.id)[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"Tailored_Resume_{str(tailored.id)[:8]}.tex"
    return Response(
        content=tex_code,
        media_type="text/x-tex",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-LaTeX-Compiler-Status": status_msg,
        },
    )



