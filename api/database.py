"""
database.py - Supabase database connection and helper functions
"""

import os
from typing import Optional, List, Any
from datetime import datetime


# Supabase client - lazy import to avoid import-time crashes in serverless
supabase: Optional[Any] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client (lazy initialization)
    """
    global supabase
    
    if supabase is None:
        # Lazy import to ensure missing dependencies don't crash at module import
        try:
            from supabase import create_client
        except Exception as e:
            raise Exception("Supabase client not installed. Ensure 'supabase' is in requirements.")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return supabase


def create_user(username: str, email: str, password_hash: str) -> dict:
    """
    Create a new user in the database
    
    Args:
        username: User's username
        email: User's email
        password_hash: Hashed password
        
    Returns:
        Created user data
        
    Raises:
        Exception: If user creation fails
    """
    try:
        client = get_supabase_client()
        response = client.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": password_hash,
        }).execute()
        
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to create user: {str(e)}")


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user by email
    
    Args:
        email: User's email
        
    Returns:
        User data if found, None otherwise
    """
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Get user by ID
    
    Args:
        user_id: User's ID
        
    Returns:
        User data if found, None otherwise
    """
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching user by id: {str(e)}")
        return None


def save_chat_message(user_id: str, message: str, response: str) -> dict:
    """
    Save a chat message to the database
    
    Args:
        user_id: User's ID
        message: User's message
        response: Bot's response
        
    Returns:
        Saved chat entry data
        
    Raises:
        Exception: If save fails
    """
    try:
        client = get_supabase_client()
        response = client.table("chat_history").insert({
            "user_id": user_id,
            "message": message,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
        }).execute()
        
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to save chat message: {str(e)}")


def get_chat_history(user_id: str, limit: int = 50) -> List[dict]:
    """
    Get chat history for a user
    
    Args:
        user_id: User's ID
        limit: Maximum number of entries to return
        
    Returns:
        List of chat history entries
    """
    try:
        client = get_supabase_client()
        response = client.table("chat_history") \
            .select("message, response, timestamp") \
            .eq("user_id", user_id) \
            .order("timestamp", desc=False) \
            .limit(limit) \
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching chat history: {str(e)}")
        return []


def user_exists(username: str = None, email: str = None) -> bool:
    """
    Check if a user already exists
    
    Args:
        username: Username to check
        email: Email to check
        
    Returns:
        True if user exists, False otherwise
    """
    try:
        client = get_supabase_client()
        
        if email:
            response = client.table("users").select("id").eq("email", email).execute()
            if response.data:
                return True
        
        if username:
            response = client.table("users").select("id").eq("username", username).execute()
            if response.data:
                return True
        
        return False
    except Exception as e:
        print(f"Error checking user existence: {str(e)}")
        return False


def subscribe_to_newsletter(email: str) -> dict:
    """
    Subscribe an email to the newsletter
    
    Args:
        email: Email address to subscribe
        
    Returns:
        Subscription data
        
    Raises:
        Exception: If subscription fails
    """
    try:
        client = get_supabase_client()
        response = client.table("newsletter_subscribers").insert({
            "email": email,
            "subscribed_at": datetime.utcnow().isoformat(),
        }).execute()
        
        return response.data[0] if response.data else {}
    except Exception as e:
        raise Exception(f"Failed to subscribe to newsletter: {str(e)}")
