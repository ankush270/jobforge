"""Upskill Gap Analysis & Proof-of-Work Roadmap service.

Adapts logic from:
- 15_upskill_gap_analysis/upskill.mjs (49KB)
- 15_upskill_gap_analysis/upskill.md (13KB)
- 15_upskill_gap_analysis/project.md
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete_json
from app.services.intelligence.ats_scorer import compute_ats_score, extract_keywords_from_jd

logger = logging.getLogger(__name__)


async def generate_upskill_roadmap(
    resume_content: dict[str, Any],
    job_description: str,
    job_keywords: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Analyze skill gap, recommend proof-of-work portfolio projects and learning roadmap."""
    if not job_keywords or not job_keywords.get("required_skills"):
        job_keywords = extract_keywords_from_jd(job_description)

    ats_score = compute_ats_score(resume_content, job_keywords)
    missing = ats_score.get("missing_keywords", [])
    current_score = ats_score["overall_score"]
    candidate_skills = resume_content.get("skills", [])

    system_prompt = (
        "You are a Senior Staff Engineer and Technical Career Mentor.\n"
        "Analyze the candidate's skill gaps against the job requirements. "
        "Recommend 2 concrete, realistic 'Proof-of-Work' portfolio projects that the candidate can "
        "build in 3-7 days to convincingly demonstrate competence in the missing technologies.\n"
        "Return ONLY a valid JSON object."
    )

    prompt = f"""Target Job Description:
{job_description[:1800]}

Candidate's Current Skills:
{", ".join(candidate_skills)}

Critical Missing Skills:
{", ".join(missing[:12]) if missing else "None identified (high alignment)"}

Current ATS Compatibility Score: {current_score}%

Return JSON with:
{{
  "current_fit_score": {current_score},
  "projected_fit_score": {min(100, current_score + 25)},
  "critical_skill_gaps": [
    {{"skill": "Skill Name", "importance": "high" | "medium", "reason": "Why needed for this role"}}
  ],
  "proof_of_work_projects": [
    {{
      "title": "Project Title",
      "time_estimate": "3-5 days",
      "target_skills_bridged": ["Skill A", "Skill B"],
      "description": "What to build and how it demonstrates production-grade capability...",
      "key_architecture_deliverables": ["Deliverable 1", "Deliverable 2"],
      "resume_bullet_preview": "Rewritten bullet point candidate can put on resume upon completion"
    }}
  ],
  "recommended_learning_resources": [
    {{"topic": "Topic", "resource_type": "documentation" | "course" | "book", "recommendation": "Name of resource"}}
  ]
}}
"""

    try:
        roadmap = await complete_json(prompt=prompt, system=system_prompt, temperature=0.2)
        if roadmap and isinstance(roadmap, dict) and "proof_of_work_projects" in roadmap:
            return roadmap
    except Exception as e:
        logger.warning(f"LLM upskill roadmap generation failed: {e}. Returning rule-based roadmap.")

    # Rule-based fallback
    top_missing = missing[:4] if missing else ["Cloud Deployment", "Automated CI/CD"]
    return {
        "current_fit_score": current_score,
        "projected_fit_score": min(100, current_score + 22),
        "critical_skill_gaps": [
            {"skill": s, "importance": "high", "reason": f"Required by job description for core deliverables."}
            for s in top_missing
        ],
        "proof_of_work_projects": [
            {
                "title": f"Production-Grade Service with {top_missing[0]}",
                "time_estimate": "3-5 days",
                "target_skills_bridged": top_missing[:2],
                "description": f"Build and deploy an API service highlighting {top_missing[0]} integration with automated tests and Docker containerization.",
                "key_architecture_deliverables": [
                    "Repository with clean modular structure and automated tests",
                    "Public live demo or Dockerfile deployment instructions",
                ],
                "resume_bullet_preview": f"Architected high-throughput service using {top_missing[0]}, cutting API response time and achieving 99.9% uptime in tests.",
            }
        ],
        "recommended_learning_resources": [
            {"topic": s, "resource_type": "documentation", "recommendation": f"Official {s} Documentation and Quickstarts"}
            for s in top_missing
        ],
    }
