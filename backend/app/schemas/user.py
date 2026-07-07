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

class RefreshRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    SurveyCompleted: bool

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: EmailStr
    nickname: str | None = None
    profile_img: int | None = None
    current_learning_id: int | None = None

class OnboardingResponse(BaseModel):
    language: int
    level: str
    StudyGoal: int

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    userID: str
    email: EmailStr
    current_language: str
    target_days: int
    studied_days: int
    daily_streak: int

class UserDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str
    daily_streak: int
    language_total: int
    accuracy_rate: int
    most_weak: str
    most_improved: str
    feedback_voca: str
    feedback_grammar: str
    feedback_dialogue: str
    error_trend: dict