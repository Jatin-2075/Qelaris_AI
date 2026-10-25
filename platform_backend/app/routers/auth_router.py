from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import uuid

from ..database.database import get_db
from ..models.auth_model import AuthUser
from ..schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse, RefreshTokenRequest, AuthUserResponse
from ..security.security import hash_password, verify_password, create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=AuthUserResponse)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email_existing_user = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    username_existing_user = db.query(AuthUser).filter(AuthUser.username == payload.username).first()

    if email_existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email Already Registered")

    if username_existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username Already Exists")

    new_user = AuthUser(username=payload.username, email=payload.email, password=hash_password(payload.password))

    try:
        db.add(new_user)
        db.flush()
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AuthUser).filter(AuthUser.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {"access_token": create_access_token(user.id), "refresh_token": create_refresh_token(user.id), "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded.get("sub")
        if not user_id or decoded.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = uuid.UUID(user_id)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return {"access_token": create_access_token(user.id), "refresh_token": create_refresh_token(user.id), "token_type": "bearer"}