from pydantic import BaseModel, Field, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class SignupRequest(BaseModel):
    email : EmailStr
    username : str
    password : str

class LoginRequest(BaseModel):
    email: EmailStr
    password : str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthUserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRequest(BaseModel):
    refresh_token : str = Field(..., description="The refresh token provided during loggin")
