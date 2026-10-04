"""Interview Preparation & STAR Story Bank service.

Adapts logic from:
- 07_interview_prep_and_star_bank/interview_prep.py
- 07_interview_prep_and_star_bank/interview-prep.md (30KB)
- 07_interview_prep_and_star_bank/interview-redflag.md (25KB)
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete_json
from app.services.intelligence.tailor import sanitize_ai_text

logger = logging.getLogger(__name__)


async def generate_interview_prep_pack(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_content: dict[str, Any],
) -> dict[str, Any]:
    """Generate role-specific technical/behavioral questions, STAR stories, and red flags."""
    candidate_name = resume_content.get("contact", {}).get("name", "Candidate")
    skills = resume_content.get("skills", [])
    skills_str = ", ".join(skills[:15]) if skills else "General Software Engineering"

    exps = resume_content.get("workExperience", [])
    recent_roles = []
    for e in exps[:3]:
        recent_roles.append(f"{e.get('title')} at {e.get('company')}: " + " | ".join(e.get("bullets", [])[:2]))
    exp_summary = "\n".join(recent_roles)

    system_prompt = (
        "You are a seasoned Principal Engineer and Technical Hiring Manager.\n"
        "Generate a comprehensive, rigorous interview preparation pack tailored to the job description "
        "and candidate's verified experience. Return ONLY a valid JSON object."
    )

    prompt = f"""Target Company: {company_name}
Target Role: {job_title}
Job Description:
{job_description[:2000]}

Candidate: {candidate_name}
Candidate Skills: {skills_str}
Candidate Experience:
{exp_summary}

Generate JSON with the following structure:
{{
  "predicted_questions": [
    {{
      "category": "technical" | "behavioral" | "architecture",
      "question": "Question text...",
      "why_they_ask": "What the interviewer is evaluating...",
      "key_talking_points": ["Point 1", "Point 2"]
    }}
  ],
  "star_stories": [
    {{
      "theme": "Conflict resolution / Scaling challenge / Leadership",
      "situation": "Context from candidate real experience...",
      "task": "What needed to be achieved...",
      "action": "Specific engineering or leadership action taken...",
      "result": "Outcome achieved..."
    }}
  ],
  "reverse_questions_to_ask": [
    "Sharp question candidate should ask interviewer to evaluate team health...",
    "Question about engineering culture and deployment cycles..."
  ],
  "culture_red_flags_to_watch": [
    "Signal to observe during the interview that indicates burnout or poor management..."
  ],
  "study_plan": [
    {{"day": 1, "focus": "Deep-dive core frameworks and system design principles"}},
    {{"day": 2, "focus": "Rehearse STAR stories and behavioral alignment"}},
    {{"day": 3, "focus": "Company product research and reverse question prep"}}
  ]
}}
"""

    try:
        data = await complete_json(prompt=prompt, system=system_prompt, temperature=0.3)
        if data and isinstance(data, dict) and "predicted_questions" in data:
            return data
    except Exception as e:
        logger.warning(f"LLM interview prep generation failed: {e}. Returning rule-based preparation pack.")

    # Rule-based fallback
    return {
        "predicted_questions": [
            {
                "category": "technical",
                "question": f"How do you design scalable applications using {skills[0] if skills else 'your core tech stack'}?",
                "why_they_ask": f"Tests depth in {skills[0] if skills else 'core competencies'} and production reliability.",
                "key_talking_points": [
                    "Design patterns and trade-offs",
                    "Database optimization and caching strategies",
                    "Monitoring, logging, and error resilience",
                ],
            },
            {
                "category": "behavioral",
                "question": "Tell me about a complex project where technical requirements changed mid-stream.",
                "why_they_ask": "Evaluates adaptability, technical communication, and risk mitigation.",
                "key_talking_points": [
                    "Root cause of requirement change",
                    "Stakeholder communication without blaming",
                    "Phased delivery to maintain team velocity",
                ],
            },
            {
                "category": "architecture",
                "question": f"How would you approach migrating or refactoring a legacy service at {company_name}?",
                "why_they_ask": "Evaluates safety, backwards-compatibility, and observability.",
                "key_talking_points": [
                    "Strangler fig pattern",
                    "Comprehensive regression tests and canary deployments",
                ],
            },
        ],
        "star_stories": [
            {
                "theme": "Engineering Impact & Scalability",
                "situation": f"Working at {exps[0].get('company', 'previous company') if exps else 'prior role'} with growing throughput requirements.",
                "task": "Ensure system performance and uptime under heightened load.",
                "action": "Implemented optimized database indexing, decoupled async background workers, and added APM tracing.",
                "result": "Maintained sub-200ms latency and zero unplanned downtime during traffic peaks.",
            }
        ],
        "reverse_questions_to_ask": [
            "What does the deployment and release lifecycle look like from PR merge to production?",
            "What is the single biggest architectural bottleneck your team is currently solving this quarter?",
            "How does the engineering team balance technical debt remediation with product feature delivery?",
        ],
        "culture_red_flags_to_watch": [
            "Unclear answer when asked about on-call schedules or work-life balance expectations",
            "Lack of written documentation or informal tribal knowledge for core systems",
        ],
        "study_plan": [
            {"day": 1, "focus": "Review core system design patterns and data modeling for target domain"},
            {"day": 2, "focus": "Practice STAR behavioral responses using the 4-part framework"},
            {"day": 3, "focus": "Prepare reverse questions and research recent company releases"},
        ],
    }
