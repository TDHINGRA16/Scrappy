// ========================================
// API Hook for Backend Communication
// ========================================

"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type {
  ScrapeRequest,
  ScrapeResponse,
  SaveToSheetsRequest,
  SaveToSheetsResponse,
  SMSOutreachRequest,
  SMSOutreachResponse,
  ApiResponse,
} from "@/types";

interface UseApiReturn {
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  healthCheck: () => Promise<ApiResponse<{ status: string }>>;
  scrape: (params: ScrapeRequest) => Promise<ApiResponse<ScrapeResponse>>;
  saveToSheets: (params: SaveToSheetsRequest) => Promise<ApiResponse<SaveToSheetsResponse>>;
  sendOutreach: (params: SMSOutreachRequest) => Promise<ApiResponse<SMSOutreachResponse>>;
}

export function useApi(): UseApiReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleRequest = useCallback(async <T>(
    request: () => Promise<ApiResponse<T>>
  ): Promise<ApiResponse<T>> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await request();
      if (response.error) {
        setError(response.error);
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      return { error: errorMessage, status: 500 };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const healthCheck = useCallback(() => {
    return handleRequest(() => apiClient.healthCheck());
  }, [handleRequest]);

  const scrape = useCallback((params: ScrapeRequest) => {
    return handleRequest(() => apiClient.scrape(params));
  }, [handleRequest]);

  const saveToSheets = useCallback((params: SaveToSheetsRequest) => {
    return handleRequest(() => apiClient.saveToSheets(params));
  }, [handleRequest]);

  const sendOutreach = useCallback((params: SMSOutreachRequest) => {
    return handleRequest(() => apiClient.sendOutreach(params));
  }, [handleRequest]);

  return {
    isLoading,
    error,
    clearError,
    healthCheck,
    scrape,
    saveToSheets,
    sendOutreach,
  };
}

export default useApi;
