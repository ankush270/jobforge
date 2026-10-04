"""Cover Letter & Recruiter Outreach Generator service.

Adapts logic from:
- 06_cover_letter_generator/cover_letter.py
- 06_cover_letter_generator/generate-cover-letter.mjs
- 06_cover_letter_generator/cover.md
- 06_cover_letter_generator/email.md
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete
from app.services.intelligence.tailor import sanitize_ai_text

logger = logging.getLogger(__name__)


async def generate_cover_letter_content(
    resume_content: dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
    mode: str = "cover_letter",  # "cover_letter" | "email"
) -> str:
    """Generate a highly targeted 3-paragraph cover letter or short recruiter pitch."""
    candidate_name = resume_content.get("contact", {}).get("name", "Candidate")
    skills = resume_content.get("skills", [])
    skills_str = ", ".join(skills[:12]) if skills else "Software Development"

    exps = resume_content.get("workExperience", [])
    recent_exp = ""
    if exps:
        e = exps[0]
        recent_exp = f"{e.get('title', '')} at {e.get('company', '')}: " + "; ".join(e.get("bullets", [])[:2])

    if mode == "email":
        system_prompt = (
            "You are a career strategist drafting a concise, punchy 75-100 word cold outreach email "
            "to a recruiter or hiring manager. Do not sound desperate or generic. Avoid buzzwords like "
            "'spearheaded' or 'synergized'. Do not use em-dashes ('—')."
        )
        prompt = f"""Target Role: {job_title} at {company_name}
Job Context: {job_description[:1000]}
Candidate: {candidate_name}
Core Skills: {skills_str}
Key Highlight: {recent_exp}

Draft a cold outreach email with a catchy Subject Line, 2 short paragraphs, and a call to action.
"""
    else:
        system_prompt = (
            "You are an executive resume and cover letter writer. Draft a 3-paragraph research-backed "
            "cover letter customized for the company and job description.\n"
            "Paragraph 1 (The Hook): Acknowledge the company's specific domain/tech challenge and express enthusiasm for their mission.\n"
            "Paragraph 2 (The Proof): Bridge 1-2 actual achievements from the candidate's experience to the job's core requirements.\n"
            "Paragraph 3 (The Close): Professional availability for an interview discussion, without fawning.\n"
            "Rules:\n"
            "- 150-250 words total.\n"
            "- Never invent metrics or past companies.\n"
            "- Avoid buzzwords ('spearheaded', 'game-changing', 'cutting-edge').\n"
            "- Do NOT use em dashes ('—')."
        )
        prompt = f"""Company: {company_name}
Role: {job_title}
Job Description:
{job_description[:2000]}

Candidate Name: {candidate_name}
Skills: {skills_str}
Recent Experience:
{recent_exp}

Write the full cover letter text with formal greeting (Dear Hiring Team at {company_name},) and sign-off ({candidate_name}).
"""

    try:
        content = await complete(prompt=prompt, system=system_prompt, temperature=0.3)
        return sanitize_ai_text(content)
    except Exception as e:
        logger.warning(f"LLM call failed for cover letter: {e}. Generating structured template.")
        # Fallback template
        if mode == "email":
            return (
                f"Subject: Application: {job_title} - {candidate_name}\n\n"
                f"Hi Hiring Team,\n\n"
                f"I noticed the {job_title} opening at {company_name} and wanted to reach out. "
                f"With a solid background in {skills_str}, I have experience delivering scalable solutions "
                f"and would love to bring this expertise to your team.\n\n"
                f"My resume is attached for your review. I would welcome the opportunity to connect for a brief conversation.\n\n"
                f"Best regards,\n{candidate_name}"
            )
        return (
            f"Dear Hiring Team at {company_name},\n\n"
            f"I am writing to express my strong interest in the {job_title} role at {company_name}. "
            f"Having followed your team's work, I admire your commitment to building reliable, high-impact products.\n\n"
            f"Throughout my career, I have specialized in {skills_str}. In my recent experience as {recent_exp or 'Software Engineer'}, "
            f"I have consistently focused on clean architecture and delivering measurable results that align with the requirements of this role.\n\n"
            f"I would welcome the opportunity to discuss how my technical skills and problem-solving approach can benefit {company_name}.\n\n"
            f"Sincerely,\n{candidate_name}"
        )
