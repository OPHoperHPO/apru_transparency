# Agent Integration Documentation

## Overview

This document describes the integration of Google ADK agents with the APRU platform for document and website analysis.

## Architecture

The integration consists of several components:

### Backend Components

1. **Agent Tasks** (`backend/app/processing/tasks.py`)
   - Celery tasks that wrap agent functionality
   - `analyze_document_with_legal_llm`: Analyzes documents using the legal_llm agent
   - `analyze_website_with_browser_agent`: Analyzes websites using the dynamic_agent
   - **Note**: These tasks are registered with Celery via the standard `tasks.py` module for automatic discovery

2. **API Endpoints** (`backend/app/processing/views.py`)
   - `POST /api/v1/agents/analyze-document/`: Upload and analyze documents
   - `POST /api/v1/agents/analyze-website/`: Analyze website URLs

3. **Agents** (`backend/app/agents/`)
   - `legal_llm/`: Thai legal compliance analysis agent using Gemini
   - `dynamic_agent/`: Browser-based website analysis agent using Google ADK

### Frontend Components

1. **Agent Service** (`frontend/src/services/agents.ts`)
   - Client for calling agent analysis endpoints
   - Utilities for polling task status
   - Conversion helpers for agent results

2. **UI Components**
   - `CheckDocumentView.vue`: Document upload and analysis interface
   - `CheckWebsiteView.vue`: Website URL input and analysis interface
   - `LegalAnalysisDisplay.vue`: Display component for legal analysis results
   - `EvaluationDetailView.vue`: Enhanced to show agent results

## Data Flow

### Document Analysis Flow

1. User uploads document via `CheckDocumentView`
2. Frontend creates evaluation and calls `/api/v1/agents/analyze-document/`
3. Backend extracts text from PDF and creates a Task
4. Celery worker picks up task and runs `analyze_document_with_legal_llm`
5. Legal LLM agent analyzes document against 23 Thai legal criteria
6. Results stored in `Task.result_json` with structure:
   ```json
   {
     "contract_id": "...",
     "overall_compliance_score": 0.85,
     "summary": "Analysis summary...",
     "critical_issues": ["issue1", "issue2"],
     "recommendations": ["rec1", "rec2"],
     "criteria": {
       "criterion_name": {
         "status": "compliant|non_compliant|partially_compliant|unclear",
         "explanation": "...",
         "recommendations": "...",
         "confidence_score": 0.95
       }
     }
   }
   ```
7. Frontend polls task status and displays results in `EvaluationDetailView`

### Website Analysis Flow

1. User enters URL via `CheckWebsiteView`
2. Frontend creates evaluation and calls `/api/v1/agents/analyze-website/`
3. Backend creates a Task for the URL
4. Celery worker picks up task and runs `analyze_website_with_browser_agent`
5. Browser agent (when integrated) navigates site and analyzes dark patterns
6. Results stored in `Task.result_json`
7. Frontend displays results with real-time progress updates

## Integration with Existing System

### Task Model Integration

The agent tasks use the existing `Task` model from `app.processing`:

- `Task.url`: Stores the URL or document identifier
- `Task.project`: Links to the Project/Evaluation
- `Task.result_json`: Stores the complete agent analysis result
- `Task.status`: Tracks progress (QUEUED → IN_PROGRESS → DONE/FAILED)

### Project Model Integration

Agent results update the `Project` model:

- `Project.trust_score`: Set based on agent compliance/transparency score
- `Project.status`: Updated to UNDER_REVIEW when analysis completes

### Evaluation Display

The `EvaluationDetailView` has been enhanced with:

- Legal analysis tab that displays agent results via `LegalAnalysisDisplay` component
- Automatic loading of agent results from task when available
- Fallback to existing mock data if no agent results

## Agent Details

### Legal LLM Agent

**Purpose**: Analyze legal documents for Thai regulatory compliance

**Criteria Analyzed** (23 total):
- Consumer Protection (4 criteria)
- Legal Framework (6 criteria)
- Data Protection (2 criteria)
- Contract Structure (4 criteria)
- Regulatory Compliance (7 criteria)

**Output**: Structured JSON with status, explanation, recommendations for each criterion

**Model**: Uses Gemini 2.5 Pro with parallel analysis of criterion groups

### Dynamic Agent (Browser Agent)

**Purpose**: Analyze websites for dark patterns and transparency issues

**Capabilities**:
- Browser automation via MCP (Model Context Protocol) 
- Visual element analysis
- User journey simulation
- Pattern recognition

**Output**: Transparency score and detected dark patterns

**Status**: ✅ **Fully Integrated** - Now runs in Celery pipeline with MCP server support

**Integration**: The `analyze_website` function in `app.agents.dynamic_agent` creates a pipeline with:
- `ingest_agent`: Processes the URL and goal
- `browser_loop`: Iterative browser automation agent that:
  - Makes decisions about what to do next
  - Navigates and interacts with the page
  - Parses data from the page
  - Critiques progress
  - Returns results when complete

**Requirements**: MCP server URL must be configured in environment variable `BROWSER_MCP`

## Environment Configuration

### Required Environment Variables

Backend (`backend/.env`):
```bash
# Google AI
GOOGLE_API_KEY=your_gemini_api_key
LLM_MODEL_NAME=gemini-2.5-pro  # or gemini-2.0-flash

# Browser Agent (optional, for dynamic agent)
BROWSER_MCP=http://localhost:8080  # MCP server URL
BROWSER_LLM=gemini-2.5-pro
BROWSER_PIPELINE_ITERS=12
```

Frontend (`frontend/.env`):
```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## Testing

Run the agent integration tests:

```bash
cd backend
python manage.py test app.tests.test_agent_integration
```

Tests cover:
- Document analysis endpoint
- Website analysis endpoint
- Task creation and linking
- Agent task execution
- Error handling

## Deployment Considerations

1. **Dependencies**: Ensure `google-genai` and `google-adk` are installed
2. **API Keys**: Set `GOOGLE_API_KEY` in production environment
3. **Celery Workers**: Configure workers to handle long-running agent tasks
4. **Rate Limiting**: Consider rate limits for Gemini API calls
5. **MCP Server**: ✅ For browser agent, ensure MCP server is deployed and `BROWSER_MCP` env var is set

## Future Enhancements

1. **Batch Analysis**: Support analyzing multiple documents/websites at once
2. **Custom Criteria**: Allow users to define custom legal criteria
3. **Result Caching**: Cache agent results to avoid re-analysis
4. **Webhooks**: Add webhook support for task completion notifications
5. **Multi-language Support**: Extend legal analysis beyond Thai regulations

## Troubleshooting

### Document Analysis Not Working

- Check `GOOGLE_API_KEY` is set correctly
- Verify PDF extraction with `pip install PyPDF2`
- Check Celery worker logs for errors
- Ensure Task status is updating correctly

### Website Analysis Issues

- ✅ Browser agent is now integrated and runs via Celery
- Check `BROWSER_MCP` environment variable is set
- Verify MCP server is running and accessible at the configured URL
- Check Celery worker logs for agent execution errors

### Frontend Not Showing Results

- Check task polling in browser console
- Verify API endpoints are accessible
- Check task status is DONE
- Ensure `result_json` field is populated

## API Reference

### Analyze Document

**Endpoint**: `POST /api/v1/agents/analyze-document/`

**Request**:
```
Content-Type: multipart/form-data

file: (PDF file)
project_id: (optional UUID)
```

**Response**:
```json
{
  "id": "task-uuid",
  "status": "queued"
}
```

### Analyze Website

**Endpoint**: `POST /api/v1/agents/analyze-website/`

**Request**:
```json
{
  "url": "https://example.com",
  "project_id": "optional-uuid"
}
```

**Response**:
```json
{
  "id": "task-uuid",
  "status": "queued"
}
```

### Get Task Status

**Endpoint**: `GET /api/v1/tasks/{task_id}/status/`

**Response**:
```json
{
  "id": "task-uuid",
  "status": "done",
  "progress": 100,
  "created_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:05:00Z"
}
```

### Get Task Result

**Endpoint**: `GET /api/v1/tasks/{task_id}/result/`

**Response**:
```json
{
  "id": "task-uuid",
  "status": "done",
  "result_json": {
    "overall_compliance_score": 0.85,
    "summary": "...",
    "criteria": { ... }
  }
}
```
