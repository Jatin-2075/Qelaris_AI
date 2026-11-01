import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.database import get_db
from database.models.auth_model import AuthUser
from ..schemas.auth_schema import (
    AuthUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
)
from ..security.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=AuthUserResponse)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(AuthUser).filter(AuthUser.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(AuthUser).filter(AuthUser.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = AuthUser(
        username=payload.username,
        email=payload.email,
        password=hash_password(payload.password),
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create user")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded.get("sub")
        if not user_id or decoded.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = uuid.UUID(user_id)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
