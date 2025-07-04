# Scrappy - Web Scraper & Outreach Tool

A powerful FastAPI-based application for web scraping and automated outreach via WhatsApp and Email.

## Features

- **Web Scraping**: Extract business information from Google and other sources
- **Automated Outreach**: Send personalized WhatsApp and Email messages
- **Data Import/Export**: Support for CSV, Excel, JSON, and Google Sheets
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Background Processing**: Asynchronous job processing
- **Contact Management**: Validate and manage contact information

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Setup Database

```bash
# Initialize Alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Search & Scraping
- `POST /api/search/` - Start a new search job
- `GET /api/export/jobs/{job_id}/status` - Get job status

### Import/Export
- `POST /api/import/import/csv` - Import contacts from CSV
- `POST /api/import/import/google-sheets` - Import from Google Sheets
- `POST /api/import/bulk-message` - Send bulk messages
- `POST /api/export/csv/{job_id}` - Export results as CSV
- `POST /api/export/excel/{job_id}` - Export results as Excel
- `POST /api/export/json/{job_id}` - Export results as JSON

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | For WhatsApp |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | For WhatsApp |
| `TWILIO_WHATSAPP_NUMBER` | Your Twilio WhatsApp number | For WhatsApp |
| `SMTP_SERVER` | SMTP server hostname | For Email |
| `SMTP_PORT` | SMTP server port | For Email |
| `SMTP_USERNAME` | SMTP username | For Email |
| `SMTP_PASSWORD` | SMTP password | For Email |
| `SMTP_FROM_EMAIL` | From email address | For Email |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | For Sheets |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | For Sheets |
| `SELENIUM_REMOTE_URL` | Selenium Grid URL | Optional |

### Database Setup

1. Install PostgreSQL
2. Create a database
3. Update `DATABASE_URL` in `.env`
4. Run migrations: `alembic upgrade head`

### Google Sheets Integration

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create OAuth 2.0 credentials
4. Add credentials to `.env`

### Twilio WhatsApp Setup

1. Create a Twilio account
2. Set up WhatsApp Business API
3. Get your credentials from Twilio Console
4. Add credentials to `.env`

## Usage Examples

### 1. Search for Businesses

```python
import httpx

response = httpx.post("http://localhost:8000/api/search/", json={
    "query": "restaurants in New York",
    "limit": 10,
    "mode": "scrape_and_contact",
    "message_type": "both",
    "prewritten_message": "Hi {name}, we'd love to help your business grow!"
})

print(response.json())
```

### 2. Import from CSV

```python
import httpx

with open("contacts.csv", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/import/import/csv",
        files={"file": f}
    )

print(response.json())
```

### 3. Export Results

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/export/excel/1",
    params={"include_messages": True}
)

with open("results.xlsx", "wb") as f:
    f.write(response.content)
```

## Rate Limits

The application includes built-in rate limiting:

- **SMTP**: 10 emails per minute, 100 per hour
- **WhatsApp**: 60 messages per minute, 1000 per day
- **Web Scraping**: 30 requests per minute
- **Google Sheets**: 100 requests per 100 seconds

## Project Structure

```
heshscrap/
├── app/
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── utils/          # Utilities
│   ├── models.py       # Database models
│   ├── schemas.py      # Pydantic schemas
│   ├── database.py     # Database setup
│   ├── config.py       # Configuration
│   └── main.py         # FastAPI app
├── alembic/            # Database migrations
├── requirements.txt    # Dependencies
└── .env.example       # Environment template
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

### Creating Migrations

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Docker Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/scraper_db
    depends_on:
      - db
      - selenium

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: scraper_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  selenium:
    image: selenium/standalone-chrome:latest
    ports:
      - "4444:4444"

volumes:
  postgres_data:
```

### Build and Run

```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support or questions, please open an issue on GitHub.
