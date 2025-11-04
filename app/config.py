# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App settings
    app_name: str = "LLM Code Deployment"
    debug: bool = False
    secret_token: str
    
    # LLM API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # API Base URLs
    openrouter_url: str = "https://openrouter.ai/api/v1"
    anthropic_url: Optional[str] = None
    openai_url: Optional[str] = None
    gemini_url: Optional[str] = None
    
    # GitHub settings
    github_token: str
    github_username: str
    
    # Model preferences
    model_preferences: List[str] = [
        "anthropic/claude-opus-4.1",
        "claude-opus-4-1",
        "gpt-5",
        "google/gemini-2.5-pro",
        "gemini-2.5-pro"
    ]
    
    # Provider preferences
    provider_preferences: List[str] = [
        "openrouter",
        "anthropic",
        "openai",
        "gemini"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()