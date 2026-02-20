"""
Shared dependencies for API routes
"""
from groq import Groq
from config.settings import GROQ_API_KEY

# Initialize Groq client (shared across all routes)
groq_client = Groq(api_key=GROQ_API_KEY)


def get_groq_client():
    """Dependency injection for Groq client"""
    return groq_client