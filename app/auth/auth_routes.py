from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate, Token
from app.auth.models import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.db.database import get_db
from app.db.crud import get_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    create_user(
        db,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    return {"message": "User registered successfully"}

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token}
