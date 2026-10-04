"""Application Kanban API: CRUD, status transitions, board view."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.db.models import AppStatus, Application, FollowUp, StatusChange
from app.dependencies import DB, CurrentUser
from app.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    FunnelStats,
    KanbanBoardResponse,
)

router = APIRouter(prefix="/applications", tags=["applications"])

# Follow-up cadence: Day 3, 7, 14 after application
FOLLOW_UP_DAYS = [3, 7, 14]


@router.get("/board", response_model=KanbanBoardResponse)
async def get_kanban_board(user: CurrentUser, db: DB):
    """Get the full Kanban board with applications grouped by status."""
    result = await db.execute(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.user_id == user.id)
        .order_by(Application.position, Application.updated_at.desc())
    )
    applications = result.unique().scalars().all()

    columns: dict[str, list[ApplicationRead]] = defaultdict(list)
    stats: dict[str, int] = defaultdict(int)

    for app in applications:
        key = app.status.value if isinstance(app.status, AppStatus) else app.status
        columns[key].append(ApplicationRead.model_validate(app))
        stats[key] += 1

    return KanbanBoardResponse(columns=dict(columns), stats=dict(stats))


@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(body: ApplicationCreate, user: CurrentUser, db: DB):
    """Add a job to the application tracker."""
    # Check for duplicate
    existing = await db.execute(
        select(Application).where(
            Application.user_id == user.id,
            Application.job_id == body.job_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Application already exists for this job")

    app = Application(
        user_id=user.id,
        job_id=body.job_id,
        tailored_resume_id=body.tailored_resume_id,
        cover_letter_id=body.cover_letter_id,
        status=AppStatus(body.status.value),
        notes=body.notes,
    )
    db.add(app)
    await db.flush()

    # Log the initial status
    change = StatusChange(
        application_id=app.id,
        from_status=None,
        to_status=app.status,
    )
    db.add(change)

    # If status is 'applied', seed follow-up cadence and set applied_at
    if app.status == AppStatus.applied:
        app.applied_at = datetime.now(timezone.utc)
        _seed_follow_ups(db, app)

    await db.flush()
    await db.refresh(app, attribute_names=["job"])
    return ApplicationRead.model_validate(app)


@router.patch("/{app_id}", response_model=ApplicationRead)
async def update_application(app_id: UUID, body: ApplicationUpdate, user: CurrentUser, db: DB):
    """Update application status, notes, or position (Kanban drag)."""
    result = await db.execute(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.id == app_id, Application.user_id == user.id)
    )
    app = result.unique().scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if body.status is not None:
        old_status = app.status
        new_status = AppStatus(body.status.value)

        # Log the status change
        change = StatusChange(
            application_id=app.id,
            from_status=old_status,
            to_status=new_status,
        )
        db.add(change)

        app.status = new_status

        # Set applied_at and seed follow-ups when moving to 'applied'
        if new_status == AppStatus.applied and not app.applied_at:
            app.applied_at = datetime.now(timezone.utc)
            _seed_follow_ups(db, app)

    if body.notes is not None:
        app.notes = body.notes
    if body.position is not None:
        app.position = body.position
    if body.tailored_resume_id is not None:
        app.tailored_resume_id = body.tailored_resume_id
    if body.cover_letter_id is not None:
        app.cover_letter_id = body.cover_letter_id

    await db.flush()
    return ApplicationRead.model_validate(app)


@router.get("/stats", response_model=FunnelStats)
async def get_funnel_stats(user: CurrentUser, db: DB):
    """Conversion funnel and response latency statistics (Feature #20)."""
    from datetime import datetime, timezone

    # 1. Fetch counts by status
    result = await db.execute(
        select(Application.status, func.count())
        .where(Application.user_id == user.id)
        .group_by(Application.status)
    )
    counts = {row[0].value if isinstance(row[0], AppStatus) else row[0]: row[1] for row in result.all()}

    total_applied = counts.get("applied", 0) + counts.get("screening", 0) + counts.get("interviewing", 0)
    screening = counts.get("screening", 0)
    interviewing = counts.get("interview_scheduled", 0) + counts.get("interviewing", 0)
    offers = counts.get("offer_received", 0) + counts.get("negotiating", 0)
    rejected = counts.get("rejected", 0)
    ghosted = counts.get("ghosted", 0)

    # 2. Compute funnel velocity and response latency from applications & status changes
    now = datetime.now(timezone.utc)
    apps_result = await db.execute(
        select(Application).where(Application.user_id == user.id)
    )
    all_apps = apps_result.scalars().all()

    screen_durations: list[float] = []
    reject_durations: list[float] = []
    ghost_risk = 0

    for a in all_apps:
        if not a.applied_at:
            continue
        applied_time = a.applied_at
        if applied_time.tzinfo is None:
            applied_time = applied_time.replace(tzinfo=timezone.utc)

        # Check for ghosting risk (applied > 21 days ago without progression)
        if a.status in (AppStatus.applied, "applied"):
            days_since_apply = (now - applied_time).days
            if days_since_apply > 21:
                ghost_risk += 1

        # Check screening / interview velocity
        if a.status in (
            AppStatus.screening, "screening",
            AppStatus.interview_scheduled, "interview_scheduled",
            AppStatus.interviewing, "interviewing",
            AppStatus.offer_received, "offer_received",
        ):
            screen_durations.append((a.updated_at - applied_time).total_seconds() / 86400.0)

        # Check rejection latency
        if a.status in (AppStatus.rejected, "rejected"):
            reject_durations.append((a.updated_at - applied_time).total_seconds() / 86400.0)

    avg_screen = round(sum(screen_durations) / len(screen_durations), 1) if screen_durations else None
    avg_reject = round(sum(reject_durations) / len(reject_durations), 1) if reject_durations else None

    return FunnelStats(
        total_applied=total_applied,
        screening=screening,
        interviewing=interviewing,
        offers=offers,
        rejected=rejected,
        ghosted=ghosted,
        screen_rate=round(screening / total_applied * 100, 1) if total_applied else None,
        offer_rate=round(offers / interviewing * 100, 1) if interviewing else None,
        avg_days_to_screen=avg_screen,
        avg_days_to_reject=avg_reject,
        ghost_risk_count=ghost_risk,
    )


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(app_id: UUID, user: CurrentUser, db: DB):
    """Remove an application from the tracker."""
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)


def _seed_follow_ups(db: DB, app: Application) -> None:
    """Create Day 3/7/14 follow-up reminders when an application is submitted."""
    now = datetime.now(timezone.utc)
    for day in FOLLOW_UP_DAYS:
        follow_up = FollowUp(
            application_id=app.id,
            day_offset=day,
            scheduled_at=now + timedelta(days=day),
            status="pending",
        )
        db.add(follow_up)
