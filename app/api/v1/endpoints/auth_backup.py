"""
Authentication API Endpoints - Complete Enterprise Auth System
Includes login, signup, OAuth (Google, GitHub, Microsoft), profile management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import httpx
import logging

# Initialize
logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock settings for development
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str] = None
    password: str
    confirm_password: str
    agreed_to_terms: bool = True
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    organization: Optional[str] = None
    role: str = "user"
    is_verified: bool = False
    avatar_url: Optional[str] = None
    oauth_provider: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# Mock user data for development
MOCK_USERS = {
    "admin@opsflow.ai": {
        "id": "user-001",
        "email": "admin@opsflow.ai",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret123
        "first_name": "Admin",
        "last_name": "User",
        "organization": "OpsFlow Guardian",
        "is_active": True,
        "is_verified": True,
        "role": "admin",
        "created_at": datetime.utcnow(),
        "last_login": None
    },
    "john.doe@company.com": {
        "id": "user-002", 
        "email": "john.doe@company.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret123
        "first_name": "John",
        "last_name": "Doe",
        "organization": "TechCorp Inc.",
        "is_active": True,
        "is_verified": True,
        "role": "manager",
        "created_at": datetime.utcnow(),
        "last_login": None
    }
}

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with email and password"""
    user_data = MOCK_USERS.get(email)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return user_data

# Authentication Endpoints

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: SignupRequest):
    """Register new user account"""
    try:
        logger.info(f"🔐 User registration attempt: {request.email}")
        
        # Check if user already exists
        if request.email in MOCK_USERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = f"user-{secrets.token_hex(8)}"
        hashed_password = get_password_hash(request.password)
        
        user_data = {
            "id": user_id,
            "email": request.email,
            "hashed_password": hashed_password,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "organization": request.organization,
            "is_active": True,
            "is_verified": False,  # Would send verification email in real impl
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Store user (in real implementation, save to database)
        MOCK_USERS[request.email] = user_data
        logger.info(f"✅ Created new user account: {user_data['email']}")
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data["email"], "user_id": user_data["id"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(**user_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(request: LoginRequest):
    """User login with email and password"""
    try:
        logger.info(f"🔐 Login attempt: {request.email}")
        
        # Authenticate user
        user_data = authenticate_user(request.email, request.password)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create tokens
        token_data = {"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        access_token_expires = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 24 if request.remember_me 
            else ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_data)
        
        # Update last login
        user_data["last_login"] = datetime.utcnow()
        
        logger.info(f"✅ User logged in successfully: {user_data['email']}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=UserProfile(**user_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: dict):
    """Refresh access token using refresh token"""
    try:
        refresh_token = request.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )
        
        # Verify refresh token
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            token_type: str = payload.get("type")
            
            if email is None or user_id is None or token_type != "refresh":
                raise JWTError
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user_data = MOCK_USERS.get(email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(**user_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout_user():
    """Logout user (mock implementation)"""
    try:
        logger.info("👋 User logged out")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# OAuth Endpoints (Mock)

@router.get("/oauth/google")
async def oauth_google_login():
    """Initiate Google OAuth login (Mock)"""
    try:
        # In real implementation, redirect to Google OAuth
        logger.info("🔐 Google OAuth login initiated (Mock)")
        
        # Mock successful OAuth
        user_data = {
            "id": f"google-user-{secrets.token_hex(8)}",
            "email": "user@gmail.com",
            "first_name": "Google",
            "last_name": "User",
            "organization": "Google Inc.",
            "is_active": True,
            "is_verified": True,
            "role": "user",
            "oauth_provider": "google",
            "avatar_url": "https://via.placeholder.com/150",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        # Store user
        MOCK_USERS[user_data["email"]] = user_data
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data["email"], "user_id": user_data["id"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(**user_data)
        )
        
    except Exception as e:
        logger.error(f"❌ Google OAuth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth login failed"
        )

@router.get("/oauth/github")
async def oauth_github_login():
    """Initiate GitHub OAuth login (Mock)"""
    try:
        logger.info("🔐 GitHub OAuth login initiated (Mock)")
        
        # Mock successful OAuth
        user_data = {
            "id": f"github-user-{secrets.token_hex(8)}",
            "email": "user@github.com",
            "first_name": "GitHub",
            "last_name": "User",
            "organization": "GitHub Inc.",
            "is_active": True,
            "is_verified": True,
            "role": "user",
            "oauth_provider": "github",
            "avatar_url": "https://github.com/identicons/sample.png",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        # Store user
        MOCK_USERS[user_data["email"]] = user_data
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data["email"], "user_id": user_data["id"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(**user_data)
        )
        
    except Exception as e:
        logger.error(f"❌ GitHub OAuth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth login failed"
        )

@router.get("/oauth/microsoft")
async def oauth_microsoft_login():
    """Initiate Microsoft OAuth login (Mock)"""
    try:
        logger.info("🔐 Microsoft OAuth login initiated (Mock)")
        
        # Mock successful OAuth
        user_data = {
            "id": f"microsoft-user-{secrets.token_hex(8)}",
            "email": "user@outlook.com",
            "first_name": "Microsoft",
            "last_name": "User",
            "organization": "Microsoft Corp.",
            "is_active": True,
            "is_verified": True,
            "role": "user",
            "oauth_provider": "microsoft",
            "avatar_url": "https://via.placeholder.com/150",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        # Store user
        MOCK_USERS[user_data["email"]] = user_data
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_data["email"], "user_id": user_data["id"], "role": user_data["role"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_data["email"], "user_id": user_data["id"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfile(**user_data)
        )
        
    except Exception as e:
        logger.error(f"❌ Microsoft OAuth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Microsoft OAuth login failed"
        )

# Profile Management

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile"""
    try:
        # Verify token
        token = authorization.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user_data = MOCK_USERS.get(email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(**user_data)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    profile_data: dict,
    authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """Update current user profile"""
    try:
        # Verify token
        token = authorization.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user_data = MOCK_USERS.get(email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update profile fields
        if "first_name" in profile_data:
            user_data["first_name"] = profile_data["first_name"]
        if "last_name" in profile_data:
            user_data["last_name"] = profile_data["last_name"]
        if "organization" in profile_data:
            user_data["organization"] = profile_data["organization"]
        
        logger.info(f"📝 Updated user profile: {user_data['email']}")
        
        return UserProfile(**user_data)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    authorization: HTTPAuthorizationCredentials = Depends(security)
):
    """Change user password"""
    try:
        # Verify token
        token = authorization.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user_data = MOCK_USERS.get(email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(request.current_password, user_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        user_data["hashed_password"] = get_password_hash(request.new_password)
        
        logger.info(f"🔑 Password changed for user: {user_data['email']}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Password Reset (Mock)

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Send password reset email (Mock)"""
    try:
        logger.info(f"📧 Password reset requested for: {request.email}")
        
        # In real implementation, send email with reset link
        return {"message": "Password reset email sent (if email exists)"}
        
    except Exception as e:
        logger.error(f"❌ Password reset request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password with token (Mock)"""
    try:
        logger.info(f"🔑 Password reset with token: {token[:10]}...")
        
        # In real implementation, verify token and update password
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        logger.error(f"❌ Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
async def login(credentials: Dict[str, Any] = Body(...)):
    """User login endpoint"""
    try:
        email = credentials.get("email", "")
        password = credentials.get("password", "")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        # Mock authentication - replace with real authentication logic
        if email == "admin@opsflow.com" and password == "admin123":
            user_data = {
                "user_id": "user-001",
                "email": email,
                "name": "Admin User",
                "role": "administrator",
                "permissions": ["read", "write", "approve", "admin"],
                "company": "OpsFlow Inc"
            }
            
            # Mock JWT token
            token_data = {
                "access_token": f"mock-jwt-token-{uuid.uuid4()}",
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": f"mock-refresh-token-{uuid.uuid4()}"
            }
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user_data,
                "tokens": token_data
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/register")
async def register(registration_data: Dict[str, Any] = Body(...)):
    """User registration endpoint"""
    try:
        email = registration_data.get("email", "")
        password = registration_data.get("password", "")
        name = registration_data.get("name", "")
        company = registration_data.get("company", "")
        
        if not all([email, password, name]):
            raise HTTPException(status_code=400, detail="Email, password, and name are required")
        
        # Mock registration - replace with real registration logic
        user_data = {
            "user_id": f"user-{uuid.uuid4()}",
            "email": email,
            "name": name,
            "role": "user",
            "company": company,
            "created_at": datetime.utcnow().isoformat(),
            "is_verified": False
        }
        
        return {
            "success": True,
            "message": "Registration successful. Please verify your email.",
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/refresh")
async def refresh_token(token_data: Dict[str, Any] = Body(...)):
    """Refresh access token"""
    try:
        refresh_token = token_data.get("refresh_token", "")
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        # Mock token refresh - replace with real token validation and refresh
        new_token_data = {
            "access_token": f"mock-jwt-token-{uuid.uuid4()}",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": f"mock-refresh-token-{uuid.uuid4()}"
        }
        
        return {
            "success": True,
            "tokens": new_token_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout")
async def logout():
    """User logout endpoint"""
    try:
        # Mock logout - in real implementation, invalidate the token
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me")
async def get_current_user():
    """Get current user information"""
    try:
        # Mock user data - replace with real user retrieval based on JWT token
        user_data = {
            "user_id": "user-001",
            "email": "admin@opsflow.com",
            "name": "Admin User",
            "role": "administrator",
            "permissions": ["read", "write", "approve", "admin"],
            "company": "OpsFlow Inc",
            "last_login": "2025-01-23T10:00:00Z",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "timezone": "UTC"
            }
        }
        
        return {
            "success": True,
            "user": user_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user information")
