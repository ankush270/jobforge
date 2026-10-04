"""Companies API: list and company intel & red flags."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, select

from app.db.models import Company
from app.dependencies import DB, CurrentUser
from app.schemas import CompanyRead
from app.services.intelligence.company_intel import analyze_company_intel

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyRead])
async def list_companies(db: DB, user: CurrentUser):
    """List companies discovered across jobs."""
    result = await db.execute(select(Company).order_by(Company.created_at.desc()).limit(100))
    return [CompanyRead.model_validate(c) for c in result.scalars().all()]


@router.get("/{identifier}/intel")
async def get_company_intel(identifier: str, db: DB, user: CurrentUser):
    """Retrieve or generate deep intelligence and red flag assessment for a company."""
    # Lookup by UUID or by slug
    query = select(Company)
    try:
        u = UUID(identifier)
        query = query.where(Company.id == u)
    except ValueError:
        query = query.where(or_(Company.slug == identifier.lower(), Company.name.ilike(identifier)))

    company = (await db.execute(query)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # If intel already cached in company_info, return it
    if company.company_info and company.company_info.get("overview"):
        return {
            "company_id": str(company.id),
            "name": company.name,
            "slug": company.slug,
            "tier": company.tier,
            "intel": company.company_info,
        }

    # Otherwise, run live intelligence analysis
    intel = await analyze_company_intel(company_name=company.name, domain=company.domain)

    company.company_info = intel
    company.tier = intel.get("tier", company.tier)
    await db.flush()

    return {
        "company_id": str(company.id),
        "name": company.name,
        "slug": company.slug,
        "tier": company.tier,
        "intel": intel,
    }


# ══════════════════════════════════════════════════
# Target Companies Management (290+ Master List)
# ══════════════════════════════════════════════════

import json
from pathlib import Path
from app.schemas import TargetCompanyCreate, TargetCompanyRead


def _get_target_file_path() -> Path:
    candidates = [
        Path("target_companies.json"),
        Path(__file__).resolve().parents[4] / "target_companies.json",
        Path("e:/Projects/job/extracted_features/target_companies.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


@router.get("/targets", response_model=list[TargetCompanyRead])
async def list_target_companies(
    search: str | None = None,
    category: str | None = None,
):
    """Retrieve all tracked target companies with categories and pre-filtered URLs."""
    path = _get_target_file_path()
    if not path.exists():
        return []

    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return []

    results = []
    for item in items:
        if search:
            s_low = search.lower()
            if s_low not in item.get("name", "").lower() and s_low not in item.get("category", "").lower():
                continue
        if category and category.lower() != "all":
            if category.lower() not in item.get("category", "").lower():
                continue
        results.append(TargetCompanyRead.model_validate(item))

    return results


@router.post("/targets", response_model=TargetCompanyRead, status_code=201)
async def add_target_company(body: TargetCompanyCreate):
    """Add a new company to the target companies directory and link registry."""
    path = _get_target_file_path()
    items = []
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            items = []

    # Check for existing
    for it in items:
        if it.get("name", "").lower() == body.name.lower():
            raise HTTPException(status_code=409, detail=f"Company '{body.name}' is already in target list")

    from app.services.scraper.ats_scanners import discover_ats_vendor
    ats_info = discover_ats_vendor(body.careers_url)
    vendor = "Direct Portal"
    if ats_info.get("vendor"):
        vendor = f"{ats_info['vendor'].capitalize()} API"

    new_item = {
        "name": body.name.strip(),
        "category": body.category.strip() or "Tech / Product",
        "careers_url": body.careers_url.strip(),
        "ats_or_portal": vendor,
        "locations_in_india": body.locations_in_india or ["India / Remote"],
        "status": "verified"
    }

    items.append(new_item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    # Also append to link.txt if available
    link_path = path.parent / "link.txt"
    if link_path.exists():
        try:
            with open(link_path, "a", encoding="utf-8") as f:
                f.write(f"{new_item['name']}: {new_item['careers_url']}\n")
        except Exception:
            pass

    return TargetCompanyRead.model_validate(new_item)


@router.delete("/targets/{company_name}")
async def remove_target_company(company_name: str):
    """Remove a company from the target companies directory."""
    path = _get_target_file_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Target companies registry not found")

    with open(path, encoding="utf-8") as f:
        items = json.load(f)

    initial_len = len(items)
    filtered = [it for it in items if it.get("name", "").lower() != company_name.lower()]

    if len(filtered) == initial_len:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found in target list")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2)

    return {"message": f"Company '{company_name}' removed from targets", "remaining": len(filtered)}

