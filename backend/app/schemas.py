from pydantic import BaseModel, EmailStr

class AccountCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    contact: str

class AccountLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ReviewResponse(BaseModel):
    id: int
    email: str
    code: str
    static_result: str | None
    ai_result: str | None
    created_at: str