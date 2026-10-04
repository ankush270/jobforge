"""Salaries & Negotiation Intelligence API."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.dependencies import CurrentUser
from app.services.intelligence.salary_intel import (
    analyze_salary_gap,
    generate_counter_negotiation_script,
    lookup_market_benchmark,
)

router = APIRouter(prefix="/salaries", tags=["salaries"])


class SalaryGapRequest(BaseModel):
    offered_salary: int
    role: str
    experience_yrs: int | None = None
    location: str | None = None
    currency: str = "INR"


class NegotiateRequest(BaseModel):
    company_name: str
    role: str
    current_offer: int
    target_salary: int
    currency: str = "INR"
    key_strengths: list[str] | None = None


@router.get("/benchmark")
async def get_salary_benchmark(
    role: str = Query(..., description="Job title, e.g. 'Senior Backend Engineer'"),
    experience_yrs: int | None = Query(None, description="Years of experience"),
    location: str | None = Query(None, description="City or country"),
    currency: str = Query("INR", description="INR or USD"),
    user: CurrentUser = None,
):
    """Retrieve market compensation benchmarks (P25, P50 Median, P75, P90)."""
    return lookup_market_benchmark(
        role=role,
        experience_yrs=experience_yrs,
        location=location,
        currency=currency,
    )


@router.post("/analyze-gap")
async def analyze_offer_gap(body: SalaryGapRequest, user: CurrentUser):
    """Analyze the gap between an offered salary and market percentiles."""
    benchmark = lookup_market_benchmark(
        role=body.role,
        experience_yrs=body.experience_yrs,
        location=body.location,
        currency=body.currency,
    )
    analysis = analyze_salary_gap(offered_salary=body.offered_salary, benchmark=benchmark)
    return {
        "benchmark": benchmark,
        "analysis": analysis,
    }


@router.post("/negotiate")
async def create_negotiation_script(body: NegotiateRequest, user: CurrentUser):
    """Generate a persuasive counter-offer negotiation email and talking points."""
    return await generate_counter_negotiation_script(
        company_name=body.company_name,
        role=body.role,
        current_offer=body.current_offer,
        target_salary=body.target_salary,
        currency=body.currency,
        key_strengths=body.key_strengths,
    )
