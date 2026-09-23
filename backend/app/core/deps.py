"""
Auth dependency.

PLACEHOLDER IMPLEMENTATION — user isolation is fully wired through every
model/query (user_id on every row, every CRUD service filters by it), but
real authentication is NOT implemented yet. For now the current user is
resolved from an `X-User-Id` header so the rest of the stack (schema, CRUD,
row isolation, RLS policies) can be built and tested end-to-end.

NEXT STEP (see CONTEXTIQ_MASTER_SPEC.md "Auth roadmap"): replace this with
verification of a Supabase-issued JWT (`Authorization: Bearer <token>`),
decoding the `sub` claim as the user id. Because RLS policies already key
off `auth.uid()`, and the DB `users.id` is designed to equal
`auth.users.id`, swapping this dependency is the ONLY change needed —
no schema or route changes required.
"""
import uuid
import logging

from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.config import get_settings

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    """Resolve identity from a verified JWT; permit X-User-Id only in development."""
    settings = get_settings()
    if credentials is not None:
        try:
            claims = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
            subject = claims.get("sub")
            if not subject:
                raise ValueError("missing subject")
            return uuid.UUID(subject)
        except (JWTError, ValueError) as exc:
            logger.info("Rejected invalid bearer token: %s", type(exc).__name__)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.") from exc
    if settings.APP_ENV == "production":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")


def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the full current User row, 404-ing if the header id doesn't exist."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user.")
    return user
