from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.enums import UserRole
from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=1, max_length=200)
    role: UserRole
    college_id: int | None = None
    college_name: str | None = Field(default=None, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def _map_frontend_fields(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if not data.get("full_name") and data.get("name"):
                data["full_name"] = data["name"]
            if not data.get("college_name") and data.get("college"):
                data["college_name"] = data["college"]
        return data

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long.")
        return v



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
