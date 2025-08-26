from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import httpx
import uuid
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db, User, Session as SessionModel, create_tables

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"

# Create tables on startup (commented out due to permission issues)
# create_tables()

@router.get("/signup")
def google_signup():
    """Initiate Google OAuth for user signup"""
    state = str(uuid.uuid4())  # Generate state for CSRF protection
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
        "state": f"signup_{state}"
    }
    url = httpx.URL(GOOGLE_AUTH_URI).copy_merge_params(params)
    return RedirectResponse(str(url))

@router.get("/signin")
def google_signin():
    """Initiate Google OAuth for user signin"""
    state = str(uuid.uuid4())  # Generate state for CSRF protection
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "select_account",
        "state": f"signin_{state}"
    }
    url = httpx.URL(GOOGLE_AUTH_URI).copy_merge_params(params)
    return RedirectResponse(str(url))

@router.get("/callback")
async def auth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback for both signup and signin"""
    
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")
    
    # Determine if this is signup or signin based on state
    action = "signin"  # default
    if state.startswith("signup_"):
        action = "signup"
    elif state.startswith("signin_"):
        action = "signin"
    
    # Exchange code for tokens
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        # Get access token
        token_resp = await client.post(GOOGLE_TOKEN_URI, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info from Google
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URI, 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        userinfo = userinfo_resp.json()
    
    user_email = userinfo.get("email")
    user_google_id = userinfo.get("id")
    user_name = userinfo.get("name")
    user_picture = userinfo.get("picture")
    
    if not user_email or not user_google_id:
        raise HTTPException(status_code=400, detail="Invalid user information from Google")
    
    # Handle signup vs signin logic
    if action == "signup":
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_email).first()
        if existing_user:
            return JSONResponse({
                "success": False,
                "message": "User already exists. Please sign in instead.",
                "action": "signup"
            })
        
        # Create new user
        new_user = User(
            google_id=user_google_id,
            email=user_email,
            name=user_name,
            picture=user_picture
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create session
        session_id = str(uuid.uuid4())
        new_session = SessionModel(
            id=session_id,
            user_id=new_user.id,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(new_session)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "User registered successfully",
            "action": "signup",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.name,
                "picture": new_user.picture,
                "created_at": new_user.created_at.isoformat()
            },
            "session_id": session_id
        })
    
    else:  # signin
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_email).first()
        if not existing_user:
            return JSONResponse({
                "success": False,
                "message": "User not found. Please sign up first.",
                "action": "signin"
            })
        
        # Create session
        session_id = str(uuid.uuid4())
        new_session = SessionModel(
            id=session_id,
            user_id=existing_user.id,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(new_session)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "User signed in successfully",
            "action": "signin",
            "user": {
                "id": existing_user.id,
                "email": existing_user.email,
                "name": existing_user.name,
                "picture": existing_user.picture,
                "created_at": existing_user.created_at.isoformat()
            },
            "session_id": session_id
        })

@router.get("/user")
def get_user(session_id: str = Query(...), db: Session = Depends(get_db)):
    """Get user info by session ID"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check if session is expired
    if session.expires_at and session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse({
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at.isoformat()
        }
    })

@router.post("/logout")
def logout(session_id: str = Query(...), db: Session = Depends(get_db)):
    """Logout user by removing session"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
    
    return JSONResponse({
        "success": True,
        "message": "Logged out successfully"
    })
