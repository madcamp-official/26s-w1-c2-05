import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

# DB와 연결 가능한 engine 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

with engine.begin() as conn:
    inspector = inspect(conn)
    # 현재 컬럼 목록
    columns = [c["name"] for c in inspector.get_columns("users")]

    # 없으면 추가
    if "current_level" not in columns:
        conn.execute(text(f"""
            ALTER TABLE {"users"}
            ADD COLUMN {"current_level"} {"INTEGER"}
        """))
        print(f"column added.")
    else:
        print(f"already exists.")

    columns = [c["name"] for c in inspector.get_columns("learning_progresses")]

    # 없으면 추가
    if "language_total" not in columns:
        conn.execute(text(f"""
            ALTER TABLE {"learning_progresses"}
            ADD COLUMN {"language_total"} {"INTEGER"}
        """))
        print(f"column added.")
    else:
        print(f"already exists.")
    if "total_answers" not in columns:
        conn.execute(text(f"""
            ALTER TABLE {"learning_progresses"}
            ADD COLUMN {"total_answers"} {"INTEGER"}
        """))
        print(f"column added.")
    else:
        print(f"already exists.")
    if "correct_answers" not in columns:
        conn.execute(text(f"""
            ALTER TABLE {"learning_progresses"}
            ADD COLUMN {"correct_answers"} {"INTEGER"}
        """))
        print(f"column added.")
    else:
        print(f"already exists.")

# 접속 끝나도 연결 유지
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()