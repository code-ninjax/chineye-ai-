"""
chatbot.py - Simple chatbot logic
"""


import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAnB3swqms4s2x-tB29Fy3xaoc2alABg2I")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = "My name is Chineye AI and I'm here to help."

def chatbot_response(user_message: str) -> str:
    """
    Generate a chatbot response using Gemini API
    """
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {"text": user_message}
                ]
            }
        ]
    }
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        # Gemini returns response in data['candidates'][0]['content']['parts'][0]['text']
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
        return "Sorry, I couldn't generate a response right now. Please try again later."
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Sorry, there was a problem connecting to the AI service. Please try again later."
