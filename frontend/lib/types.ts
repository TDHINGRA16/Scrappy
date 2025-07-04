// API Types for the scraping application
// Backend now uses Selenium instead of Playwright for enhanced reliability

export interface SearchRequest {
  query: string
  limit?: number
  source: "google_maps"
  mode: "scrape_only" | "scrape_and_contact"
  message_type?: "whatsapp" | "email" | "both" | null
  prewritten_message?: string | null
}

export interface SearchJobResponse {
  job_id: number
  status: string
}

export interface ScrapeResultResponse {
  id: number
  name: string
  website?: string | null
  email?: string | null
  phone?: string | null
  address?: string | null
  source: string
  // Enhanced fields from the new scraper
  reviews_count?: number | null
  reviews_average?: number | null
  store_shopping?: string | null
  in_store_pickup?: string | null
  store_delivery?: string | null
  place_type?: string | null
  opening_hours?: string | null
  introduction?: string | null
}

export interface SearchJobDetail {
  id: number
  query: string
  limit?: number | null
  source: string
  mode: string
  message_type?: string | null
  prewritten_message?: string | null
  created_at: string
  status: string
  results: ScrapeResultResponse[]
}

export interface OutreachMessageResponse {
  id: number
  job_id: number
  contact_method: string
  recipient: string
  message: string
  status: string
  sent_at?: string | null
  error?: string | null
}

export interface GoogleSheetImportRequest {
  sheet_id: string
  range?: string
  message_template?: string | null
}

export interface CSVImportResponse {
  job_id: number
  count: number
  status: string
}

export interface ExportRequest {
  job_id: number
  format: "csv" | "excel" | "json"
  include_messages?: boolean
}

export interface BulkMessageRequest {
  contacts: Array<{
    email?: string
    phone?: string
    name?: string
  }>
  message_template: string
  contact_method: "email" | "whatsapp" | "both"
  subject?: string
}

export interface ContactValidationRequest {
  emails?: string[]
  phones?: string[]
}

export interface ContactValidationResponse {
  valid_emails: string[]
  invalid_emails: string[]
  valid_phones: string[]
  invalid_phones: string[]
}

export interface UserLogin {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface User {
  email: string
  is_active: boolean
}

export interface UserResponse {
  email: string
  message: string
}

// API Error Response
export interface ApiError {
  detail: string
}
