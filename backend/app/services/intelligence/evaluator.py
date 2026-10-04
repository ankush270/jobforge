"""Full 8-Block A-H Evaluation Engine.

Adapts logic from:
- 20_evaluation_and_fit_scoring_framework/oferta.md (90KB)
- 20_evaluation_and_fit_scoring_framework/rank-pipeline.mjs
- 20_evaluation_and_fit_scoring_framework/role-matcher.mjs
- 20_evaluation_and_fit_scoring_framework/classify-tier.mjs

Computes an in-depth 8-dimension evaluation matrix for any job opening:
  A: Role Match (Title & Seniority alignment)
  B: CV Fit (Candidate verified accomplishments vs JD requirements)
  C: Level Strategy (Down-level vs Stretch vs Lateral move analysis)
  D: Compensation Benchmark (Calibrated market percentiles)
  E: Personalization Angle (Hook & strategic value proposition)
  F: Interview Readiness (Likely technical hurdles & prep difficulty)
  G: Legitimacy & Ghost Signal (Credibility score & ghost flags)
  H: Work-Auth / Location Feasibility (Remote/Hybrid practical match)
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete_json
from app.services.intelligence.ats_scorer import compute_ats_score, extract_keywords_from_jd
from app.services.intelligence.company_intel import classify_tier_fast
from app.services.intelligence.salary_intel import lookup_market_benchmark

logger = logging.getLogger(__name__)


async def run_full_ah_evaluation(
    job_title: str,
    company_name: str,
    job_description: str,
    location: str | None,
    resume_content: dict[str, Any],
    is_ghost: bool = False,
    ghost_signals: list[str] | None = None,
) -> dict[str, Any]:
    """Execute full 8-block A-H evaluation matrix."""
    company_tier = classify_tier_fast(company_name)
    keywords = extract_keywords_from_jd(job_description)
    ats = compute_ats_score(resume_content, keywords)

    candidate_skills = resume_content.get("skills", [])
    skills_text = ", ".join(candidate_skills[:12]) if candidate_skills else "Software Engineering"
    exps = resume_content.get("workExperience", [])
    recent_title = exps[0].get("title", "Software Engineer") if exps else "Engineer"

    comp_benchmark = lookup_market_benchmark(
        role=job_title,
        experience_yrs=len(exps) * 2 or 3,
        location=location,
        currency="INR",
    )

    system_prompt = (
        "You are an Elite Career Strategist and Executive Headhunter.\n"
        "Perform a thorough 8-block (A through H) job evaluation matrix adapted from the 'Oferta' framework. "
        "Be objective, highly critical, and realistic. Return ONLY a valid JSON object."
    )

    prompt = f"""Target Role: {job_title} at {company_name} (Tier: {company_tier})
Location: {location or 'Not specified'}
Job Description Summary:
{job_description[:1800]}

Candidate Profile:
- Recent Title: {recent_title}
- Core Skills: {skills_text}
- ATS Baseline Score: {ats['overall_score']}%
- Missing Keywords: {", ".join(ats['missing_keywords'][:8])}
- Known Ghost Signals: {", ".join(ghost_signals or []) if is_ghost else 'None'}

Return a JSON object with:
{{
  "overall_fit_score": 0-100,
  "recommendation": "APPLY_IMMEDIATELY" | "TAILOR_AND_APPLY" | "LOW_PRIORITY" | "SKIP",
  "block_a_role_match": {{
    "seniority_alignment": "junior" | "mid" | "senior" | "staff",
    "score": 0-100,
    "summary": "Title and core deliverables match analysis..."
  }},
  "block_b_cv_fit": {{
    "skills_overlap_pct": {ats['sub_scores']['skills_coverage']},
    "strengths": ["Key strength 1", "Key strength 2"],
    "critical_gaps": ["Critical gap 1", "Critical gap 2"]
  }},
  "block_c_level_strategy": {{
    "move_type": "lateral" | "stretch_promotion" | "down_level",
    "risk_level": "low" | "medium" | "high",
    "strategy_notes": "How to position candidate experience for this level..."
  }},
  "block_d_compensation": {{
    "estimated_median": {comp_benchmark['p50_median']},
    "estimated_top": {comp_benchmark['p75']},
    "currency": "{comp_benchmark['currency']}"
  }},
  "block_e_personalization_angle": {{
    "hook": "1-sentence hook to mention in outreach",
    "unique_value_proposition": "Why candidate specifically solves their problem"
  }},
  "block_f_interview_prep": {{
    "expected_difficulty": "medium" | "high" | "intense",
    "primary_focus_areas": ["System Design", "Domain Depth"]
  }},
  "block_g_legitimacy_check": {{
    "ghost_risk": "low" | "moderate" | "high",
    "credibility_score": 0-100,
    "notes": "Employer legitimacy assessment"
  }},
  "block_h_location_auth": {{
    "fit": "perfect" | "acceptable" | "relocation_required",
    "notes": "Remote/onsite evaluation"
  }}
}}
"""

    try:
        evaluation = await complete_json(prompt=prompt, system=system_prompt, temperature=0.2)
        if evaluation and isinstance(evaluation, dict) and "overall_fit_score" in evaluation:
            evaluation["keywords"] = keywords
            evaluation["ats_score"] = ats["overall_score"]
            return evaluation
    except Exception as e:
        logger.warning(f"LLM A-H evaluation failed: {e}. Returning rule-based evaluation.")

    # Rule-based fallback
    fit_score = int(ats["overall_score"] * 0.8 + (10 if not is_ghost else -20))
    fit_score = max(20, min(95, fit_score))

    rec = "APPLY_IMMEDIATELY" if fit_score >= 75 else ("TAILOR_AND_APPLY" if fit_score >= 50 else "LOW_PRIORITY")

    return {
        "overall_fit_score": fit_score,
        "recommendation": rec,
        "ats_score": ats["overall_score"],
        "keywords": keywords,
        "block_a_role_match": {
            "seniority_alignment": "mid",
            "score": min(90, ats["overall_score"] + 10),
            "summary": f"Role requirements align with {recent_title} trajectory.",
        },
        "block_b_cv_fit": {
            "skills_overlap_pct": ats["sub_scores"]["skills_coverage"],
            "strengths": [candidate_skills[0] if candidate_skills else "Engineering fundamentals"],
            "critical_gaps": ats["missing_keywords"][:3],
        },
        "block_c_level_strategy": {
            "move_type": "lateral",
            "risk_level": "low",
            "strategy_notes": "Position past deliverables with quantitative metrics to anchor seniority.",
        },
        "block_d_compensation": {
            "estimated_median": comp_benchmark["p50_median"],
            "estimated_top": comp_benchmark["p75"],
            "currency": comp_benchmark["currency"],
        },
        "block_e_personalization_angle": {
            "hook": f"Specialized in scalable architecture with verified experience in {skills_text}.",
            "unique_value_proposition": "Bridges core requirements with reliable production track record.",
        },
        "block_f_interview_prep": {
            "expected_difficulty": "medium",
            "primary_focus_areas": ["Data Structures", "System Architecture"],
        },
        "block_g_legitimacy_check": {
            "ghost_risk": "high" if is_ghost else "low",
            "credibility_score": 35 if is_ghost else 85,
            "notes": "Ghost posting signals identified" if is_ghost else "Verified active company posting",
        },
        "block_h_location_auth": {
            "fit": "perfect" if "remote" in (location or "").lower() else "acceptable",
            "notes": f"Location: {location or 'Remote'}",
        },
    }
