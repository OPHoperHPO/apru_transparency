"""Entry point for the dynamic Google ADK agent."""
from app.agents.dynamic_agent.agents.pipeline import root_agent as _root_agent
root_agent = _root_agent
__all__ = ["root_agent"]
