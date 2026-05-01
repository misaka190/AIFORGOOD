from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.schemas.schemas import LoginRequest, Token, UserCreate, UserOut
from app.services.audit_service import create_audit_log
from app.services.auth_service import login_user, register_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> UserOut:
    user = register_user(db, payload)
    create_audit_log(db, "register", "user", user.id, actor_user_id=user.id, request=request, payload={"email": user.email})
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    token = login_user(db, payload)
    create_audit_log(db, "login", "auth", None, request=request, payload={"email": payload.email})
    return token


@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)) -> UserOut:
    return current_user
