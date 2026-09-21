import email_validator
from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        # Signup specifically checks deliverability (the domain has valid MX
        # records), not just syntax — EmailStr alone would accept a well-formed
        # but non-existent domain like "test@g.com".
        try:
            info = email_validator.validate_email(value, check_deliverability=True)
        except email_validator.EmailNotValidError as exc:
            raise ValueError(str(exc)) from exc
        return info.normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")
        return value


class LoginRequest(BaseModel):
    # Login only checks format, not deliverability — an existing account's
    # domain losing MX records after signup should never lock the user out.
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
