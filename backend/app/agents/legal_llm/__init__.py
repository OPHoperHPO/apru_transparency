"""
Legal LLM Agent using Google Gemini for contract analysis
"""
from .models import LegalAnalysisResult
from .analyzer import analyze_contract
__all__ = ["LegalAnalysisResult", "analyze_contract"]