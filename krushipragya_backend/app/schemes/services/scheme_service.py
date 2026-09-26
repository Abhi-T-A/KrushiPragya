"""Scheme service providing search, filtering, detail retrieval, and farmer read/save states."""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.government import GovernmentScheme, SchemeUserState
from app.schemes.services.scheme_payment_service import SchemePaymentService

logger = logging.getLogger(__name__)


class SchemeService:
    """Service handling scheme discovery, pagination, farmer state, and detail queries."""

    @staticmethod
    def get_schemes_list(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        state: Optional[str] = "Karnataka",
        crop: Optional[str] = None,
        language: str = "kn",
        page: int = 1,
        limit: int = 20,
        user_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve paginated list of government schemes with search and farmer read states."""
        query = select(GovernmentScheme).where(GovernmentScheme.status == "ACTIVE")

        # Filters
        if state and state.lower() != "all":
            query = query.where(
                or_(
                    GovernmentScheme.state.ilike(f"%{state}%"),
                    GovernmentScheme.state.ilike("%Central%"),
                    GovernmentScheme.state.ilike("%All India%"),
                )
            )

        if category and category.lower() != "all":
            query = query.where(GovernmentScheme.category.ilike(f"%{category}%"))

        if crop and crop.strip():
            c_term = crop.strip().lower()
            query = query.where(
                or_(
                    GovernmentScheme.eligibility.ilike(f"%{c_term}%"),
                    GovernmentScheme.description.ilike(f"%{c_term}%"),
                    GovernmentScheme.title.ilike(f"%{c_term}%"),
                )
            )

        if search and search.strip():
            s_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    GovernmentScheme.title.ilike(s_term),
                    GovernmentScheme.title_kn.ilike(s_term),
                    GovernmentScheme.description.ilike(s_term),
                    GovernmentScheme.benefits.ilike(s_term),
                    GovernmentScheme.department.ilike(s_term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.execute(count_stmt).scalar() or 0

        # Pagination & sorting
        offset = (page - 1) * limit
        query = query.order_by(desc(GovernmentScheme.created_at)).offset(offset).limit(limit)
        schemes = db.execute(query).scalars().all()

        # Load user states for unread badges if user is authenticated
        user_states: Dict[uuid.UUID, SchemeUserState] = {}
        if user_id:
            scheme_ids = [s.id for s in schemes]
            if scheme_ids:
                states = db.execute(
                    select(SchemeUserState).where(
                        SchemeUserState.user_id == user_id,
                        SchemeUserState.scheme_id.in_(scheme_ids),
                    )
                ).scalars().all()
                user_states = {st.scheme_id: st for st in states}

        items = []
        for s in schemes:
            ust = user_states.get(s.id)
            # Unread if never viewed, or if scheme updated after last read
            is_read = False
            is_saved = False
            if ust:
                is_saved = ust.is_saved
                if ust.is_read and ust.read_at and ust.read_at >= s.updated_at:
                    is_read = True

            # Presentation resolution: prioritize Kannada title if requested or available
            display_title = s.title_kn if (language == "kn" and s.title_kn) else s.title
            display_desc = s.description_kn if (language == "kn" and s.description_kn) else s.description
            display_benefits = s.benefits_kn if (language == "kn" and s.benefits_kn) else s.benefits

            items.append({
                "id": str(s.id),
                "name": display_title,
                "title_en": s.title,
                "title_kn": s.title_kn,
                "description": display_desc,
                "department": s.department or "Department of Agriculture",
                "state": s.state or "Karnataka",
                "category": s.category,
                "benefits_summary": display_benefits[:200] if display_benefits else "",
                "application_url": s.application_url,
                "is_read": is_read,
                "is_saved": is_saved,
                "source": {
                    "name": s.source_name or "Official Government Portal",
                    "url": s.source_url,
                    "last_verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
                },
                "fee_info": SchemePaymentService.calculate_scheme_fee_info(s),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })

        return items, total

    @staticmethod
    def get_scheme_detail(
        db: Session,
        scheme_id: uuid.UUID,
        language: str = "kn",
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a specific government scheme including provenance and related schemes."""
        scheme = db.get(GovernmentScheme, scheme_id)
        if not scheme:
            return None

        # Check farmer read/saved state
        is_read = False
        is_saved = False
        if user_id:
            ust = db.execute(
                select(SchemeUserState).where(
                    SchemeUserState.user_id == user_id,
                    SchemeUserState.scheme_id == scheme_id,
                )
            ).scalar_one_or_none()
            if ust:
                is_saved = ust.is_saved
                if ust.is_read and ust.read_at and ust.read_at >= scheme.updated_at:
                    is_read = True

        # Related schemes in the same category or department
        related = db.execute(
            select(GovernmentScheme).where(
                GovernmentScheme.id != scheme.id,
                GovernmentScheme.status == "ACTIVE",
                or_(
                    GovernmentScheme.category == scheme.category,
                    GovernmentScheme.department == scheme.department,
                ),
            ).order_by(desc(GovernmentScheme.created_at)).limit(3)
        ).scalars().all()

        related_items = [
            {
                "id": str(r.id),
                "name": r.title_kn if (language == "kn" and r.title_kn) else r.title,
                "category": r.category,
                "department": r.department,
            }
            for r in related
        ]

        def split_points(text_val: Optional[str]) -> List[str]:
            if not text_val:
                return []
            lines = [l.strip(" -•\t") for l in text_val.split("\n") if l.strip()]
            return lines if lines else [text_val.strip()]

        display_title = scheme.title_kn if (language == "kn" and scheme.title_kn) else scheme.title
        display_desc = scheme.description_kn if (language == "kn" and scheme.description_kn) else scheme.description
        elig_items = split_points(scheme.eligibility_kn if (language == "kn" and scheme.eligibility_kn) else scheme.eligibility)
        ben_items = split_points(scheme.benefits_kn if (language == "kn" and scheme.benefits_kn) else scheme.benefits)
        proc_items = split_points(scheme.application_process_kn if (language == "kn" and scheme.application_process_kn) else scheme.application_process)
        doc_items = split_points(scheme.documents_required_kn if (language == "kn" and scheme.documents_required_kn) else scheme.documents_required)

        return {
            "id": str(scheme.id),
            "name": display_title,
            "title_en": scheme.title,
            "title_kn": scheme.title_kn,
            "description": display_desc,
            "department": scheme.department or "Department of Agriculture",
            "state": scheme.state or "Karnataka",
            "category": scheme.category,
            "status": scheme.status,
            "eligibility": elig_items,
            "benefits": ben_items,
            "application_process": proc_items,
            "documents_required": doc_items,
            "application_url": scheme.application_url,
            "is_read": is_read,
            "is_saved": is_saved,
            "source": {
                "name": scheme.source_name or "Official Government Portal",
                "url": scheme.source_url,
                "last_verified_at": scheme.last_verified_at.isoformat() if scheme.last_verified_at else None,
                "source_type": scheme.source_type,
                "crawler_status": scheme.crawler_status or "VERIFIED",
            },
            "fee_info": SchemePaymentService.calculate_scheme_fee_info(scheme),
            "related_schemes": related_items,
            "created_at": scheme.created_at.isoformat() if scheme.created_at else None,
            "updated_at": scheme.updated_at.isoformat() if scheme.updated_at else None,
        }

    @staticmethod
    def mark_as_read(db: Session, user_id: uuid.UUID, scheme_id: uuid.UUID) -> bool:
        """Mark a scheme as read for the user to clear the Unread tag."""
        scheme = db.get(GovernmentScheme, scheme_id)
        if not scheme:
            return False

        ust = db.execute(
            select(SchemeUserState).where(
                SchemeUserState.user_id == user_id,
                SchemeUserState.scheme_id == scheme_id,
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if ust:
            ust.is_read = True
            ust.read_at = now
        else:
            ust = SchemeUserState(
                id=uuid.uuid4(),
                user_id=user_id,
                scheme_id=scheme_id,
                is_read=True,
                read_at=now,
                is_saved=False,
            )
            db.add(ust)

        db.commit()
        return True

    @staticmethod
    def toggle_saved(db: Session, user_id: uuid.UUID, scheme_id: uuid.UUID, is_saved: bool) -> bool:
        """Save or bookmark a scheme for the farmer."""
        scheme = db.get(GovernmentScheme, scheme_id)
        if not scheme:
            return False

        ust = db.execute(
            select(SchemeUserState).where(
                SchemeUserState.user_id == user_id,
                SchemeUserState.scheme_id == scheme_id,
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if ust:
            ust.is_saved = is_saved
            ust.saved_at = now if is_saved else None
        else:
            ust = SchemeUserState(
                id=uuid.uuid4(),
                user_id=user_id,
                scheme_id=scheme_id,
                is_read=False,
                is_saved=is_saved,
                saved_at=now if is_saved else None,
            )
            db.add(ust)

        db.commit()
        return True
