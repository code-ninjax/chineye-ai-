"""
main.py - FastAPI server with all endpoints and proper CORS
"""

import os
import traceback
from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.models import (
    SignupRequest, LoginRequest, LoginResponse, SendMessageRequest,
    MessageResponse, ChatHistoryResponse, ChatHistoryEntry
)
from backend.auth import (
    hash_password, verify_password, create_access_token,
    verify_token, extract_user_id_from_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.database import (
    create_user, get_user_by_email, get_user_by_id, save_chat_message,
    get_chat_history, user_exists, subscribe_to_newsletter
)
from backend.chatbot import chatbot_response

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Chineye AI Chatbot API",
    description="Full-stack chatbot with JWT authentication",
    version="1.0.0",
)

# ============================================================================
# CORS MIDDLEWARE - MUST BE FIRST
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        user_id = extract_user_id_from_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


# ============================================================================
# HEALTH & ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Chineye AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Chineye AI API"}


@app.get("/api/health")
async def api_health_check():
    """Health check endpoint under /api for hosted verification"""
    return {"status": "ok", "service": "Chineye AI API"}


@app.get("/test-db")
async def test_db():
    """Test database connection"""
    try:
        from database import get_supabase_client
        client = get_supabase_client()
        response = client.table("users").select("*").limit(1).execute()
        return {
            "status": "connected",
            "message": "Database connection successful",
            "users_count": response.count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    
    try:
        # Validate input
        if len(request.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters"
            )
        
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        if len(request.password) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be 72 characters or less"
            )
        
        # Check if user already exists
        if user_exists(username=request.username, email=request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Hash password and create user
        password_hash = hash_password(request.password)
        user_data = create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash
        )
        
        return {
            "message": "User created successfully",
            "email": request.email,
            "username": request.username,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in signup: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@app.post("/api/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    
    try:
        user = get_user_by_email(request.email)
        
        if not user or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user["username"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/api/send-message")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message and get a chatbot response"""
    
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Generate bot response
        bot_response = chatbot_response(request.message)
        
        # Save to database
        try:
            save_chat_message(
                user_id=current_user["id"],
                message=request.message,
                response=bot_response
            )
        except Exception as e:
            print(f"Warning: Could not save message: {str(e)}")
        
        return {
            "message": request.message,
            "response": bot_response
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in send_message: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Send message failed: {str(e)}"
        )


@app.get("/api/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    """Get chat history for current user"""
    
    try:
        history = get_chat_history(user_id=current_user["id"])
        
        # Convert to proper format
        formatted_history = [
            {
                "message": entry["message"],
                "response": entry["response"],
                "timestamp": entry["timestamp"],
            }
            for entry in history
        ]
        
        return {"history": formatted_history}
    except Exception as e:
        print(f"ERROR in get_history: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get history failed: {str(e)}"
        )


@app.post("/api/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    return {
        "message": "Logged out successfully",
        "username": current_user["username"]
    }


# ============================================================================
# NEWSLETTER ENDPOINTS
# ============================================================================

@app.post("/api/newsletter")
async def subscribe_newsletter(request: dict):
    """Subscribe email to newsletter"""
    
    try:
        email = request.get("email", "").strip()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Basic email validation
        if "@" not in email or "." not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Subscribe to newsletter
        subscription = subscribe_to_newsletter(email)
        
        return {
            "message": "Successfully subscribed to newsletter",
            "email": email,
            "subscribed_at": subscription.get("subscribed_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        # Check if it's a duplicate email error
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already subscribed"
            )
        print(f"ERROR in subscribe_newsletter: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Newsletter subscription failed: {str(e)}"
        )


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
