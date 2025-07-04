# SCRAPPY 🕷️

**A Modern Web Scraping & Automated Outreach Platform**

SCRAPPY is a full-stack application that combines powerful web scraping capabilities with automated outreach tools. Built with FastAPI (backend) and Next.js (frontend), it enables users to scrape business data from Google Maps and automate personalized outreach via email and WhatsApp.

## 🚀 Features

### 🔍 Web Scraping
- **Google Maps Integration**: Extract comprehensive business information including:
  - Business names, addresses, phone numbers
  - Website URLs and email addresses
  - Reviews count and average ratings
  - Store features (pickup, delivery, shopping)
  - Opening hours and business types
- **Smart Deduplication**: Automatically removes duplicate entries
- **Rate Limiting**: Built-in protection against API limits
- **Background Processing**: Non-blocking scraping jobs

### 📧 Automated Outreach
- **Multi-Channel**: Support for Email and WhatsApp messaging
- **Personalized Templates**: Dynamic message templating with business data
- **Bulk Operations**: Send messages to multiple contacts efficiently
- **Status Tracking**: Monitor message delivery status

### 📊 Data Management
- **Multiple Import Formats**: CSV, Excel, JSON, Google Sheets
- **Export Options**: CSV, Excel, JSON formats
- **Real-time Updates**: Live job status and progress tracking
- **Data Validation**: Automatic contact information validation

### 🎨 Modern UI/UX
- **Interactive Text Effects**: Dynamic TextPressure components for headings
- **Clean Design**: Light theme with professional appearance
- **Responsive Layout**: Mobile-friendly interface
- **Real-time Dashboard**: Live updates and job monitoring

## 🏗️ Architecture

```
SCRAPPY/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── models.py       # Database models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── main.py         # FastAPI application
│   │   ├── config.py       # Configuration settings
│   │   ├── database.py     # Database connection
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities and helpers
│   ├── alembic/            # Database migrations
│   ├── logs/               # Application logs
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js Frontend
│   ├── app/                # App router pages
│   ├── components/         # Reusable UI components
│   ├── lib/                # Utilities and API clients
│   ├── hooks/              # Custom React hooks
│   └── public/             # Static assets
│
└── .gitignore             # Git ignore rules
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for Python
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Playwright**: Web scraping and automation
- **Pydantic**: Data validation using Python type hints
- **Asyncio**: Asynchronous programming support

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: High-quality UI components
- **React Hooks**: Modern React patterns

### DevOps & Tools
- **Git**: Version control
- **Docker**: Containerization (optional)
- **Poetry/pip**: Python dependency management
- **npm/pnpm**: Node.js package management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL database
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/HeshMedia/scrappy.git
cd scrappy
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies
npm install
# or
pnpm install

# Setup environment variables
cp .env.example .env.local
# Edit .env.local with your API endpoints

# Start the development server
npm run dev
# or
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## 📖 Usage Guide

### 1. Authentication
- Access the login page at `http://localhost:3000/login`
- Use your credentials to access the dashboard

### 2. Web Scraping
1. Navigate to **Search** in the dashboard
2. Enter your search query (e.g., "restaurants in New York")
3. Configure scraping parameters
4. Start the job and monitor progress
5. View results in real-time

### 3. Data Import
1. Go to **Import** section
2. Choose between CSV upload or Google Sheets
3. Configure import settings
4. Map data fields appropriately
5. Process the import

### 4. Automated Outreach
1. Select contacts from scraped or imported data
2. Choose outreach method (Email/WhatsApp)
3. Customize message templates
4. Send messages and track delivery

### 5. Export Data
- Export scraped data in multiple formats
- Include outreach status and analytics
- Schedule automated exports

## 🔧 Configuration

### Backend Configuration (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/scrappy_db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
WHATSAPP_API_KEY=your-whatsapp-api-key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Frontend Configuration (.env.local)
```env
# API Endpoints
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Search & Scraping
- `POST /api/search/` - Start a new search job
- `GET /api/search/{job_id}` - Get job status and results

#### Import/Export
- `POST /api/import/csv` - Import contacts from CSV
- `POST /api/import/google-sheets` - Import from Google Sheets
- `GET /api/export/{format}/{job_id}` - Export data

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/verify` - Token verification

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
# or
pnpm test
```

## 📝 Development

### Code Style
- **Backend**: Follow PEP 8 guidelines
- **Frontend**: Use Prettier and ESLint configurations
- **Commits**: Use conventional commit messages

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔒 Security

- Environment variables for sensitive data
- JWT token-based authentication
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection protection via ORM

## 📈 Performance

- Asynchronous processing for scraping jobs
- Database connection pooling
- Efficient pagination for large datasets
- Caching for frequently accessed data
- Optimized queries with proper indexing

## 🚀 Deployment

### Production Setup
1. Set up production database (PostgreSQL)
2. Configure environment variables
3. Build frontend: `npm run build`
4. Deploy backend with a WSGI server (Gunicorn)
5. Use a reverse proxy (Nginx)
6. Set up SSL certificates

### Docker Deployment (Optional)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL service is running
   - Verify connection string in .env

2. **Scraping Not Working**
   - Ensure Playwright is properly installed
   - Check rate limiting settings

3. **Frontend Build Errors**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility

### Logs
- Backend logs: `backend/logs/scrappy.log`
- Frontend logs: Browser developer console

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Next.js team for the React framework
- Shadcn for the beautiful UI components
- Playwright for reliable web automation

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Email: tushardhingra20@gmail.com
