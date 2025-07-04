import type { 
  SearchRequest, 
  SearchJobResponse, 
  SearchJobDetail,
  UserLogin,
  Token,
  ApiError
} from "./types"

const API_BASE_URL = "http://127.0.0.1:8000"

class ApiClient {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("token")
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    }
  }
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    }

    const response = await fetch(url, config)
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }
    
    return response.json()
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" })
  }

  // Specific API methods
  async createSearchJob(request: SearchRequest): Promise<SearchJobResponse> {
    return this.post<SearchJobResponse>("/api/search/", request)
  }

  async getSearchJob(jobId: number): Promise<SearchJobDetail> {
    return this.get<SearchJobDetail>(`/api/search/${jobId}`)
  }

  async login(credentials: UserLogin): Promise<Token> {
    return this.post<Token>("/api/auth/login", credentials)
  }
}

export const apiClient = new ApiClient()
export default apiClient