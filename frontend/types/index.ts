// ========================================
// Types for Scrappy v2.0 Frontend
// ========================================

// Scraping Types
export interface ScrapeRequest {
  search_query: string;
  location?: string;
  target_count?: number;
  headless?: boolean;
}

export interface Lead {
  place_id: string;
  cid: string;
  name: string;
  phone: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  rating: number | null;
  reviews_count: number | null;
  category: string | null;
  google_maps_url: string;
  href?: string;
  latitude: number | null;
  longitude: number | null;
  opening_hours: string[] | null;
  scraped_at: string;
}

export interface ScrapeResponse {
  success: boolean;
  query: string;
  location: string;
  requested_count: number;
  scraped_count: number;
  unique_count: number;
  duplicates_removed: number;
  leads: Lead[];
  scrape_time_seconds: number;
  timestamp: string;
}

export interface ScrapeProgress {
  status: "idle" | "scrolling" | "extracting" | "processing" | "complete" | "error";
  currentCount: number;
  targetCount: number;
  message: string;
}

// Google Sheets Types
export interface SaveToSheetsRequest {
  leads: Lead[];
  spreadsheet_id?: string;
  sheet_name?: string;
}

export interface SaveToSheetsResponse {
  success: boolean;
  spreadsheet_id: string;
  spreadsheet_url: string;
  rows_added: number;
  message: string;
}

// SMS Outreach Types
export interface SMSOutreachRequest {
  leads: Lead[];
  message_template: string;
  provider?: "twilio" | "fast2sms";
}

export interface SMSOutreachResponse {
  success: boolean;
  total_leads: number;
  messages_sent: number;
  messages_failed: number;
  results: {
    phone: string;
    status: "sent" | "failed";
    error?: string;
  }[];
}

// User/Auth Types
export interface User {
  id: string;
  email: string;
  name: string;
  image?: string;
  emailVerified: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface Session {
  user: User;
  expires: Date;
}

// Google Sheets Integration Types
export interface GoogleIntegrationStatus {
  connected: boolean;
  email?: string;
  created_at?: string;
  updated_at?: string;
}

export interface GoogleAuthURLResponse {
  authorization_url: string;
  state: string;
}

export interface GoogleCallbackRequest {
  code: string;
  state: string;
}

export interface GoogleCallbackResponse {
  success: boolean;
  message: string;
  email?: string;
}

export interface SaveToGoogleSheetsRequest {
  spreadsheet_id?: string;
  sheet_name?: string;
  data: (string | number | null)[][];
}

export interface SaveToGoogleSheetsResponse {
  success: boolean;
  spreadsheet_id: string;
  spreadsheet_url: string;
  rows_added: number;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// UI State Types
export interface ScrapingState {
  isLoading: boolean;
  progress: ScrapeProgress;
  results: Lead[] | null;
  error: string | null;
}

// Form Types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface SignupFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface ScrapingFormData {
  search_query: string;
  location: string;
  target_count: number;
}

// Component Props Types
export interface ButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  disabled?: boolean;
  className?: string;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
}

export interface InputProps {
  label?: string;
  error?: string;
  helperText?: string;
  className?: string;
}

// Table Types
export interface Column<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  render?: (value: unknown, row: T) => React.ReactNode;
}

// Export/Download Types
export interface ExportOptions {
  format: "csv" | "json" | "xlsx";
  filename?: string;
}

// WhatsApp Integration Types
export interface WhatsAppStatus {
  connected: boolean;
  phone_number?: string;
  verified_name?: string;
  quality_rating?: string;
  display_name?: string;
  connected_at?: string;
  has_shared_access: boolean;
}

export interface WhatsAppConnectRequest {
  phone_number_id: string;
  access_token: string;
  business_account_id?: string;
  display_name?: string;
}

export interface WhatsAppConnectResponse {
  success: boolean;
  message: string;
  phone_number?: string;
  verified_name?: string;
  quality_rating?: string;
}

export interface WhatsAppSendRequest {
  to: string;
  message: string;
}

export interface WhatsAppBulkRequest {
  recipients?: { phone: string; message: string }[];
  message_template?: string;
  leads?: Lead[];
  delay_ms?: number;
}

export interface WhatsAppBulkResponse {
  success: boolean;
  total: number;
  sent: number;
  failed: number;
  errors: { phone: string; error: string }[];
}

export interface WhatsAppTemplate {
  name: string;
  status: string;
  category: string;
  language: string;
}

export interface WhatsAppTemplatesResponse {
  success: boolean;
  templates: WhatsAppTemplate[];
}
