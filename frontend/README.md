# APRU Frontend

A modern Vue 3 frontend application for the APRU Tech Policy Hackathon fintech platform with Stripe-inspired design.

## 🚀 Features

- **Modern Vue 3** with Composition API and TypeScript
- **Vuetify 3** for Material Design components
- **Tailwind CSS** for utility-first styling
- **Stripe-inspired design** with rounded corners and clean aesthetics
- **Light theme** with professional color scheme
- **Smooth animations** using @vueuse/motion
- **Responsive design** for all screen sizes
- **Authentication system** with JWT integration
- **Project management** dashboard
- **Task processing** interface
- **Regulatory compliance** monitoring

## 🛠️ Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type safety and better DX
- **Vite** - Fast build tool and dev server
- **Vuetify 3** - Material Design component framework
- **Tailwind CSS** - Utility-first CSS framework
- **Pinia** - Vue store for state management
- **Vue Router** - Official router for Vue.js
- **Axios** - HTTP client for API calls
- **@vueuse/motion** - Animation library

## 🎨 Design Features

- **Gradient backgrounds** with modern color schemes
- **Glassmorphism effects** for cards and components
- **Rounded corners** (xl, 2xl, 3xl border radius)
- **Hover animations** with subtle transforms
- **Smooth transitions** for all interactions
- **Professional typography** with proper spacing
- **Status indicators** with color-coded badges
- **Progress bars** and loading states
- **Clean navigation** with icons and active states

## 📱 Pages & Components

### 🔐 Authentication
- **Login page** with demo credentials
- **JWT token management** with auto-refresh
- **Route guards** for protected pages

### 📊 Dashboard
- **Overview cards** with key metrics
- **Project status** distribution
- **Recent projects** listing
- **Quick actions** buttons
- **Animated counters** and progress indicators

### 📁 Projects
- **Grid layout** with project cards
- **Status badges** (draft, submitted, under review, approved, rejected)
- **Trust score** indicators
- **CRUD operations** with dialogs
- **Search and filtering** capabilities

### ⚡ Tasks
- **Task submission** form
- **Progress tracking** with bars
- **Status monitoring** (new, queued, in progress, done, failed)
- **Priority levels** (low, normal, high)
- **Result download** functionality

### 🛡️ Regulator Dashboard
- **System performance** metrics
- **Compliance status** monitoring
- **Activity timeline** with icons
- **Alert management** system
- **Health indicators** and uptime tracking

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 🐳 Docker

The frontend includes Docker support:

```bash
# Build Docker image
docker build -t apru-frontend .

# Run with Docker Compose
docker-compose up frontend
```

## 🔧 Development

### Demo Mode
The application includes demo mode with mock data for development:

- **Demo credentials**: admin / admin123
- **Mock projects** with different statuses
- **Simulated tasks** with progress tracking
- **Sample compliance** metrics

### Code Structure
```
src/
├── components/        # Reusable Vue components
├── views/            # Page components
├── router/           # Vue Router configuration
├── stores/           # Pinia state management
├── services/         # API service layer
├── plugins/          # Vue plugins (Vuetify)
└── assets/           # Static assets and styles
```

### Key Features Implementation

- **Vuetify Integration**: Custom theme with Stripe-inspired colors
- **Tailwind CSS**: Utility classes for rapid styling
- **Animation System**: Page transitions and hover effects
- **API Layer**: Axios with interceptors for auth
- **State Management**: Pinia stores for projects and auth
- **Type Safety**: Full TypeScript implementation

## 🎯 Design Principles

- **Consistency**: Unified spacing, colors, and typography
- **Accessibility**: Proper contrast ratios and ARIA labels
- **Performance**: Optimized bundle size and lazy loading
- **Responsiveness**: Mobile-first approach with breakpoints
- **User Experience**: Intuitive navigation and feedback

## 📦 Build & Deploy

The application builds to a static site that can be deployed to any web server:

```bash
npm run build
# Outputs to dist/ directory
```

Includes Nginx configuration for Docker deployment with:
- Gzip compression
- Static asset caching
- Client-side routing support
- Security headers

## 🤝 Contributing

This project was created for the APRU Tech Policy Hackathon 2025 focusing on "Leveraging AI and Data for Inclusive Growth".

---

Built with ❤️ for APRU Tech Policy Hackathon 2025