from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserLogout, Token, UserResponse
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 확인
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다."
        )

    # 사용자 이름 중복 확인
    db_user = db.query(User).filter(User.user_id == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="중복된 ID입니다."
        )

    # 비밀번호 및 비밀번호 확인 동일 여부 확인
    if user.password != user.pw_repeat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호와 비밀번호 확인 문자가 같은지 확인해주세요."
        )

    # 비밀번호 요구사항 확인
    if len(user.password) < 8 or not any(char.isdigit() for char in user.password) or not any(char.isalpha() for char in user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 숫자와 문자로 구성되고 8자리 이상이어야 합니다."
        )

    # 비밀번호 해싱 및 사용자 생성
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        user_id=user.username,
        hashed_password=hashed_password,
        nickname="The curiositarian",
        profile_img=0,
        current_learning_id=0,
    )
    # 데이터베이스에 저장
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 토큰 유효 시간
 
@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # 사용자 확인
    user = db.query(User).filter(User.user_id == user_credentials.id).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect id or password"
        )

    # 토큰 생성
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=30)
    )

    db.add(RefreshToken(refresh_token=refresh_token, id=user.user_id))
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout", response_model=dict)
async def logout(user_logout: UserLogout, db: Session = Depends(get_db)):
    # 로그아웃 처리: 서버에서 관리하는 refresh token을 삭제
    token =  db.query(RefreshToken).filter(RefreshToken.refresh_token == user_logout.refresh_token).delete()
    db.commit()
    if not token:
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Invalid refresh-token."
          )

    return {"message": "로그아웃 하였습니다."}