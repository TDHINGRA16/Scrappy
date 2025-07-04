# HeshScrap Frontend

A modern Next.js frontend for the HeshScrap web scraping and automated outreach tool.

## Technology Stack

- **Frontend Framework**: Next.js 15.2.4 with React 19
- **Styling**: Tailwind CSS with custom components
- **UI Components**: Radix UI primitives
- **Type Safety**: TypeScript
- **Backend Integration**: RESTful API powered by Selenium web scraping

## Features

- **Google Maps Scraping**: Selenium-powered scraping for business information
- **Automated Outreach**: Email and WhatsApp messaging capabilities
- **Job Management**: Track and monitor scraping jobs
- **Real-time Updates**: Live status updates for ongoing jobs
- **Export Functionality**: Download results in various formats

## Backend Technology

The backend has been updated to use **Selenium WebDriver** instead of Playwright for enhanced reliability and better Google Maps compatibility.

## Getting Started

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Start the development server:
   ```bash
   pnpm dev
   ```

3. Build for production:
   ```bash
   pnpm build
   ```

## API Integration

The frontend communicates with a FastAPI backend that uses Selenium for web scraping. All scraping operations are handled server-side for better performance and reliability.
