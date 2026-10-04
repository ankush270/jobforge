"""AI Resume Tailoring Service — STAR bullet rewriting and multi-pass refinement.

Adapts logic from:
- 05_ai_tailoring_star_bullets_and_prompts/improver.py (57KB)
- 05_ai_tailoring_star_bullets_and_prompts/refiner.py (30KB)
- 05_ai_tailoring_star_bullets_and_prompts/prompts/templates.py
- 04_ats_scoring_and_keyword_matching/resume_preservation.py
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

from app.ai.llm_router import complete_json
from app.services.intelligence.ats_scorer import compute_ats_score, extract_keywords_from_jd
from app.services.intelligence.preservation import verify_preservation

logger = logging.getLogger(__name__)

# AI Phrase Blacklist and Replacements from refinement.py
AI_PHRASE_REPLACEMENTS: dict[str, str] = {
    "spearheaded": "led",
    "orchestrated": "coordinated",
    "championed": "advocated for",
    "synergized": "collaborated",
    "leveraged": "used",
    "revolutionized": "transformed",
    "pioneered": "introduced",
    "catalyzed": "initiated",
    "operationalized": "implemented",
    "architected": "designed",
    "envisioned": "planned",
    "effectuated": "completed",
    "endeavored": "worked",
    "facilitated": "helped",
    "utilized": "used",
    "synergy": "collaboration",
    "synergies": "collaborations",
    "paradigm": "approach",
    "paradigm shift": "change",
    "best-in-class": "top-performing",
    "world-class": "high-quality",
    "cutting-edge": "modern",
    "bleeding-edge": "modern",
    "game-changer": "innovation",
    "game-changing": "innovative",
    "disruptive": "innovative",
    "holistic": "comprehensive",
    "robust": "reliable",
    "actionable": "practical",
    "impactful": "effective",
    "proactively": "actively",
    "in order to": "to",
    "moving forward": "",
    "at this point in time": "currently",
    "on a daily basis": "daily",
}


def sanitize_ai_text(text: str) -> str:
    """Clean out AI buzzwords, double hyphens, and em-dashes."""
    if not text:
        return text

    # Remove em-dashes and substitute with standard hyphen or comma
    cleaned = text.replace("—", " - ").replace("–", " - ").replace("---", " - ")

    # Case-insensitive replacement for AI phrases
    for phrase, replacement in AI_PHRASE_REPLACEMENTS.items():
        pattern = rf"\b{re.escape(phrase)}\b"
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Clean double spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def build_markdown_resume(content: dict[str, Any]) -> str:
    """Convert structured resume JSON into clean ATS-friendly markdown."""
    lines: list[str] = []

    # Personal info
    contact = content.get("contact", {})
    name = contact.get("name", "Candidate")
    lines.append(f"# {name}")

    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin"):
        contact_parts.append(f"[LinkedIn]({contact['linkedin']})")
    if contact.get("github"):
        contact_parts.append(f"[GitHub]({contact['github']})")
    if contact_parts:
        lines.append(" | ".join(contact_parts))
    lines.append("")

    # Summary
    summary = content.get("summary")
    if summary:
        lines.append("## Professional Summary")
        lines.append(summary)
        lines.append("")

    # Work Experience
    experience = content.get("workExperience", [])
    if experience:
        lines.append("## Work Experience")
        for exp in experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            years = exp.get("years", "")
            loc = exp.get("location", "")
            header = f"### {title} — {company}"
            sub = " | ".join(filter(None, [loc, years]))
            lines.append(header)
            if sub:
                lines.append(f"*{sub}*")
            lines.append("")
            for bullet in exp.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

    # Skills
    skills = content.get("skills", [])
    if skills:
        lines.append("## Technical Skills")
        lines.append(", ".join(skills))
        lines.append("")

    # Education
    education = content.get("education", [])
    if education:
        lines.append("## Education")
        for edu in education:
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            yr = edu.get("years", "")
            lines.append(f"- **{deg}**, {inst} ({yr})")
        lines.append("")

    # Projects
    projects = content.get("projects", [])
    if projects:
        lines.append("## Projects")
        for proj in projects:
            pname = proj.get("name", "")
            prole = proj.get("role", "")
            header = f"### {pname}" + (f" ({prole})" if prole else "")
            lines.append(header)
            for bullet in proj.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

    # Certifications
    certs = content.get("certifications", [])
    if certs:
        lines.append("## Certifications")
        for cert in certs:
            lines.append(f"- {cert}")
        lines.append("")

    return "\n".join(lines)


async def tailor_resume_pipeline(
    master_resume_content: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any] | None = None,
    tailor_mode: str = "keywords",  # "nudge" | "keywords" | "full"
) -> dict[str, Any]:
    """Execute full AI tailoring pipeline:
    1. Extract keywords & gaps from JD
    2. Rewrite work experience bullets into STAR format with relevant keyword injection
    3. Sanitize AI phrases
    4. Anti-hallucination verification against master resume
    5. ATS score calculation
    """
    if not job_keywords or not job_keywords.get("required_skills"):
        job_keywords = extract_keywords_from_jd(job_description)

    # Initial baseline ATS score
    initial_score = compute_ats_score(master_resume_content, job_keywords)
    missing_keywords = initial_score.get("missing_keywords", [])
    injectable_keywords = initial_score.get("injectable_keywords", [])

    # Deep copy to prevent modifying master
    tailored = copy.deepcopy(master_resume_content)

    # Prepare prompt for LLM
    system_prompt = (
        "You are an expert ATS Resume Optimization Specialist adhering to the STAR method.\n"
        "Rewrite only the 'summary' and the 'bullets' in 'workExperience' and 'projects' to better "
        "align with the target job requirements.\n\n"
        "STRICT TRUTHFULNESS & ANTI-HALLUCINATION RULES:\n"
        "1. NEVER invent any companies, job titles, university names, degrees, or dates.\n"
        "2. NEVER invent metrics, dollar amounts, or numbers not present in the original resume.\n"
        "3. Incorporate relevant keywords ONLY when the candidate's existing experience supports it.\n"
        "4. Bullet format: Strong action verb + task/context + tools/skills + outcome.\n"
        "5. Avoid buzzwords like 'spearheaded', 'synergized', 'cutting-edge', 'leveraged'. Use natural verbs.\n"
        "6. Do NOT use em dashes ('—'). Return strictly valid JSON."
    )

    user_prompt = f"""Target Job Description:
{job_description[:2500]}

Keywords to Emphasize (Missing in Resume):
{", ".join(missing_keywords[:15])}

Candidate's Current Resume Content:
{master_resume_content}

Return a JSON object with:
{{
  "summary": "Tailored professional summary aligned with the target role...",
  "workExperience": [
    {{
      "id": 1,
      "company": "Exact original company name",
      "title": "Exact original title",
      "years": "Exact original years",
      "location": "Exact original location",
      "bullets": [
        "Rewritten bullet using STAR framework..."
      ]
    }}
  ],
  "projects": [
    {{
      "id": 1,
      "name": "Exact original project name",
      "bullets": [
        "Rewritten project bullet..."
      ]
    }}
  ],
  "skills": ["Original skills re-ordered with job-relevant skills first"],
  "changes_made": [
    "Brief explanation of what was aligned in work experience 1",
    "Brief explanation of keywords incorporated"
  ]
}}
"""

    llm_error = None
    changes_made: list[str] = []

    try:
        response = await complete_json(prompt=user_prompt, system=system_prompt, temperature=0.2)
        if response and isinstance(response, dict):
            # Update summary if present
            if response.get("summary"):
                tailored["summary"] = sanitize_ai_text(response["summary"])

            # Update workExperience bullets while protecting company/title/years
            if isinstance(response.get("workExperience"), list):
                orig_exps = {e.get("company", "").lower(): e for e in tailored.get("workExperience", [])}
                for exp in response["workExperience"]:
                    comp_name = exp.get("company", "").lower()
                    if comp_name in orig_exps:
                        # Only update bullets, sanitize each
                        orig_entry = orig_exps[comp_name]
                        new_bullets = [sanitize_ai_text(b) for b in exp.get("bullets", []) if isinstance(b, str) and b.strip()]
                        if new_bullets:
                            orig_entry["bullets"] = new_bullets

            # Update projects bullets while protecting names
            if isinstance(response.get("projects"), list):
                orig_projs = {p.get("name", "").lower(): p for p in tailored.get("projects", [])}
                for proj in response["projects"]:
                    p_name = proj.get("name", "").lower()
                    if p_name in orig_projs:
                        new_bullets = [sanitize_ai_text(b) for b in proj.get("bullets", []) if isinstance(b, str) and b.strip()]
                        if new_bullets:
                            orig_projs[p_name]["bullets"] = new_bullets

            # Update skills ordering (never drop original skills)
            if isinstance(response.get("skills"), list):
                orig_skills = set(tailored.get("skills", []))
                suggested_skills = [s for s in response["skills"] if isinstance(s, str) and s in orig_skills]
                remaining_skills = [s for s in tailored.get("skills", []) if s not in suggested_skills]
                tailored["skills"] = suggested_skills + remaining_skills

            changes_made = response.get("changes_made", [
                "Rephrased bullet points to STAR format",
                "Reordered skills to emphasize job-relevant competencies",
            ])
    except Exception as e:
        logger.warning(f"AI tailoring call failed or timed out: {e}. Falling back to rule-based keyword alignment.")
        llm_error = str(e)
        # Fallback: reorder skills and sanitize existing bullets
        for exp in tailored.get("workExperience", []):
            exp["bullets"] = [sanitize_ai_text(b) for b in exp.get("bullets", [])]
        changes_made = ["Sanitized AI buzzwords and aligned structure (rule-based fallback)"]

    # 4. Anti-Hallucination Guard Verification
    verification = verify_preservation(
        master_profile=master_resume_content,
        tailored_content=tailored,
    )

    # If verification failed due to hallucination, revert protected sections
    if verification["status"] == "failed":
        logger.warning(f"Preservation check failed: {verification['violations']}. Reverting protected sections.")
        # Ensure company names, dates, and protected fields are strictly restored
        tailored["workExperience"] = master_resume_content.get("workExperience", [])
        tailored["education"] = master_resume_content.get("education", [])
        tailored["contact"] = master_resume_content.get("contact", {})
        # Re-run verification
        verification = verify_preservation(master_resume_content, tailored)

    # 5. Compute new ATS score after tailoring
    final_score = compute_ats_score(tailored, job_keywords)

    # 6. Generate formatted Markdown version
    content_md = build_markdown_resume(tailored)

    return {
        "content": tailored,
        "content_md": content_md,
        "ats_score": final_score["overall_score"],
        "ats_breakdown": final_score["sub_scores"],
        "missing_keywords": final_score["missing_keywords"],
        "injectable_keywords": final_score["injectable_keywords"],
        "recommendations": final_score["recommendations"],
        "fact_check_status": verification["status"],
        "verification_details": verification,
        "changes_made": changes_made,
        "llm_error": llm_error,
    }
