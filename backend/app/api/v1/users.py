import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.task import TaskRead
from app.schemas.user import UserCreate, UserRead, UserSignupWithTasks
from app.services.user_service import authenticate_user, create_user, signup_user_with_tasks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


def _generate_jwt_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = "••••••••••••"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    tasks: List[TaskRead] = []


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup_with_tasks(payload: UserSignupWithTasks, db: Session = Depends(get_db)):
    """
    Registers a new user, saves their cognitive profile, circadian rhythms,
    distraction weights, AND creates their initial focus tasks directly in PostgreSQL.
    """
    user, tasks = signup_user_with_tasks(db, payload)
    token = _generate_jwt_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "tasks": tasks,
    }


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates against the PostgreSQL database and returns JWT token + user tasks.
    """
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = _generate_jwt_token(str(user.id))
    tasks = list(user.tasks) if user.tasks else []
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "tasks": tasks,
    }


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Legacy dev-mode registration."""
    return create_user(db, payload)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
