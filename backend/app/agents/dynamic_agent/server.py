import logging
import os
from pathlib import Path
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from app.agents.dynamic_agent.utils.tracing import LocalLoggingSpanExporter
from app.agents.dynamic_agent.utils.typing import Feedback
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("blog-writer")
allow_origins = (
    os.getenv("ALLOW_ORIGINS").split(",")
    if os.getenv("ALLOW_ORIGINS")
    else ["*"]
)
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "/tmp/blog-writer-artifacts"))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
provider = TracerProvider()
processor = export.BatchSpanProcessor(LocalLoggingSpanExporter(debug=False))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
session_service_uri = None  # без внешних хранилищ
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
)
app.title = "blog-writer"
app.description = "API for interacting with the Agent blog-writer"
@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    logger.info("feedback: %s", feedback.model_dump())
    return {"status": "success"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
