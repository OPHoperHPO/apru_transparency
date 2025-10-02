from __future__ import annotations
import os
from app.utils.llmproxy import GeminiLLM
from app.agents.roach_motel_agent import roach_motel_root_agent
model_name = os.getenv("LLM_MODEL_NAME") or "gemini-2.0-flash"
LLM = GeminiLLM(model=model_name)
root_agent =roach_motel_root_agent
