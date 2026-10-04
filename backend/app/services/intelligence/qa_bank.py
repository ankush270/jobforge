"""Master QA Bank & Recruiter Email Reply Generator service.

Adapts logic from:
- 16_email_drafts_and_qa_bank/application-answers.mjs (24KB)
- 16_email_drafts_and_qa_bank/reply-matcher.mjs (30KB)
- 16_email_drafts_and_qa_bank/paste-reply.mjs
- 16_email_drafts_and_qa_bank/apply.md (42KB)
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete
from app.services.intelligence.tailor import sanitize_ai_text

logger = logging.getLogger(__name__)


async def generate_form_answer(
    question: str,
    resume_content: dict[str, Any],
    job_description: str | None = None,
    word_limit: int = 150,
) -> str:
    """Generate a high-converting answer to tricky job portal application questions."""
    candidate_name = resume_content.get("contact", {}).get("name", "Candidate")
    skills = ", ".join(resume_content.get("skills", [])[:10])

    system_prompt = (
        "You are an executive career advisor helping a candidate fill out an online job application form.\n"
        f"Draft a direct, confident answer within approximately {word_limit} words.\n"
        "Never invent fake employers or metrics. Avoid hollow buzzwords."
    )

    prompt = f"""Application Form Question: "{question}"

Candidate: {candidate_name}
Verified Skills: {skills}
Target Job Context: {job_description[:1000] if job_description else 'N/A'}

Write an articulate, authentic answer ready to paste into the application form.
"""

    try:
        ans = await complete(prompt=prompt, system=system_prompt, temperature=0.3)
        return sanitize_ai_text(ans)
    except Exception as e:
        logger.warning(f"LLM answer generation failed: {e}. Returning template.")
        return (
            f"With strong experience in {skills}, I have focused my career on building robust, scalable solutions. "
            "I enjoy solving complex architectural challenges in collaborative team environments and look forward "
            "to bringing this energy and technical discipline to your organization."
        )


async def generate_recruiter_email_reply(
    incoming_email: str,
    intent: str,  # "schedule_interview" | "negotiate" | "decline" | "follow_up"
    candidate_name: str,
) -> str:
    """Generate a clean, context-aware reply to a recruiter or hiring manager."""
    system_prompt = (
        "You are a professional software engineer replying to a recruiter email. "
        "Draft a crisp, polite, and responsive email reply. Avoid fluff."
    )

    prompt = f"""Incoming Email:
\"\"\"{incoming_email[:1200]}\"\"\"

My Goal / Intent: {intent}
Candidate Name: {candidate_name}

Draft the reply email with subject line and body.
"""

    try:
        reply = await complete(prompt=prompt, system=system_prompt, temperature=0.3)
        return sanitize_ai_text(reply)
    except Exception as e:
        logger.warning(f"LLM email reply draft failed: {e}. Returning template.")
        if intent == "schedule_interview":
            return (
                f"Subject: Re: Interview Availability - {candidate_name}\n\n"
                f"Hi,\n\n"
                "Thank you for reaching out! I would be delighted to speak with the team. "
                "I am generally available over the next few days between 10:00 AM - 5:00 PM. "
                "Please let me know what time slot works best on your calendar.\n\n"
                f"Best regards,\n{candidate_name}"
            )
        return (
            f"Subject: Re: Next Steps - {candidate_name}\n\n"
            f"Hi,\n\n"
            "Thank you for your message and for keeping me updated. "
            "Looking forward to our continued conversation.\n\n"
            f"Best regards,\n{candidate_name}"
        )
