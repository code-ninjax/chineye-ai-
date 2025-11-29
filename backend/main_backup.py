"""
main.py - FastAPI server with all endpoints
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional

from models import (
    SignupRequest, LoginRequest, LoginResponse, SendMessageRequest,
    MessageResponse, ChatHistoryResponse, ChatHistoryEntry, ErrorResponse
)
from auth import (
    hash_password, verify_password, create_access_token,
    verify_token, extract_user_id_from_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import (
    create_user, get_user_by_email, get_user_by_id, save_chat_message,
    get_chat_history, user_exists
)
from chatbot import chatbot_response
from datetime import timedelta

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Chineye AI Chatbot API",
    description="A full-stack chatbot application with JWT authentication",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================================ #
# HELPER FUNCTIONS
# ============================================================================ #

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated user from JWT token
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        User data
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "", 1)
    user_id = extract_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# ============================================================================ #
# ROUTES
# ============================================================================ #

@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    """Handle CORS preflight requests"""
    return {}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Chineye AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.post(
    "/api/signup",
    response_model=dict,
    responses={400: {"model": ErrorResponse}}
)
async def signup(request: SignupRequest):
    """
    Register a new user
    
    Args:
        request: Signup request with username, email, password
        
    Returns:
        Success message and redirect info
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
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
        print(f"Signup error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@app.post(
    "/api/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}}
)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token
    
    Args:
        request: Login request with email and password
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException: If credentials are invalid
    """
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
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"]
    )


@app.post(
    "/api/send-message",
    response_model=MessageResponse,
)
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message and get a chatbot response
    
    Args:
        request: Message request
        current_user: Current authenticated user
        
    Returns:
        User message and bot response
        
    Raises:
        HTTPException: If message is empty or save fails
    """
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
        print(f"Error saving message: {str(e)}")
        # Continue anyway - don't block user
    
    return MessageResponse(
        message=request.message,
        response=bot_response
    )


@app.get(
    "/api/history",
    response_model=ChatHistoryResponse,
)
async def get_history(current_user: dict = Depends(get_current_user)):
    """
    Get chat history for current user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of chat history entries
    """
    history = get_chat_history(user_id=current_user["id"])
    
    # Convert to proper format
    formatted_history = [
        ChatHistoryEntry(
            message=entry["message"],
            response=entry["response"],
            timestamp=entry["timestamp"],
        )
        for entry in history
    ]
    
    return ChatHistoryResponse(history=formatted_history)


@app.post("/api/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint (mainly for frontend to clear token)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    return {
        "message": "Logged out successfully",
        "username": current_user["username"]
    }


# ============================================================================ #
# HEALTH CHECK
# ============================================================================ #

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Chineye AI API"}


# ============================================================================ #
# ERROR HANDLERS
# ============================================================================ #

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "detail": exc.detail,
        "status_code": exc.status_code,
    }


# ============================================================================ #
# RUN SERVER
# ============================================================================ #

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
