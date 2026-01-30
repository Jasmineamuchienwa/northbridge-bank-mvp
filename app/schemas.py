from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class DepositRequest(BaseModel):
    amount: float

class TransferRequest(BaseModel):
    to_email: EmailStr
    amount: float
