from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.models.models import DoctorReview, User
from app.schemas.schemas import ReviewCreate, ReviewDetailResponse, ReviewResponse
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    request: Request,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    review = db.query(DoctorReview).filter(DoctorReview.prediction_id == payload.prediction_id).first()
    if review:
        review.review_priority = payload.review_priority
        review.review_status = payload.review_status
        review.review_action = payload.review_action
        review.review_note = payload.review_note
        review.reviewed_at = datetime.now(timezone.utc)
    else:
        review = DoctorReview(
            prediction_id=payload.prediction_id,
            reviewer_id=current_user.id,
            review_priority=payload.review_priority,
            review_status=payload.review_status,
            review_action=payload.review_action,
            review_note=payload.review_note,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review)

    db.commit()
    db.refresh(review)
    create_audit_log(db, "review", "doctor_review", review.id, actor_user_id=current_user.id, request=request, payload={"prediction_id": str(payload.prediction_id)})
    return ReviewResponse(review_id=review.id, prediction_id=review.prediction_id, saved=True)


@router.get("/{prediction_id}", response_model=ReviewDetailResponse)
def get_review(
    prediction_id: str,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db),
) -> ReviewDetailResponse:
    del current_user
    review = db.query(DoctorReview).filter(DoctorReview.prediction_id == prediction_id).first()
    if not review:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    return ReviewDetailResponse(
        review_id=review.id,
        prediction_id=review.prediction_id,
        reviewer_id=review.reviewer_id,
        review_priority=review.review_priority,
        review_status=review.review_status,
        review_action=review.review_action,
        review_note=review.review_note,
        reviewed_at=review.reviewed_at,
    )
