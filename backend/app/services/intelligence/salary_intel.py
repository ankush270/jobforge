"""Salary Benchmarking & Negotiation Intelligence service.

Adapts logic from:
- 09_salary_benchmarks_and_negotiation/salary-gap.mjs (65KB)
- 09_salary_benchmarks_and_negotiation/negotiation-roi.mjs (33KB)
- 09_salary_benchmarks_and_negotiation/offer-prep.md (27KB)
- 09_salary_benchmarks_and_negotiation/salary_lookup.py
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.llm_router import complete
from app.services.intelligence.tailor import sanitize_ai_text

logger = logging.getLogger(__name__)

# Calibrated baseline tech compensation benchmarks (in INR & USD)
_BENCHMARK_RATES = {
    "software engineer": {"inr": (800000, 1400000, 2200000, 3200000), "usd": (90000, 125000, 160000, 210000)},
    "senior software engineer": {"inr": (1800000, 2800000, 4200000, 5800000), "usd": (140000, 175000, 220000, 280000)},
    "frontend developer": {"inr": (700000, 1200000, 1900000, 2800000), "usd": (85000, 115000, 150000, 190000)},
    "backend developer": {"inr": (800000, 1400000, 2300000, 3400000), "usd": (95000, 130000, 170000, 220000)},
    "full stack developer": {"inr": (850000, 1500000, 2400000, 3500000), "usd": (95000, 135000, 175000, 230000)},
    "data scientist": {"inr": (900000, 1600000, 2600000, 3800000), "usd": (105000, 145000, 185000, 240000)},
    "devops engineer": {"inr": (900000, 1600000, 2500000, 3600000), "usd": (105000, 140000, 180000, 230000)},
    "engineering manager": {"inr": (2800000, 4200000, 6000000, 8500000), "usd": (180000, 225000, 280000, 360000)},
}


def lookup_market_benchmark(
    role: str,
    experience_yrs: int | None = None,
    location: str | None = None,
    currency: str = "INR",
) -> dict[str, Any]:
    """Look up calibrated market percentiles (P25, P50, P75, P90)."""
    curr = currency.lower() if currency else "inr"
    if curr not in ("inr", "usd"):
        curr = "inr"

    matched_key = "software engineer"
    role_lower = role.lower()
    for k in _BENCHMARK_RATES:
        if k in role_lower:
            matched_key = k
            break

    p25, p50, p75, p90 = _BENCHMARK_RATES[matched_key][curr]

    # Adjust for experience years
    multiplier = 1.0
    if experience_yrs:
        if experience_yrs > 8:
            multiplier = 1.35
        elif experience_yrs > 5:
            multiplier = 1.15
        elif experience_yrs < 2:
            multiplier = 0.85

    return {
        "role": role,
        "matched_standard_role": matched_key.title(),
        "currency": curr.upper(),
        "p25": int(p25 * multiplier),
        "p50_median": int(p50 * multiplier),
        "p75": int(p75 * multiplier),
        "p90": int(p90 * multiplier),
        "experience_adjustment": f"{experience_yrs} years" if experience_yrs else "Standard",
        "location": location or "India",
    }


def analyze_salary_gap(
    offered_salary: int,
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    """Calculate gap between current offer and market percentiles (salary-gap.mjs logic)."""
    p50 = benchmark["p50_median"]
    p75 = benchmark["p75"]

    diff_p50 = offered_salary - p50
    pct_p50 = round((diff_p50 / p50) * 100, 1)

    diff_p75 = offered_salary - p75
    pct_p75 = round((diff_p75 / p75) * 100, 1)

    # 3-year cumulative impact
    three_year_gain_at_p75 = (p75 - offered_salary) * 3 if offered_salary < p75 else 0

    if offered_salary < benchmark["p25"]:
        leverage_status = "severely_underpaid"
        advice = "The offer is below the 25th percentile. Strong grounds to negotiate a 20-30% adjustment."
    elif offered_salary < p50:
        leverage_status = "below_median"
        advice = "Offer is below the market median. Negotiate towards the P50-P75 range citing your specific skills."
    elif offered_salary < p75:
        leverage_status = "competitive"
        advice = "Solid competitive offer. You have leverage to ask for a 5-10% bump or performance signing bonus."
    else:
        leverage_status = "top_of_market"
        advice = "Offer is in the top quartile of the market. Consider negotiating equity, signing bonus, or remote flexibility."

    return {
        "offered_salary": offered_salary,
        "market_median": p50,
        "target_p75": p75,
        "gap_from_median": diff_p50,
        "gap_percentage": pct_p50,
        "three_year_difference_at_p75": three_year_gain_at_p75,
        "leverage_status": leverage_status,
        "strategic_advice": advice,
    }


async def generate_counter_negotiation_script(
    company_name: str,
    role: str,
    current_offer: int,
    target_salary: int,
    currency: str,
    key_strengths: list[str] | None = None,
) -> dict[str, Any]:
    """Generate persuasive, professional counter-offer email and verbal talking points."""
    strengths_str = ", ".join(key_strengths) if key_strengths else "relevant domain expertise and strong technical delivery"

    system_prompt = (
        "You are an executive compensation negotiator. Draft an elegant, respectful, and highly persuasive "
        "counter-offer response for a job offer. Maintain gratitude for the offer while firmly stating the "
        "counter-proposal based on market benchmarks and demonstrated value. Avoid aggressive posturing."
    )

    prompt = f"""Company: {company_name}
Role: {role}
Current Offer: {currency} {current_offer:,}
Target Counter-Proposal: {currency} {target_salary:,}
Key Strengths / Value Props: {strengths_str}

Generate:
1. Written Email Counter-Proposal: Clean, respectful email with subject line, expressing enthusiasm for the team, framing the value proposition, and proposing {currency} {target_salary:,}.
2. Phone Call Talking Points: 3-4 bullet points candidate can keep on their screen during a negotiation call with the recruiter.
"""

    try:
        raw_text = await complete(prompt=prompt, system=system_prompt, temperature=0.3)
        return {
            "negotiation_script": sanitize_ai_text(raw_text),
            "suggested_target": target_salary,
            "currency": currency,
        }
    except Exception as e:
        logger.warning(f"LLM negotiation script generation failed: {e}. Returning template.")
        return {
            "negotiation_script": (
                f"Subject: {role} Offer - Counter Proposal - Excited to Join {company_name}\n\n"
                f"Hi Hiring Team,\n\n"
                f"Thank you so much for extending the offer for the {role} position. I am genuinely excited about "
                f"the vision at {company_name} and looking forward to contributing to the team.\n\n"
                f"Based on my proven track record in {strengths_str}, and current market benchmarks for this seniority, "
                f"I would be thrilled to immediately sign the offer if we could adjust the base compensation to "
                f"{currency} {target_salary:,}.\n\n"
                f"I am confident I will deliver immediate impact, and I hope we can find common ground on this figure. "
                f"Looking forward to hearing your thoughts.\n\n"
                f"Warm regards,"
            ),
            "suggested_target": target_salary,
            "currency": currency,
        }
