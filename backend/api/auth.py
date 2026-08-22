import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.business import Business


router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "CHANGE_THIS_SECRET_IN_PRODUCTION"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


class SignupRequest(BaseModel):
    business_name: str
    owner_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    website: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    business_id: int
    business_name: str


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters."
        )

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(business_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(business_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    data: SignupRequest,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Business)
        .filter(Business.email == data.email.lower())
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    business = Business(
        name=data.business_name.strip(),
        owner_name=data.owner_name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        phone=data.phone,
        website=data.website,
        ai_enabled=True,
        active=True,
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    token = create_access_token(business.id)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        business_id=business.id,
        business_name=business.name,
    )


@router.post(
    "/login",
    response_model=AuthResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    business = (
        db.query(Business)
        .filter(Business.email == data.email.lower())
        .first()
    )

    if not business:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    if not business.active:
        raise HTTPException(
            status_code=403,
            detail="This business account is inactive."
        )

    if not verify_password(
        data.password,
        business.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(business.id)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        business_id=business.id,
        business_name=business.name,
    )


def get_current_business(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Business:

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        business_id = payload.get("sub")

        if business_id is None:
            raise credentials_exception

        business_id = int(business_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    business = (
        db.query(Business)
        .filter(Business.id == business_id)
        .first()
    )

    if not business or not business.active:
        raise credentials_exception

    return business


@router.get("/me")
def me(
    business: Business = Depends(get_current_business)
):
    return {
        "id": business.id,
        "business_name": business.name,
        "owner_name": business.owner_name,
        "email": business.email,
        "phone": business.phone,
        "website": business.website,
        "ai_enabled": business.ai_enabled,
        "active": business.active,
        "created_at": business.created_at,
    }
