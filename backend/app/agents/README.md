# Agent Integrations

This package bundles external agent implementations that power APRU's AI-driven features.

## Dynamic ADK Agent

The code under `dynamic_agent/` is sourced from the APRU dynamic agent project. It keeps the original FastAPI wrapper and
Gemini configuration so the agent can still be run as a standalone ADK service if needed.

## Legal LLM Agent

The `legal_llm/` package comes from the APRU legal analysis project and exposes the `analyze_contract` helper for structured
Gemini responses that match Thai legal compliance requirements.

Both integrations are vendored so they can be imported directly from the Django backend without separate repositories.
