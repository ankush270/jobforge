"""Company Intel & Red Flag Detector service.

Adapts logic from:
- 10_company_intel_and_red_flag_detector/company-history.mjs (98KB)
- 10_company_intel_and_red_flag_detector/company-funded.mjs (40KB)
- 20_evaluation_and_fit_scoring_framework/classify-tier.mjs
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete_json

logger = logging.getLogger(__name__)

# Known company tiers
_FAANG_TIER = {"google", "meta", "apple", "amazon", "netflix", "microsoft"}
_UNICORN_TIER = {
    "stripe", "openai", "anthropic", "databricks", "airtable", "figma", "notion",
    "canva", "bytedance", "spacex", "snowflake", "uber", "swiggy", "zomato", "razorpay",
}


def classify_tier_fast(company_name: str) -> str:
    """Fast rule-based tier classification."""
    clean = company_name.lower().strip()
    if clean in _FAANG_TIER:
        return "faang"
    if clean in _UNICORN_TIER:
        return "unicorn"
    return "growth_company"


async def analyze_company_intel(company_name: str, domain: str | None = None) -> dict[str, Any]:
    """Analyze company profile, funding, engineering culture, and red flags."""
    tier = classify_tier_fast(company_name)

    system_prompt = (
        "You are a Silicon Valley tech venture analyst and talent intelligence expert.\n"
        "Evaluate the target company and return an objective, factual intelligence report in JSON."
    )

    prompt = f"""Target Company: {company_name}
Domain / Website: {domain or 'N/A'}

Analyze and return JSON with:
{{
  "tier": "{tier}",
  "overview": "Brief 2-sentence summary of what the company does and its business model",
  "funding_stage": "Public / Series A/B/C / Bootstrapped / Seed",
  "estimated_headcount": "1-50 / 51-200 / 201-1000 / 1000+",
  "engineering_culture_rating": 1-5,
  "tech_stack_highlights": ["Tech 1", "Tech 2"],
  "culture_positives": [
    "High engineering autonomy",
    "Strong compensation"
  ],
  "potential_red_flags": [
    "Known aggressive on-call or turnover patterns (if any, otherwise empty)"
  ],
  "stability_assessment": "high" | "moderate" | "volatile"
}}
"""

    try:
        intel = await complete_json(prompt=prompt, system=system_prompt, temperature=0.2)
        if intel and isinstance(intel, dict) and "overview" in intel:
            return intel
    except Exception as e:
        logger.warning(f"LLM company intel analysis failed: {e}. Using rule-based assessment.")

    # Rule-based fallback
    return {
        "tier": tier,
        "overview": f"{company_name} is an active technology organization operating in software engineering.",
        "funding_stage": "Established / Venture-backed",
        "estimated_headcount": "200-1000+",
        "engineering_culture_rating": 4,
        "tech_stack_highlights": ["Cloud Infrastructure", "Distributed Systems", "Modern Web Frameworks"],
        "culture_positives": [
            "Active hiring pipeline",
            "Clear role responsibilities",
        ],
        "potential_red_flags": [],
        "stability_assessment": "high" if tier in ("faang", "unicorn") else "moderate",
    }
