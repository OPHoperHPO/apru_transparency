"""
Configuration module for Legal LLM
"""
import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
class Config:
    """Configuration settings for Legal LLM"""
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))
    TOP_P: float = float(os.getenv("TOP_P", "0.8"))
    TOP_K: int = int(os.getenv("TOP_K", "40"))
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.GEMINI_API_KEY:
            return False
        return True
    @classmethod
    def get_missing_config(cls) -> list[str]:
        """Get list of missing configuration items"""
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        return missing