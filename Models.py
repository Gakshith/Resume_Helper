from pydantic import BaseModel, Field


class Login(BaseModel):
    UserName: str = Field(..., min_length=3, max_length=50)
    Password: str = Field(..., min_length=4, max_length=128)


class Register(BaseModel):
    UserName: str = Field(..., min_length=3, max_length=50)
    Password: str = Field(..., min_length=4, max_length=128)

class ChatRequest(BaseModel):
    message: str


