import os
from google.adk.models import google_llm
from google.genai import Client
from google.genai.types import HttpOptions
class GeminiLLM(google_llm.Gemini):
    @property
    def api_client(self) -> Client:
        """Override to use the Google GenAI client."""
        return Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=HttpOptions(
                base_url=os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com"),
                api_version=os.getenv("GEMINI_API_VERSION", "v1beta1"),
            ),
        )
