// ========================================
// Google Sheets Integration Hook
// ========================================
// 
// Uses the API proxy which automatically handles authentication
// via httpOnly session cookies. No token passing required.
// ========================================

"use client";

import { useState, useCallback, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import type { GoogleIntegrationStatus, SaveToGoogleSheetsResponse, Lead } from "@/types";

interface UseGoogleSheetsReturn {
  status: GoogleIntegrationStatus | null;
  isLoading: boolean;
  isConnecting: boolean;
  isSaving: boolean;
  error: string | null;
  isAuthenticated: boolean;
  fetchStatus: () => Promise<void>;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  saveToSheets: (leads: Lead[], query?: string, sheetName?: string, spreadsheetId?: string) => Promise<SaveToGoogleSheetsResponse | null>;
}

export function useGoogleSheets(): UseGoogleSheetsReturn {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [status, setStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch integration status
  const fetchStatus = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getGoogleIntegrationStatus();

      if (response.data) {
        setStatus(response.data);
      } else if (response.error) {
        // Don't show error if just not connected
        if (response.status !== 401) {
          setError(response.error);
        }
      }
    } catch (err) {
      console.error("Failed to fetch Google Sheets status:", err);
      setError("Failed to check integration status");
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Connect Google Sheets (initiates OAuth flow)
  const connect = useCallback(async () => {
    if (!isAuthenticated) {
      setError("Please log in first");
      return;
    }

    try {
      setIsConnecting(true);
      setError(null);

      const response = await apiClient.getGoogleAuthURL();

      if (response.data?.authorization_url) {
        // Store state for CSRF verification on callback
        if (response.data.state) {
          sessionStorage.setItem("google_oauth_state", response.data.state);
        }
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url;
      } else if (response.error) {
        setError(response.error);
        setIsConnecting(false);
      }
    } catch (err) {
      console.error("Failed to connect Google Sheets:", err);
      setError("Failed to initiate Google connection");
      setIsConnecting(false);
    }
  }, [isAuthenticated]);

  // Disconnect Google Sheets
  const disconnect = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiClient.disconnectGoogleSheets();

      if (response.data?.success) {
        setStatus({ connected: false });
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      console.error("Failed to disconnect Google Sheets:", err);
      setError("Failed to disconnect");
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Save leads to Google Sheets
  const saveToSheets = useCallback(async (
    leads: Lead[],
    query?: string,
    sheetName: string = "Scrappy Results",
    spreadsheetId?: string
  ): Promise<SaveToGoogleSheetsResponse | null> => {
    if (!isAuthenticated) {
      setError("Please log in first");
      return null;
    }

    if (!status?.connected) {
      setError("Please connect Google Sheets first");
      return null;
    }

    try {
      setIsSaving(true);
      setError(null);

      // Format leads as 2D array for Google Sheets
      const data = leads.map(lead => [
        lead.name || "",
        lead.address || "",
        lead.phone || "",
        lead.website || "",
        lead.rating?.toString() || "",
        lead.reviews_count?.toString() || "",
        lead.category || "",
        lead.place_id || "",
        lead.latitude?.toString() || "",
        lead.longitude?.toString() || "",
        lead.scraped_at || new Date().toISOString(),
      ]);

      const response = await apiClient.saveToGoogleSheets({
        spreadsheet_id: spreadsheetId,
        sheet_name: sheetName,
        query,
        data,
      });

      if (response.data) {
        return response.data;
      } else if (response.error) {
        setError(response.error);
        return null;
      }

      return null;
    } catch (err) {
      console.error("Failed to save to Google Sheets:", err);
      setError("Failed to save to Google Sheets");
      return null;
    } finally {
      setIsSaving(false);
    }
  }, [isAuthenticated, status?.connected]);

  // Fetch status when authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchStatus();
    } else if (!authLoading) {
      setIsLoading(false);
    }
  }, [isAuthenticated, authLoading, fetchStatus]);

  return {
    status,
    isLoading,
    isConnecting,
    isSaving,
    error,
    isAuthenticated,
    fetchStatus,
    connect,
    disconnect,
    saveToSheets,
  };
}
