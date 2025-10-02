# Backend Integration Documentation

## Overview

The frontend has been successfully connected to the Django REST API backend. The integration provides:

- **Authentication**: JWT-based authentication using Django Simple JWT
- **Project Management**: CRUD operations for transparency projects  
- **Task Processing**: Asynchronous dark pattern analysis tasks
- **Real-time Updates**: Polling mechanism for task status updates

## API Endpoints

### Authentication
- `POST /api/token/` - Login and get JWT tokens
- `POST /api/token/refresh/` - Refresh access token

### Projects API (`/api/v1/projects/`)
- `GET /api/v1/projects/` - List all projects
- `POST /api/v1/projects/` - Create new project (owner role required)
- `GET /api/v1/projects/{id}/` - Get project details
- `PATCH /api/v1/projects/{id}/` - Update project
- `DELETE /api/v1/projects/{id}/` - Delete project
- `POST /api/v1/projects/{id}/complaints/` - Submit complaint
- `GET /api/v1/projects/{id}/complaints/` - List complaints (admin/regulator only)

### Tasks API (`/api/v1/tasks/`)
- `POST /api/v1/tasks/submit/` - Submit URL for analysis
- `GET /api/v1/tasks/{id}/status/` - Get task status
- `GET /api/v1/tasks/{id}/result/` - Get task results

### Regulator Stats
- `GET /api/v1/regulator/stats/` - Basic statistics
- `GET /api/v1/regulator/stats/expanded/` - Extended statistics
- `GET /api/v1/regulator/stats/latency/` - Performance metrics

## Data Flow

1. **Website Analysis**:
   - User submits URL through frontend form
   - Frontend creates Project via `/api/v1/projects/`
   - If URL provided, submits Task via `/api/v1/tasks/submit/`
   - Frontend polls task status every 2 seconds
   - When complete, displays results mapped to evaluation format

2. **Authentication Flow**:
   - User logs in via `/api/token/`
   - JWT tokens stored in localStorage
   - Automatic token refresh on 401 responses
   - Role-based access control (individual, owner, regulator, admin)

## Frontend Services

### `services/api.ts`
- Axios client with JWT interceptors
- Automatic token refresh
- Base URL: `http://localhost:8000/api`

### `services/projects.ts`
- Maps backend Project model to frontend DarkPatternEvaluation
- Handles task submission and polling
- Generates mock dark patterns based on trust score

### `services/auth.ts`
- JWT token management
- User role determination from demo credentials
- Token expiration checking

### `services/tasks.ts`
- Direct task API integration
- Status polling capabilities
- Result retrieval

## Store Integration (`stores/projects.ts`)

- Manages evaluation state and caching
- Real-time task status polling
- Compatibility layer for existing views
- Error handling and loading states

## Environment Configuration

Frontend environment (`.env`):
```
VITE_API_BASE_URL=http://localhost:8000/api
```

Backend environment (`.env.example`):
- Django, PostgreSQL, Redis, MinIO configuration
- Demo user credentials
- JWT token lifetimes

## Demo Users

Based on backend setup:
- `admin` / `admin123` - Admin role
- `reg` / `reg123` - Regulator role  
- `owner` / `owner123` - Business owner role
- `user` / `user123` - Individual user role

## Running the System

1. **Backend**:
   ```bash
   docker-compose up -d db redis minio
   cd backend && python manage.py runserver
   ```

2. **Frontend**:
   ```bash
   cd frontend && npm run dev
   ```

3. **Access**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api
   - Admin: http://localhost:8000/admin

## Key Features Implemented

✅ **Real API Integration**: All mock data removed, using actual backend  
✅ **JWT Authentication**: Token-based auth with refresh  
✅ **Task Polling**: Real-time updates during analysis  
✅ **Role-based Access**: Different features per user type  
✅ **Error Handling**: Comprehensive error management  
✅ **Backward Compatibility**: Existing views still work  

## Future Enhancements

- Add user profile management endpoint
- Implement WebSocket for real-time updates
- Add file upload support for documents
- Enhance task result processing
- Add more detailed error handling