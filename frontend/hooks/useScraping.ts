// ========================================
// Scraping Hook with State Management
// ========================================
//
// Uses the API proxy which automatically handles authentication
// via httpOnly session cookies. No token passing required.
// ========================================

"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import type {
  Lead,
  ScrapeRequest,
  ScrapeResponse,
  ScrapeProgress,
  SaveToSheetsResponse,
} from "@/types";

interface AsyncScrapeResponse {
  scrape_id: string;
  status: string;
  query: string;
  target_count: number;
  message: string;
}

interface UseScrapingReturn {
  // State
  leads: Lead[];
  isLoading: boolean;
  progress: ScrapeProgress;
  error: string | null;
  lastScrapeResult: ScrapeResponse | null;
  scrapeId: string | null;

  // Actions
  startScraping: (params: ScrapeRequest) => Promise<ScrapeResponse | null>;
  startScrapingAsync: (params: ScrapeRequest) => Promise<AsyncScrapeResponse | null>;
  saveToSheets: (spreadsheetId?: string) => Promise<SaveToSheetsResponse | null>;
  clearResults: () => void;
  clearError: () => void;
  setLeads: (leads: Lead[]) => void;
  setScrapeId: (id: string | null) => void;
  handleAsyncComplete: (results: Lead[]) => void;
  handleAsyncError: (error: string) => void;
}

const initialProgress: ScrapeProgress = {
  status: "idle",
  currentCount: 0,
  targetCount: 0,
  message: "",
};

export function useScraping(): UseScrapingReturn {
  const { isAuthenticated } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<ScrapeProgress>(initialProgress);
  const [error, setError] = useState<string | null>(null);
  const [lastScrapeResult, setLastScrapeResult] = useState<ScrapeResponse | null>(null);
  const [scrapeId, setScrapeId] = useState<string | null>(null);

  const clearResults = useCallback(() => {
    setLeads([]);
    setLastScrapeResult(null);
    setProgress(initialProgress);
    setError(null);
    setScrapeId(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Handle completion from async progress component
  const handleAsyncComplete = useCallback((results: Lead[]) => {
    console.log('[useScraping] handleAsyncComplete called with', results?.length || 0, 'results');
    console.log('[useScraping] First result sample:', results?.[0]);
    setLeads(results);
    setIsLoading(false);
    setScrapeId(null);
    setProgress({
      status: "complete",
      currentCount: results.length,
      targetCount: results.length,
      message: `Found ${results.length} leads!`,
    });
    console.log('[useScraping] State updated: leads set, isLoading=false, scrapeId=null');
  }, []);

  // Handle error from async progress component
  const handleAsyncError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
    setScrapeId(null);
    setProgress({
      status: "error",
      currentCount: 0,
      targetCount: 0,
      message: errorMessage,
    });
  }, []);

  // Start async scraping with progress tracking (uses proxy for auth)
  const startScrapingAsync = useCallback(async (params: ScrapeRequest): Promise<AsyncScrapeResponse | null> => {
    console.log("[useScraping] startScrapingAsync called with:", params);
    
    if (!isAuthenticated) {
      const errorMsg = "Authentication required. Please sign in.";
      setError(errorMsg);
      return null;
    }

    setIsLoading(true);
    setError(null);
    setScrapeId(null);
    setProgress({
      status: "scrolling",
      currentCount: 0,
      targetCount: params.target_count || 50,
      message: "Starting scrape...",
    });

    try {
      // Call the async scrape endpoint via proxy
      const response = await fetch('/api/proxy/api/scrape-async', {
        method: 'POST',
        credentials: 'include', // Include cookies for session
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.error || 'Failed to start scrape');
      }

      const data: AsyncScrapeResponse = await response.json();
      console.log("[useScraping] Async scrape started:", data);
      
      setScrapeId(data.scrape_id);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start scraping";
      setError(errorMessage);
      setIsLoading(false);
      return null;
    }
  }, [isAuthenticated]);

  // Original synchronous scraping (kept for backward compatibility)
  const startScraping = useCallback(async (params: ScrapeRequest): Promise<ScrapeResponse | null> => {
    console.log("[useScraping] startScraping called with:", params);
    console.log("[useScraping] isAuthenticated:", isAuthenticated);
    
    if (!isAuthenticated) {
      const errorMsg = "Authentication required. Please sign in.";
      console.error("[useScraping] User not authenticated");
      setError(errorMsg);
      return null;
    }

    setIsLoading(true);
    setError(null);
    setProgress({
      status: "scrolling",
      currentCount: 0,
      targetCount: params.target_count || 50,
      message: "Starting scrape...",
    });

    try {
      // Update progress to extracting
      setProgress((prev) => ({
        ...prev,
        status: "extracting",
        message: `Scraping for "${params.search_query}"...`,
      }));

      console.log("[useScraping] Calling apiClient.scrape...");
      const response = await apiClient.scrape(params);
      console.log("[useScraping] API response:", response);

      if (response.error) {
        setError(response.error);
        setProgress({
          status: "error",
          currentCount: 0,
          targetCount: params.target_count || 50,
          message: response.error,
        });
        return null;
      }

      if (response.data) {
        setLeads(response.data.leads);
        setLastScrapeResult(response.data);
        setProgress({
          status: "complete",
          currentCount: response.data.unique_count,
          targetCount: params.target_count || 50,
          message: `Found ${response.data.unique_count} leads!`,
        });
        return response.data;
      }

      return null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Scraping failed";
      setError(errorMessage);
      setProgress({
        status: "error",
        currentCount: 0,
        targetCount: params.target_count || 50,
        message: errorMessage,
      });
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const saveToSheets = useCallback(async (spreadsheetId?: string): Promise<SaveToSheetsResponse | null> => {
    if (leads.length === 0) {
      setError("No leads to save");
      return null;
    }

    if (!isAuthenticated) {
      setError("Authentication required. Please sign in.");
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.saveToSheets({
        leads,
        spreadsheet_id: spreadsheetId,
      });

      if (response.error) {
        setError(response.error);
        return null;
      }

      return response.data || null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to save to sheets";
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [leads, isAuthenticated]);

  return {
    leads,
    isLoading,
    progress,
    error,
    lastScrapeResult,
    scrapeId,
    startScraping,
    startScrapingAsync,
    saveToSheets,
    clearResults,
    clearError,
    setLeads,
    setScrapeId,
    handleAsyncComplete,
    handleAsyncError,
  };
}

export default useScraping;
