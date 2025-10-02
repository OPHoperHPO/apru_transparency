# Agent Integration Quick Start Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis
- Google Gemini API Key

## Setup Steps

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r app/requirements.txt

# Set up environment variables
cat > .env << EOF
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/apru_db

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google AI - REQUIRED FOR AGENTS
GOOGLE_API_KEY=your-gemini-api-key-here
LLM_MODEL_NAME=gemini-2.5-pro

# Browser Agent (optional)
BROWSER_MCP=http://localhost:8080
BROWSER_LLM=gemini-2.5-pro
EOF

# Run migrations
python manage.py migrate

# Create demo users
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
User.objects.create_user('user', 'user@example.com', 'user123', role='individual')
EOF

# Start Django server
python manage.py runserver
```

### 2. Start Celery Worker (separate terminal)

```bash
cd backend

# Start Celery worker
celery -A app worker -l info
```

### 3. Frontend Setup (separate terminal)

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api
EOF

# Start dev server
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

## Testing Document Analysis

### Via UI

1. Open http://localhost:5173
2. Login with `user` / `user123`
3. Click "Check Document" in the navigation
4. Enter evaluation name: "Test Legal Analysis"
5. Upload a PDF document (e.g., a sample contract)
6. Click "Analyze Document"
7. Watch the progress indicator
8. You'll be redirected to the results page
9. Click the "Legal Analysis (Level 2)" tab
10. View the detailed legal compliance analysis

### Via API

```bash
# 1. Upload and analyze a document
curl -X POST http://localhost:8000/api/v1/agents/analyze-document/ \
  -F "file=@sample_contract.pdf" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response:
# {
#   "id": "task-uuid-here",
#   "status": "queued"
# }

# 2. Check task status
curl http://localhost:8000/api/v1/tasks/{task-uuid}/status/

# 3. Get results when done
curl http://localhost:8000/api/v1/tasks/{task-uuid}/result/

# Response will include:
# {
#   "result_json": {
#     "overall_compliance_score": 0.85,
#     "summary": "Analysis found...",
#     "critical_issues": [...],
#     "criteria": {
#       "unilateral_changes": {
#         "status": "compliant",
#         "explanation": "...",
#         "confidence_score": 0.95
#       },
#       ...
#     }
#   }
# }
```

## Testing Website Analysis

### Via UI

1. Open http://localhost:5173
2. Login with `user` / `user123`
3. Click "Check Website" in the navigation
4. Enter evaluation name: "Test Website Analysis"
5. Enter URL: "https://example.com"
6. Click "Analyze Website"
7. Watch the animated progress through analysis stages
8. View results page with transparency score

**Note**: Website analysis currently returns placeholder results until the MCP server is fully configured.

### Via API

```bash
# Analyze a website
curl -X POST http://localhost:8000/api/v1/agents/analyze-website/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "url": "https://example.com"
  }'

# Response:
# {
#   "id": "task-uuid-here",
#   "status": "queued"
# }

# Check status and get results
curl http://localhost:8000/api/v1/tasks/{task-uuid}/result/
```

## Running Tests

```bash
cd backend

# Run all tests
python manage.py test

# Run only agent integration tests
python manage.py test app.tests.test_agent_integration

# Run with verbose output
python manage.py test app.tests.test_agent_integration --verbosity=2
```

Expected output:
```
Creating test database...
test_analyze_document_endpoint ... ok
test_analyze_website_endpoint ... ok
test_document_analysis_task_success ... ok
test_website_analysis_task ... ok
...
----------------------------------------------------------------------
Ran 8 tests in 2.345s

OK
```

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"

**Solution**: Make sure you've set the environment variable:
```bash
export GOOGLE_API_KEY=your-key-here
# Or add it to backend/.env
```

### Issue: Celery tasks not running

**Solution**: 
1. Check if Celery worker is running: `ps aux | grep celery`
2. Check Redis is running: `redis-cli ping` (should return "PONG")
3. Restart Celery worker with `celery -A app worker -l info`

### Issue: PDF text extraction fails

**Solution**:
```bash
# Reinstall PyPDF2
pip uninstall PyPDF2
pip install PyPDF2
```

### Issue: Frontend not connecting to backend

**Solution**:
1. Check `VITE_API_BASE_URL` in `frontend/.env`
2. Ensure Django is running on port 8000
3. Check CORS settings in Django allow localhost:5173

### Issue: Task status shows "failed"

**Solution**:
1. Check Celery worker logs for error messages
2. Verify GOOGLE_API_KEY is valid
3. Check Task.error field in database:
   ```python
   python manage.py shell
   >>> from app.processing.models import Task
   >>> task = Task.objects.get(id='task-uuid')
   >>> print(task.error)
   ```

## Sample Test Document

Create a simple test contract PDF:

```python
# generate_test_contract.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_contract():
    c = canvas.Canvas("test_contract.pdf", pagesize=letter)
    c.drawString(100, 750, "SERVICE AGREEMENT")
    c.drawString(100, 700, "")
    c.drawString(100, 670, "This agreement is between the Service Provider and the Client.")
    c.drawString(100, 650, "")
    c.drawString(100, 620, "1. The provider may change terms at any time without notice.")
    c.drawString(100, 600, "2. All fees are non-refundable.")
    c.drawString(100, 580, "3. Client data may be shared with third parties.")
    c.drawString(100, 560, "4. Provider assumes no liability for service disruptions.")
    c.save()

create_test_contract()
```

Run: `python generate_test_contract.py`

This creates a contract with several compliance issues that the legal agent will detect.

## Verifying Integration

### Checklist

- [ ] Backend server running on http://localhost:8000
- [ ] Celery worker running and connected to Redis
- [ ] Frontend running on http://localhost:5173
- [ ] GOOGLE_API_KEY environment variable set
- [ ] Can login to the application
- [ ] Can upload a PDF document
- [ ] Task is created and processed by Celery
- [ ] Legal analysis results appear in the UI
- [ ] Can analyze a website URL
- [ ] Results display in the evaluation detail view

### Success Indicators

✅ **Document Analysis Working**:
- PDF uploads successfully
- Task status changes: queued → in_progress → done
- `result_json` contains compliance data
- Legal Analysis tab shows criteria with statuses
- Trust score is calculated and displayed

✅ **Website Analysis Working**:
- URL validation works
- Task is created
- Analysis dialog shows progress
- Results page displays (even if placeholder)
- No errors in browser console

## Next Steps

1. **Generate More Test Data**: Create various test contracts and websites
2. **Fine-tune Prompts**: Adjust agent prompts in `legal_llm/analyzer.py`
3. **Configure MCP Server**: Set up browser agent for full website analysis
4. **Monitor Performance**: Track API response times and success rates
5. **Customize UI**: Adjust the display of results to match your needs

## Support

For issues or questions:
1. Check `AGENT_INTEGRATION.md` for detailed documentation
2. Review `AGENT_ARCHITECTURE.md` for system design
3. Check Django logs: `python manage.py runserver --verbosity=2`
4. Check Celery logs in the worker terminal
5. Inspect browser console for frontend errors

## Example Complete Flow

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python manage.py runserver

# Terminal 2: Celery
cd backend
source venv/bin/activate
celery -A app worker -l info

# Terminal 3: Frontend
cd frontend
npm run dev

# Terminal 4: Test
curl -X POST http://localhost:8000/api/v1/agents/analyze-document/ \
  -F "file=@test_contract.pdf"

# Watch Celery terminal for task execution
# Check result:
curl http://localhost:8000/api/v1/tasks/{task-id}/result/
```

The integration is complete and ready for testing! 🎉
