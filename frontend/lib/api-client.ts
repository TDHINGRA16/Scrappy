// ========================================
// API Client for Backend Communication
// ========================================
// 
// Uses Next.js API proxy to forward requests to FastAPI backend.
// The proxy automatically extracts the session token from httpOnly cookies
// and adds it to the Authorization header.
// ========================================

import type {
  ScrapeRequest,
  ScrapeResponse,
  SaveToSheetsRequest,
  SaveToSheetsResponse,
  SMSOutreachRequest,
  SMSOutreachResponse,
  ApiResponse,
  GoogleIntegrationStatus,
  GoogleAuthURLResponse,
  GoogleCallbackRequest,
  GoogleCallbackResponse,
  SaveToGoogleSheetsRequest,
  SaveToGoogleSheetsResponse,
  WhatsAppStatus,
  WhatsAppConnectRequest,
  WhatsAppConnectResponse,
  WhatsAppSendRequest,
  WhatsAppBulkRequest,
  WhatsAppBulkResponse,
  WhatsAppTemplatesResponse,
} from "@/types";

// Direct backend URL for health checks (no auth required)
const DIRECT_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Proxy URL for authenticated requests (routes through Next.js to add auth)
const PROXY_URL = "/api/proxy";

class ApiClient {
  private directUrl: string;
  private proxyUrl: string;

  constructor(directUrl: string, proxyUrl: string) {
    this.directUrl = directUrl;
    this.proxyUrl = proxyUrl;
  }

  // Direct request to backend (no auth)
  private async directRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.directUrl}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || data.message || "An error occurred",
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 500,
      };
    }
  }

  // Proxied request through Next.js (auto-adds auth from httpOnly cookie)
  private async proxyRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      // Remove leading slash if present to avoid double slashes
      const cleanEndpoint = endpoint.startsWith("/") ? endpoint.slice(1) : endpoint;
      const response = await fetch(`${this.proxyUrl}/${cleanEndpoint}`, {
        ...options,
        credentials: "include", // Include cookies for session
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        // Ensure error is always a string
        let errorMessage = "An error occurred";
        if (typeof data.detail === "string") {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Handle Pydantic validation errors
          errorMessage = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
        } else if (data.error) {
          errorMessage = typeof data.error === "string" ? data.error : JSON.stringify(data.error);
        } else if (data.message) {
          errorMessage = typeof data.message === "string" ? data.message : JSON.stringify(data.message);
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 500,
      };
    }
  }

  // Health Check (no auth required)
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.directRequest("/health");
  }

  // Scraping Endpoints (token param kept for compatibility, but not used - proxy handles auth)
  async scrape(params: ScrapeRequest, _token?: string): Promise<ApiResponse<ScrapeResponse>> {
    return this.proxyRequest("/api/scrape", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Google Sheets Endpoints
  async saveToSheets(
    params: SaveToSheetsRequest,
    _token?: string
  ): Promise<ApiResponse<SaveToSheetsResponse>> {
    return this.proxyRequest("/api/save-to-sheets", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // SMS Outreach Endpoints
  async sendOutreach(
    params: SMSOutreachRequest,
    _token?: string
  ): Promise<ApiResponse<SMSOutreachResponse>> {
    return this.proxyRequest("/api/send-outreach", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Combined Scrape and Save
  async scrapeAndSave(
    params: ScrapeRequest & { spreadsheet_id?: string; sheet_name?: string }
  ): Promise<ApiResponse<ScrapeResponse & SaveToSheetsResponse>> {
    return this.proxyRequest("/api/scrape-and-save", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // ========================================
  // Google Sheets Integration Endpoints
  // ========================================

  // Get Google Sheets authorization URL
  async getGoogleAuthURL(_token?: string): Promise<ApiResponse<GoogleAuthURLResponse>> {
    return this.proxyRequest("/api/integrations/google/authorize");
  }

  // Handle Google OAuth callback
  async googleOAuthCallback(
    params: GoogleCallbackRequest,
    _token?: string
  ): Promise<ApiResponse<GoogleCallbackResponse>> {
    return this.proxyRequest("/api/integrations/google/callback", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Get Google Sheets integration status
  async getGoogleIntegrationStatus(_token?: string): Promise<ApiResponse<GoogleIntegrationStatus>> {
    return this.proxyRequest("/api/integrations/google/status");
  }

  // Save data to Google Sheets
  async saveToGoogleSheets(
    params: SaveToGoogleSheetsRequest,
    _token?: string
  ): Promise<ApiResponse<SaveToGoogleSheetsResponse>> {
    return this.proxyRequest("/api/integrations/google/save-to-sheet", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Disconnect Google Sheets integration
  async disconnectGoogleSheets(_token?: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.proxyRequest("/api/integrations/google/disconnect", {
      method: "DELETE",
    });
  }

  // Test Google Sheets connection
  async testGoogleConnection(_token?: string): Promise<ApiResponse<{
    connected: boolean;
    google_email?: string;
    google_name?: string;
    error?: string;
  }>> {
    return this.proxyRequest("/api/integrations/google/test-connection");
  }

  // ========================================
  // WhatsApp Integration Endpoints
  // ========================================

  // Get WhatsApp connection status
  async getWhatsAppStatus(_token?: string): Promise<ApiResponse<WhatsAppStatus>> {
    return this.proxyRequest("/api/whatsapp/status");
  }

  // Connect WhatsApp Business account
  async connectWhatsApp(
    params: WhatsAppConnectRequest,
    _token?: string
  ): Promise<ApiResponse<WhatsAppConnectResponse>> {
    return this.proxyRequest("/api/whatsapp/connect", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Send single WhatsApp message
  async sendWhatsAppMessage(
    params: WhatsAppSendRequest,
    _token?: string
  ): Promise<ApiResponse<{ success: boolean; message_id?: string }>> {
    return this.proxyRequest("/api/whatsapp/send", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Send bulk WhatsApp messages
  async sendBulkWhatsApp(
    params: WhatsAppBulkRequest,
    _token?: string
  ): Promise<ApiResponse<WhatsAppBulkResponse>> {
    return this.proxyRequest("/api/whatsapp/send-bulk", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Get WhatsApp message templates
  async getWhatsAppTemplates(_token?: string): Promise<ApiResponse<WhatsAppTemplatesResponse>> {
    return this.proxyRequest("/api/whatsapp/templates");
  }

  // Disconnect WhatsApp integration
  async disconnectWhatsApp(_token?: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.proxyRequest("/api/whatsapp/disconnect", {
      method: "POST",
    });
  }

  // Test WhatsApp connection
  async testWhatsAppConnection(_token?: string): Promise<ApiResponse<{
    success: boolean;
    using?: string;
    phone_number?: string;
    verified_name?: string;
    quality_rating?: string;
    error?: string;
  }>> {
    return this.proxyRequest("/api/whatsapp/test", {
      method: "POST",
    });
  }

  // ========================================
  // History & Stats Endpoints
  // ========================================

  // Get scrape history
  async getHistory(_token?: string, limit: number = 20, offset: number = 0): Promise<ApiResponse<{
    success: boolean;
    history: Array<{
      id: string;
      query: string;
      total_found: number;
      new_results: number;
      skipped_duplicates: number;
      time_taken: number;
      sheet_url: string | null;
      sheet_id: string | null;
      status: string;
      error: string | null;
      date: string;
      completed_at: string | null;
    }>;
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }>> {
    return this.proxyRequest(`/api/history?limit=${limit}&offset=${offset}`);
  }

  // Get user stats
  async getUserStats(_token?: string): Promise<ApiResponse<{
    success: boolean;
    total_unique_businesses: number;
    total_scrapes: number;
    total_results_collected: number;
    total_duplicates_skipped: number;
    dedup_efficiency: number;
    total_time_saved_minutes: number;
    recent_scrapes: Array<{
      id: string;
      query: string;
      new_results: number;
      date: string;
    }>;
  }>> {
    return this.proxyRequest("/api/stats");
  }

  // Get seen places count
  async getSeenPlacesCount(_token?: string): Promise<ApiResponse<{
    success: boolean;
    seen_places_count: number;
    message: string;
  }>> {
    return this.proxyRequest("/api/seen-places");
  }
}

export const apiClient = new ApiClient(DIRECT_API_URL, PROXY_URL);
export default apiClient;
