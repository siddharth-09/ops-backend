from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from app.db.database import get_db
from app.core.config import settings
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from passlib.context import CryptContext
from sqlalchemy import text
import httpx

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT secret key and algorithm
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    email: EmailStr
    verification_code: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_code: str
    new_password: str
    confirm_password: str

class TokenData(BaseModel):
    email: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, email: str):
    result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
    user_data = result.fetchone()
    if user_data:
        return type('User', (), dict(user_data._mapping))()
    return None

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def generate_verification_code():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def send_verification_email(email: str, verification_code: str, background_tasks: BackgroundTasks):
    # Email sending logic here - placeholder for now
    print(f"Verification code for {email}: {verification_code}")

def send_reset_email(email: str, reset_code: str, background_tasks: BackgroundTasks):
    # Password reset email logic here - placeholder for now
    print(f"Reset code for {email}: {reset_code}")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate input
    if not user_data.email or not user_data.name or not user_data.password:
        raise HTTPException(
            status_code=400,
            detail="Email, password, and name are required"
        )
    
    # Check if user already exists
    existing_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data.email}).fetchone()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Generate verification code
    verification_code = generate_verification_code()
    
    # Create new user
    try:
        result = db.execute(text("""
            INSERT INTO users (email, name, password_hash, verification_code, is_active, created_at) 
            VALUES (:email, :name, :password_hash, :verification_code, :is_active, :created_at)
            RETURNING id, email, name, is_active
        """), {
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": hashed_password,
            "verification_code": verification_code,
            "is_active": True,  # Set to True for now, change to False for email verification
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        user = result.fetchone()
        
        # Send verification email
        send_verification_email(user_data.email, verification_code, background_tasks)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified. Please check your email.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json")
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    # Validate input
    if not user_data.email or not user_data.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )
    
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified. Please check your email.",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify-email")
async def verify_email(verification_data: EmailVerification, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": verification_data.email})
    user_data = result.fetchone()
    
    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user_data.verification_code != verification_data.verification_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )
    
    db.execute(text("""
        UPDATE users 
        SET is_active = :is_active, verification_code = NULL, verified_at = :verified_at 
        WHERE email = :email
    """), {
        "is_active": True,
        "verified_at": datetime.utcnow(),
        "email": verification_data.email
    })
    
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(password_data: PasswordReset, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": password_data.email})
    user_data = result.fetchone()
    
    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Generate reset code
    reset_code = generate_verification_code()
    
    db.execute(text("""
        UPDATE users 
        SET reset_code = :reset_code, reset_code_expires = :expires 
        WHERE email = :email
    """), {
        "reset_code": reset_code,
        "expires": datetime.utcnow() + timedelta(hours=1),
        "email": password_data.email
    })
    
    db.commit()
    
    # Send reset email
    send_reset_email(password_data.email, reset_code, background_tasks)
    
    return {"message": "Password reset code sent to your email"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )
    
    result = db.execute(text("SELECT * FROM users WHERE reset_code = :reset_code"), {"reset_code": reset_data.reset_code})
    user_data = result.fetchone()
    
    if not user_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset code"
        )
    
    if datetime.utcnow() > user_data.reset_code_expires:
        raise HTTPException(
            status_code=400,
            detail="Reset code has expired"
        )
    
    # Update password
    hashed_password = get_password_hash(reset_data.new_password)
    db.execute(text("""
        UPDATE users 
        SET password_hash = :password_hash, reset_code = NULL, reset_code_expires = NULL 
        WHERE reset_code = :reset_code
    """), {
        "password_hash": hashed_password,
        "reset_code": reset_data.reset_code
    })
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active
    )

@router.get("/dashboard")
async def get_user_dashboard(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get user's workflows
    workflows_result = db.execute(text("SELECT * FROM workflows WHERE created_by = :user_id"), {"user_id": current_user.id})
    workflows = workflows_result.fetchall()
    
    # Get user's agents
    agents_result = db.execute(text("SELECT * FROM agents WHERE created_by = :user_id"), {"user_id": current_user.id})
    agents = agents_result.fetchall()
    
    dashboard_data = {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },
        "stats": {
            "total_workflows": len(workflows),
            "total_agents": len(agents),
            "active_workflows": len([w for w in workflows if w.status == "active"]),
            "active_agents": len([a for a in agents if a.status == "active"])
        },
        "recent_workflows": [
            {
                "id": w.id,
                "name": w.name,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None
            }
            for w in workflows[:5]
        ],
        "recent_agents": [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in agents[:5]
        ]
    }
    
    return dashboard_data

# OAuth Endpoints
@router.get("/oauth/google")
async def google_oauth():
    """Initiate Google OAuth flow"""
    google_client_id = "872245858233-fuvfnftodd3fat983nh1sv47o55fvd0u.apps.googleusercontent.com"
    redirect_uri = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    scope = "openid email profile"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={google_client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}"
    )
    
    return RedirectResponse(url=auth_url)

@router.get("/oauth/google/callback")
async def google_oauth_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    google_client_id = "872245858233-fuvfnftodd3fat983nh1sv47o55fvd0u.apps.googleusercontent.com"
    google_client_secret = "GOCSPX-your-google-client-secret"  # You need to get this from Google Console
    redirect_uri = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    
    # Exchange code for token
    token_data = {
        "code": code,
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post("https://oauth2.googleapis.com/token", data=token_data)
            token_info = token_response.json()
            
            if "access_token" not in token_info:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            # Get user info from Google
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_info['access_token']}"}
            )
            user_info = user_response.json()
        
        # Check if user exists
        existing_user = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": user_info["email"]}).fetchone()
        
        if not existing_user:
            # Create new user
            result = db.execute(text("""
                INSERT INTO users (email, name, is_active, created_at, oauth_provider, oauth_id) 
                VALUES (:email, :name, :is_active, :created_at, :oauth_provider, :oauth_id)
                RETURNING id, email, name, is_active
            """), {
                "email": user_info["email"],
                "name": user_info["name"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "oauth_provider": "google",
                "oauth_id": user_info["id"]
            })
            db.commit()
            user_data = result.fetchone()
            user = type('User', (), dict(user_data._mapping))()
        else:
            user = type('User', (), dict(existing_user._mapping))()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/auth/callback?token={access_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout user (invalidate token on client side)"""
    return {"message": "Successfully logged out"}
