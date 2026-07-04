from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8)
    pw_repeat: str = Field(min_length=8)


class UserLogin(BaseModel):
    id: str
    password: str = Field(min_length=8)

class UserLogout(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: EmailStr
    nickname: str | None = None
    profile_img: int | None = None
    current_learning_id: int | None = None