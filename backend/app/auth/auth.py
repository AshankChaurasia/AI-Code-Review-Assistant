from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from model.account_database import Accounts
from Database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # set in .env for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class AccountCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    contact: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AccountSchema(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str, db: Session):
    return db.query(Accounts).filter(Accounts.email == email).first()

def authenticate_user(email: str, password: str, db: Session):
    user = get_user_by_email(email, db)
    if not user or not verify_password(password, user.password):
        return False
    return user

@router.post("/signup")
def signup(account: AccountCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(Accounts).filter(Accounts.email == account.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        if len(account.password.encode("utf-8")) > 72:
            raise HTTPException(status_code=400, detail="Password too long, max 72 bytes")
        hashed_pw = hash_password(account.password)
        new_user = Accounts(
            name=account.name,
            email=account.email,
            password=hashed_pw,
            contact=account.contact
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Signup successful!", "user_id": new_user.id}
    except Exception as e:
        print("Signup error:", e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

def GetCurrentUser(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(email, db)
    if user is None:
        raise credentials_exception
    return user.email