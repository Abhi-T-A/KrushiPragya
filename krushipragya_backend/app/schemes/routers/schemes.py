"""Public and Farmer-facing Government Schemes API endpoints."""
import logging
import math
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, get_optional_current_user
from app.database.connection import get_db
from app.schemes.schemas import (
    SchemeDetailResponse,
    SchemeListResponse,
    UserActionResponse,
)
from app.schemes.services.scheme_service import SchemeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["Government Schemes"])


@router.get(
    "",
    response_model=SchemeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List government schemes with search, filters, and farmer unread badges",
)
def list_schemes(
    search: Optional[str] = Query(None, description="Search keyword in title, description, or benefits"),
    category: Optional[str] = Query(None, description="Category filter (Subsidy, Insurance, Equipment, Loan, etc.)"),
    state: Optional[str] = Query("Karnataka", description="State filter (default: Karnataka)"),
    crop: Optional[str] = Query(None, description="Filter schemes relevant to a specific crop (e.g. arecanut, paddy)"),
    language: str = Query("kn", pattern="^(kn|en)$", description="Language preference: 'kn' (Kannada) or 'en' (English)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
) -> SchemeListResponse:
    """Retrieve official government schemes filtered by category, state, crop, and search terms.
    
    If the requesting user is authenticated as a farmer, attaches personalized unread badges
    and bookmark states.
    """
    user_id = current_user.id if current_user else None
    items, total = SchemeService.get_schemes_list(
        db=db,
        search=search,
        category=category,
        state=state,
        crop=crop,
        language=language,
        page=page,
        limit=limit,
        user_id=user_id,
    )

    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return SchemeListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get(
    "/{scheme_id}",
    response_model=SchemeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete government scheme details, source provenance, and related schemes",
)
def get_scheme_detail(
    scheme_id: uuid.UUID,
    language: str = Query("kn", pattern="^(kn|en)$", description="Language preference: 'kn' or 'en'"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
) -> SchemeDetailResponse:
    """Retrieve full detail page for an individual scheme matching the reference UI."""
    user_id = current_user.id if current_user else None
    detail = SchemeService.get_scheme_detail(
        db=db,
        scheme_id=scheme_id,
        language=language,
        user_id=user_id,
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Government scheme with id '{scheme_id}' was not found.",
        )

    return SchemeDetailResponse(**detail)


@router.post(
    "/{scheme_id}/read",
    response_model=UserActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a scheme as read to dismiss unread badge",
)
def mark_scheme_read(
    scheme_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserActionResponse:
    """Mark a scheme as read for the currently authenticated farmer."""
    ok = SchemeService.mark_as_read(db=db, user_id=current_user.id, scheme_id=scheme_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Government scheme with id '{scheme_id}' was not found.",
        )
    return UserActionResponse(success=True, message="Scheme marked as read.")


@router.post(
    "/{scheme_id}/save",
    response_model=UserActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Save / bookmark a scheme for the farmer",
)
def save_scheme(
    scheme_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserActionResponse:
    """Bookmark a scheme for quick access."""
    ok = SchemeService.toggle_saved(db=db, user_id=current_user.id, scheme_id=scheme_id, is_saved=True)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Government scheme with id '{scheme_id}' was not found.",
        )
    return UserActionResponse(success=True, message="Scheme saved to your bookmarks.")


@router.delete(
    "/{scheme_id}/save",
    response_model=UserActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove scheme from farmer bookmarks",
)
def unsave_scheme(
    scheme_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserActionResponse:
    """Remove a previously bookmarked scheme."""
    ok = SchemeService.toggle_saved(db=db, user_id=current_user.id, scheme_id=scheme_id, is_saved=False)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Government scheme with id '{scheme_id}' was not found.",
        )
    return UserActionResponse(success=True, message="Scheme removed from your bookmarks.")
