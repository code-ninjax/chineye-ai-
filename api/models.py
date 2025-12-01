"""
models.py - Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List


class SignupRequest(BaseModel):
    """Request model for user signup"""
    username: str
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepassword123",
            }
        }


class LoginResponse(BaseModel):
    """Response model for login"""
    access_token: str
    token_type: str = "bearer"
    username: str


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?",
            }
        }


class MessageResponse(BaseModel):
    """Response model for a message"""
    message: str
    response: str


class ChatHistoryEntry(BaseModel):
    """Model for a chat history entry"""
    message: str
    response: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    history: List[ChatHistoryEntry]


class ErrorResponse(BaseModel):
    """Response model for errors"""
    detail: str
