from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional

class SignupRequest(BaseModel):
    email : EmailStr
    username : str
    password : str

class LoginRequest(BaseModel):
    username : str
    password : str

class TokenRequest(BaseModel):
    access_token : str
    refresh_token : str
    token_type : str = "bearer"
    expires_at : Optional[datetime] = None

class RefreshTokenRequest(BaseModel):
    refresh_token : str = Field(..., description="The refresh token provided during loggin")

