# APRU - Fintech Platform for Tech Policy Hackathon 2025

**APRU** is a comprehensive fintech platform built for the APRU Tech Policy Hackathon 2025, focusing on "Leveraging AI and Data for Inclusive Growth". The platform features a Django backend with a modern Vue 3 frontend that implements Stripe-inspired design principles.

## 🏗️ Architecture

- **Backend**: Django with PostgreSQL, Redis, and MinIO
- **Frontend**: Vue 3 + TypeScript + Vuetify + Tailwind CSS
- **Containerization**: Docker and Docker Compose
- **Design**: Modern Stripe-inspired UI with light theme

## 🚀 Key Features

### Backend Services
- **Project Management**: CRUD operations for fintech projects with status tracking
- **Task Processing**: Asynchronous task queue with Celery workers
- **User Authentication**: JWT-based authentication system
- **File Storage**: S3-compatible storage with MinIO
- **API Documentation**: OpenAPI/Swagger integration

### Frontend Application
- **Modern UI/UX**: Stripe-inspired design with rounded corners and clean aesthetics
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Interactive Dashboard**: Real-time project metrics and analytics
- **Authentication Flow**: Secure login with JWT token management
- **Project Management**: Visual project cards with status indicators
- **Task Monitoring**: Real-time task progress tracking
- **Regulatory Dashboard**: Compliance metrics and system monitoring

## 🖼️ Screenshots

### Login Page
![Login](https://github.com/user-attachments/assets/152d8256-8584-47cd-a35f-8c7dd9898eaf)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/a8e859aa-0212-4b06-962f-dd56f08f0393)

### Projects Management
![Projects](https://github.com/user-attachments/assets/2fed22ae-0f00-4d34-8acb-49ddff66e657)

### Tasks Interface
![Tasks](https://github.com/user-attachments/assets/08841c84-2420-419c-9ba2-868293a1c7da)

### Regulator Dashboard
![Regulator](https://github.com/user-attachments/assets/c7e3ede6-264b-49b4-9bb0-a8a86922abbc)

## 🛠️ Technology Stack

### Backend
- **Django 5.0+** - Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and message broker
- **Celery** - Distributed task queue
- **MinIO** - S3-compatible object storage
- **Django REST Framework** - API development

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type safety and better DX
- **Vuetify 3** - Material Design components
- **Tailwind CSS** - Utility-first CSS framework
- **Pinia** - State management
- **Vite** - Build tool and dev server
- **@vueuse/motion** - Animation library

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Web server and reverse proxy
- **GitHub Actions** - CI/CD pipeline

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/OPHoperHPO/APRU_frontend.git
cd APRU_frontend
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the services**
```bash
docker-compose up -d
```

4. **Frontend Development** (Optional)
```bash
cd frontend
npm install
npm run dev
```

### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs/
- **MinIO Console**: http://localhost:9001

### Demo Credentials
- **Admin**: admin / admin123
- **User**: user / user123

## 🎨 Design Philosophy

The frontend implements a **Stripe-inspired design** with:

- **Light Theme**: Clean, professional appearance
- **Rounded Corners**: Modern aesthetic with consistent border radius
- **Gradient Backgrounds**: Subtle gradients for visual depth
- **Smooth Animations**: Micro-interactions and page transitions
- **Card-based Layout**: Information organized in clean cards
- **Color-coded Status**: Visual indicators for different states
- **Responsive Design**: Optimized for all screen sizes

## 📊 Project Structure

```
APRU_frontend/
├── backend/                 # Django backend
│   ├── app/                 # Main Django application
│   ├── Dockerfile           # Backend container
│   └── requirements.txt     # Python dependencies
├── frontend/                # Vue.js frontend
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   ├── Dockerfile           # Frontend container
│   └── package.json         # Node.js dependencies
├── docker-compose.yml       # Multi-service orchestration
├── .env.example            # Environment configuration template
└── README.md               # This file
```

## 🔧 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Build Production
```bash
# Backend
docker build -t apru-backend ./backend

# Frontend
docker build -t apru-frontend ./frontend

# Full stack
docker-compose build
```

## 📈 Features Implemented

### ✅ Completed
- [x] Vue 3 + TypeScript setup
- [x] Vuetify 3 integration with custom theme
- [x] Tailwind CSS configuration
- [x] Stripe-inspired light theme design
- [x] Rounded modern UI components
- [x] Smooth animations and transitions
- [x] Authentication system with JWT
- [x] Project management interface
- [x] Task processing dashboard
- [x] Regulator compliance monitoring
- [x] Responsive design for all screens
- [x] Docker containerization
- [x] Production build optimization

### 🎯 Key Achievements
- **Modern Stack**: Latest Vue 3 with Composition API
- **Design Excellence**: Stripe-inspired UI/UX
- **Performance**: Optimized bundle size and loading
- **Type Safety**: Full TypeScript implementation
- **Scalability**: Docker-ready for production
- **User Experience**: Intuitive navigation and feedback

## 🤝 Contributing

This project was developed for the APRU Tech Policy Hackathon 2025. The team focused on creating a production-ready fintech platform that demonstrates modern web development practices and inclusive design principles.

### Team: Transparency
- Modern full-stack development
- Focus on inclusive financial technology
- Emphasis on regulatory compliance
- User-centric design approach

## 📄 License

This project was created for the APRU Tech Policy Hackathon 2025 focusing on "Leveraging AI and Data for Inclusive Growth".

# AI Use

## Which AI tools were used
- Google Gemini 2.5 Pro

## What AI tools were used for

### Writing Support
We used an LLM to more accurately translate the text into English.

### Visuals
We used AI-generated images for the presentation.


---

Built with ❤️ for APRU Tech Policy Hackathon 2025
