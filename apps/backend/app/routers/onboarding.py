from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.cv import CVStorage, CVValidationError
from app.db.models import CVDocument, UserProfile
from app.db.session import get_session
from app.repositories import WorkItemRepository
from app.schemas.onboarding import (
    CVStatusResponse,
    OnboardingResponse,
    OnboardingStepsResponse,
    PreferencesStepRequest,
    RoleStepRequest,
)


router = APIRouter(prefix="/onboarding", tags=["onboarding"])
settings = get_settings()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=OnboardingResponse)
def get_onboarding(user: AuthenticatedUser, session: SessionDependency) -> OnboardingResponse:
    profile = session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    document = _current_cv(session, user.id)
    return _response(profile, document)


@router.put("/role", response_model=OnboardingResponse)
def set_role(
    payload: RoleStepRequest,
    user: AuthenticatedUser,
    session: SessionDependency,
) -> OnboardingResponse:
    with session.begin():
        profile = _profile_for_update(session, user.id)
        if profile is None:
            profile = UserProfile(user_id=user.id)
            session.add(profile)
        profile.desired_role_text = payload.desired_role
        document = _current_cv(session, user.id)
        profile.onboarding_status = _derive_status(profile, document)
    return _response(profile, document)


@router.put("/preferences", response_model=OnboardingResponse)
def set_preferences(
    payload: PreferencesStepRequest,
    user: AuthenticatedUser,
    session: SessionDependency,
) -> OnboardingResponse:
    with session.begin():
        profile = _profile_for_update(session, user.id)
        if profile is None or not profile.desired_role_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Complete the desired-role step first",
            )
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
        document = _current_cv(session, user.id)
        profile.onboarding_status = _derive_status(profile, document)
    return _response(profile, document)


@router.post("/cv", response_model=OnboardingResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_cv(
    user: AuthenticatedUser,
    session: SessionDependency,
    file: UploadFile = File(...),
) -> OnboardingResponse:
    profile = session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None or not _profile_preferences_complete(profile):
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete role and preferences before uploading a CV",
        )
    session.rollback()

    storage = CVStorage(
        settings.cv_storage_path,
        maximum_bytes=settings.cv_max_bytes,
        maximum_pages=settings.cv_max_pages,
    )
    try:
        stored = await storage.store(file, user_id=user.id)
    except CVValidationError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": str(error)},
        ) from error

    try:
        with session.begin():
            profile = _profile_for_update(session, user.id)
            if profile is None or not _profile_preferences_complete(profile):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Onboarding preferences changed during upload",
                )
            session.execute(
                update(CVDocument)
                .where(CVDocument.user_id == user.id, CVDocument.is_current.is_(True))
                .values(is_current=False)
            )
            document = CVDocument(
                user_id=user.id,
                original_filename=stored.original_filename,
                content_type="application/pdf",
                byte_size=stored.byte_size,
                page_count=stored.page_count,
                sha256=stored.sha256,
                storage_key=stored.storage_key,
                extraction_status="pending",
                facts_status="pending",
                is_current=True,
            )
            session.add(document)
            session.flush()
            WorkItemRepository.enqueue(
                session,
                kind="cv.extract",
                idempotency_key=f"cv.extract:{document.id}:{document.sha256}",
                subject_type="cv_document",
                subject_id=document.id,
                payload={"cv_document_id": str(document.id)},
                max_attempts=2,
            )
            profile.onboarding_status = "processing"
        return _response(profile, document)
    except Exception:
        storage.delete(stored.storage_key)
        raise


def _profile_for_update(session: Session, user_id) -> UserProfile | None:
    return session.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
        .with_for_update()
    )


def _current_cv(session: Session, user_id) -> CVDocument | None:
    return session.scalar(
        select(CVDocument)
        .where(CVDocument.user_id == user_id, CVDocument.is_current.is_(True))
        .order_by(CVDocument.created_at.desc())
    )


def _profile_preferences_complete(profile: UserProfile) -> bool:
    if not profile.desired_role_text:
        return False
    if not (profile.accepts_onsite or profile.accepts_hybrid or profile.accepts_remote):
        return False
    if not (profile.accepts_full_time or profile.accepts_part_time):
        return False
    if profile.accepts_onsite or profile.accepts_hybrid:
        if not (
            profile.home_country_code
            and profile.home_latitude is not None
            and profile.home_longitude is not None
            and profile.travel_radius_km is not None
            and profile.onsite_countries
        ):
            return False
    if profile.accepts_remote and not profile.remote_countries:
        return False
    return True


def _derive_status(profile: UserProfile, document: CVDocument | None) -> str:
    if not _profile_preferences_complete(profile) or document is None:
        return "incomplete"
    if document.extraction_status == "error" or document.facts_status == "error":
        return "error"
    if document.extraction_status == "ready" and document.facts_status in {"ready", "review"}:
        return "ready"
    return "processing"


def _response(
    profile: UserProfile | None,
    document: CVDocument | None,
) -> OnboardingResponse:
    preferences_complete = profile is not None and _profile_preferences_complete(profile)
    return OnboardingResponse(
        status=profile.onboarding_status if profile else "incomplete",
        desired_role=profile.desired_role_text if profile else None,
        home_label=profile.home_label if profile else None,
        home_city=profile.home_city if profile else None,
        home_country_code=profile.home_country_code if profile else None,
        home_latitude=float(profile.home_latitude) if profile and profile.home_latitude is not None else None,
        home_longitude=float(profile.home_longitude) if profile and profile.home_longitude is not None else None,
        travel_radius_km=profile.travel_radius_km if profile else None,
        accepts_onsite=profile.accepts_onsite if profile else False,
        accepts_hybrid=profile.accepts_hybrid if profile else False,
        accepts_remote=profile.accepts_remote if profile else False,
        accepts_full_time=profile.accepts_full_time if profile else True,
        accepts_part_time=profile.accepts_part_time if profile else False,
        onsite_countries=list(profile.onsite_countries) if profile else [],
        remote_countries=list(profile.remote_countries) if profile else [],
        steps=OnboardingStepsResponse(
            role=bool(profile and profile.desired_role_text),
            preferences=preferences_complete,
            cv=document is not None,
        ),
        cv=(
            CVStatusResponse(
                id=document.id,
                original_filename=document.original_filename,
                byte_size=document.byte_size,
                page_count=document.page_count,
                detected_language=document.detected_language,
                extraction_status=document.extraction_status,
                extraction_method=document.extraction_method,
                extraction_error_code=document.extraction_error_code,
                facts_status=document.facts_status,
                created_at=document.created_at,
            )
            if document
            else None
        ),
    )
