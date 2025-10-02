# Agent Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Vue 3)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CheckDocumentView.vue          CheckWebsiteView.vue               │
│         │                               │                           │
│         │ Upload PDF                    │ Enter URL                 │
│         ▼                               ▼                           │
│  ┌──────────────────────────────────────────────┐                  │
│  │        Agent Service (agents.ts)             │                  │
│  │  - analyzeDocument()                         │                  │
│  │  - analyzeWebsite()                          │                  │
│  │  - pollTaskUntilComplete()                   │                  │
│  └──────────────────────────────────────────────┘                  │
│         │                               │                           │
│         └───────────────┬───────────────┘                           │
│                         │ HTTP API Calls                            │
└─────────────────────────┼─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Django + Celery)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  API Endpoints (views.py)                                          │
│  ┌───────────────────────────────────────────────────────┐         │
│  │ POST /api/v1/agents/analyze-document/                 │         │
│  │   - Extract text from PDF                             │         │
│  │   - Create Task                                       │         │
│  │   - Dispatch Celery task ──────────────┐             │         │
│  └───────────────────────────────────────┐ │             │         │
│  ┌───────────────────────────────────────┘ │             │         │
│  │ POST /api/v1/agents/analyze-website/    │             │         │
│  │   - Validate URL                        │             │         │
│  │   - Create Task                         │             │         │
│  │   - Dispatch Celery task ───────────────┼─────┐       │         │
│  └─────────────────────────────────────────┘     │       │         │
│                                                   │       │         │
│  Celery Tasks (agent_tasks.py)                   │       │         │
│  ┌───────────────────────────────────────────────┼───────┼─────┐   │
│  │ analyze_document_with_legal_llm()       ◄─────┘       │     │   │
│  │   - Call legal_llm agent                              │     │   │
│  │   - Store results in Task.result_json                 │     │   │
│  │   - Update Project.trust_score                        │     │   │
│  └───────────────────────────────────────────────────────┘     │   │
│  ┌────────────────────────────────────────────────────────────┼┐  │
│  │ analyze_website_with_browser_agent()             ◄─────────┘│  │
│  │   - Call browser agent (when available)                     │  │
│  │   - Store results in Task.result_json                       │  │
│  │   - Update Project.trust_score                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │                               │                           │
│         ▼                               ▼                           │
│  ┌────────────────────┐      ┌─────────────────────────┐          │
│  │  Models (models.py) │      │  Agents (app/agents/)  │          │
│  │  - Task             │      │  - legal_llm/          │          │
│  │  - Project          │      │  - dynamic_agent/      │          │
│  └────────────────────┘      └─────────────────────────┘          │
│                                         │                           │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────┐
                    │      External Services              │
                    │  - Google Gemini API (legal_llm)   │
                    │  - MCP Server (dynamic_agent)      │
                    └─────────────────────────────────────┘
```

## Data Flow: Document Analysis

```
User Action                Backend Processing                  Agent Execution
───────────                ──────────────────                  ───────────────

1. Upload PDF     ──────▶  Extract text with PyPDF2
   via UI                  Create Task (status=QUEUED)
                           Link to Project
                                    │
                                    ▼
2. Show progress  ◀────────  Celery worker picks task
   indicator                Set status=IN_PROGRESS
                                    │
                                    ▼
                           Call analyze_contract()  ────▶  3. Gemini Analysis
                           from legal_llm agent            - 23 legal criteria
                                                           - Parallel processing
                                                           - Thai law compliance
                                    │                              │
                                    ◀──────────────────────────────┘
                                    │
                           Store results in JSON:
                           {
                             compliance_score: 0.85,
                             criteria: {...},
                             issues: [...],
                             recommendations: [...]
                           }
                                    │
                                    ▼
4. Display        ◀────────  Set status=DONE
   results in                Update Project.trust_score
   Legal tab                 Return result_json
```

## Component Integration Map

### Frontend Components

```
src/
├── views/
│   ├── CheckDocumentView.vue          [Modified: Added agent integration]
│   ├── CheckWebsiteView.vue           [Modified: Added agent integration]
│   └── EvaluationDetailView.vue       [Modified: Display agent results]
│
├── components/
│   └── LegalAnalysisDisplay.vue       [NEW: Display legal analysis]
│
├── services/
│   ├── agents.ts                      [NEW: Agent API client]
│   ├── api.ts                         [Existing: Base API client]
│   └── projects.ts                    [Existing: Project service]
│
└── stores/
    └── projects.ts                    [Existing: State management]
```

### Backend Components

```
backend/app/
├── processing/
│   ├── agent_tasks.py                 [NEW: Celery tasks]
│   ├── views.py                       [Modified: Added agent endpoints]
│   ├── urls.py                        [Modified: Added routes]
│   └── models.py                      [Existing: Task model]
│
├── agents/
│   ├── legal_llm/                     [Existing: Legal agent]
│   │   ├── __init__.py
│   │   ├── analyzer.py                [Uses Gemini for analysis]
│   │   └── models.py                  [Analysis result schemas]
│   │
│   └── dynamic_agent/                 [Existing: Browser agent]
│       ├── __init__.py
│       ├── agent.py
│       └── agents/
│           ├── pipeline.py            [Agent orchestration]
│           └── browser_agent.py       [MCP browser automation]
│
└── projects/
    ├── models.py                      [Existing: Project model]
    └── views.py                       [Existing: Project API]
```

## Key Features Implemented

### 1. Document Analysis Pipeline

- **PDF Text Extraction**: Automatic text extraction from uploaded PDFs
- **Legal Compliance Check**: 23 Thai legal criteria analysis
- **Structured Output**: JSON results with status, explanation, confidence
- **Progress Tracking**: Real-time task status updates
- **Result Display**: Beautiful UI component showing all criteria

### 2. Website Analysis Pipeline

- **URL Validation**: Ensures valid URLs before processing
- **Task Management**: Async processing with status tracking
- **Placeholder Results**: Returns basic results until MCP server is ready
- **Progress Animation**: Visual feedback during analysis

### 3. Integration Points

- **Task Model**: Reuses existing task queue infrastructure
- **Project Model**: Links analysis results to projects
- **API Consistency**: Follows existing REST API patterns
- **UI Components**: Matches existing design system

### 4. Result Display

- **Legal Analysis Tab**: Shows detailed criterion-by-criterion analysis
- **Compliance Score**: Visual progress indicator
- **Critical Issues**: Highlighted violations
- **Recommendations**: Actionable advice
- **Confidence Scores**: AI confidence per criterion

## Agent Capabilities

### Legal LLM Agent

**Input**: Contract/document text  
**Processing**: Gemini 2.5 Pro analyzes 23 criteria in 5 groups  
**Output**: Structured compliance report

**Criteria Categories**:
1. Consumer Protection (4 criteria)
2. Legal Framework (6 criteria)
3. Data Protection (2 criteria)
4. Contract Structure (4 criteria)
5. Regulatory Compliance (7 criteria)

### Dynamic Browser Agent

**Input**: Website URL  
**Processing**: MCP-based browser automation (when available)  
**Output**: Dark pattern detection and transparency score

**Analysis Stages**:
1. Initial Scan (15%)
2. Visual Element Analysis (30%)
3. Legal Document Analysis (50%)
4. User Journey Simulation (70%)
5. Pattern Recognition (90%)
6. Report Generation (100%)

## Next Steps for Full Integration

1. **Deploy MCP Server**: Set up browser automation server for dynamic_agent
2. **Configure Environment**: Set GOOGLE_API_KEY and other variables
3. **Test Full Flow**: Run end-to-end document and website analysis
4. **Monitor Performance**: Track API usage and response times
5. **Iterate on Results**: Fine-tune prompts and criteria based on feedback
