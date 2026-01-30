from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.config import settings
from app.db import SessionLocal
from app.models import User, Account
from app.schemas import Token, UserCreate
from app.security import hash_password, verify_password

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/register", response_model=Token)
def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        write_audit_log(
            db=db,
            actor_email=user.email,
            action="AUTH.REGISTER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="Email already registered")

    role = "admin" if user.email == "admin@northbridge.com" else "user"

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_account = Account(user_id=new_user.id, balance=0.0)
    db.add(new_account)
    db.commit()

    write_audit_log(
        db=db,
        actor_email=new_user.email,
        action="AUTH.REGISTER.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    token = create_access_token({"sub": new_user.email, "role": new_user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        write_audit_log(
            db=db,
            actor_email=form_data.username,
            action="AUTH.LOGIN.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    write_audit_log(
        db=db,
        actor_email=db_user.email,
        action="AUTH.LOGIN.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    token = create_access_token({"sub": db_user.email, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}
