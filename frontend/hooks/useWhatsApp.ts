// ========================================
// useWhatsApp Hook - WhatsApp Integration Management
// ========================================
//
// Uses the API proxy which automatically handles authentication
// via httpOnly session cookies. No token passing required.
// ========================================

"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "./useAuth";
import type { 
  WhatsAppStatus, 
  WhatsAppConnectRequest, 
  WhatsAppBulkRequest,
  WhatsAppBulkResponse,
  Lead 
} from "@/types";

interface UseWhatsAppReturn {
  // Status
  status: WhatsAppStatus | null;
  isLoading: boolean;
  isConnecting: boolean;
  isSending: boolean;
  error: string | null;
  
  // Actions
  refreshStatus: () => Promise<void>;
  connect: (credentials: WhatsAppConnectRequest) => Promise<boolean>;
  disconnect: () => Promise<boolean>;
  sendMessage: (to: string, message: string) => Promise<boolean>;
  sendBulkMessages: (
    leads: Lead[],
    messageTemplate: string,
    delayMs?: number
  ) => Promise<WhatsAppBulkResponse | null>;
  testConnection: () => Promise<{ success: boolean; using?: string; phone?: string }>;
}

export function useWhatsApp(): UseWhatsAppReturn {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch WhatsApp status
  const refreshStatus = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.getWhatsAppStatus();
      
      if (response.data) {
        setStatus(response.data);
      } else {
        setError(response.error || "Failed to fetch status");
      }
    } catch (err) {
      setError("Failed to check WhatsApp status");
      console.error("WhatsApp status error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Initial status fetch
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      refreshStatus();
    } else if (!authLoading) {
      setIsLoading(false);
    }
  }, [authLoading, isAuthenticated, refreshStatus]);

  // Connect WhatsApp account
  const connect = useCallback(async (credentials: WhatsAppConnectRequest): Promise<boolean> => {
    if (!isAuthenticated) {
      setError("Not authenticated");
      return false;
    }

    try {
      setIsConnecting(true);
      setError(null);

      const response = await apiClient.connectWhatsApp(credentials);

      if (response.data?.success) {
        await refreshStatus();
        return true;
      } else {
        setError(response.error || "Failed to connect WhatsApp");
        return false;
      }
    } catch (err) {
      setError("Failed to connect WhatsApp");
      console.error("WhatsApp connect error:", err);
      return false;
    } finally {
      setIsConnecting(false);
    }
  }, [isAuthenticated, refreshStatus]);

  // Disconnect WhatsApp account
  const disconnect = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated) {
      setError("Not authenticated");
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiClient.disconnectWhatsApp();

      if (response.data?.success) {
        setStatus(null);
        await refreshStatus();
        return true;
      } else {
        setError(response.error || "Failed to disconnect");
        return false;
      }
    } catch (err) {
      setError("Failed to disconnect WhatsApp");
      console.error("WhatsApp disconnect error:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, refreshStatus]);

  // Send single message
  const sendMessage = useCallback(async (to: string, message: string): Promise<boolean> => {
    if (!isAuthenticated) {
      setError("Not authenticated");
      return false;
    }

    try {
      setIsSending(true);
      setError(null);

      const response = await apiClient.sendWhatsAppMessage({ to, message });

      if (response.data?.success) {
        return true;
      } else {
        setError(response.error || "Failed to send message");
        return false;
      }
    } catch (err) {
      setError("Failed to send message");
      console.error("WhatsApp send error:", err);
      return false;
    } finally {
      setIsSending(false);
    }
  }, [isAuthenticated]);

  // Send bulk messages to leads
  const sendBulkMessages = useCallback(async (
    leads: Lead[],
    messageTemplate: string,
    delayMs: number = 100
  ): Promise<WhatsAppBulkResponse | null> => {
    if (!isAuthenticated) {
      setError("Not authenticated");
      return null;
    }

    if (!leads.length) {
      setError("No leads provided");
      return null;
    }

    // Filter leads with phone numbers
    const leadsWithPhone = leads.filter(lead => lead.phone);
    
    if (!leadsWithPhone.length) {
      setError("No leads with phone numbers");
      return null;
    }

    try {
      setIsSending(true);
      setError(null);

      const request: WhatsAppBulkRequest = {
        message_template: messageTemplate,
        leads: leadsWithPhone,
        delay_ms: delayMs,
      };

      const response = await apiClient.sendBulkWhatsApp(request);

      if (response.data) {
        return response.data;
      } else {
        setError(response.error || "Failed to send bulk messages");
        return null;
      }
    } catch (err) {
      setError("Failed to send bulk messages");
      console.error("WhatsApp bulk send error:", err);
      return null;
    } finally {
      setIsSending(false);
    }
  }, [isAuthenticated]);

  // Test connection
  const testConnection = useCallback(async (): Promise<{ 
    success: boolean; 
    using?: string; 
    phone?: string 
  }> => {
    if (!isAuthenticated) {
      return { success: false };
    }

    try {
      const response = await apiClient.testWhatsAppConnection();
      
      if (response.data) {
        return {
          success: response.data.success,
          using: response.data.using,
          phone: response.data.phone_number,
        };
      }
      
      return { success: false };
    } catch (err) {
      console.error("WhatsApp test error:", err);
      return { success: false };
    }
  }, [isAuthenticated]);

  return {
    status,
    isLoading,
    isConnecting,
    isSending,
    error,
    refreshStatus,
    connect,
    disconnect,
    sendMessage,
    sendBulkMessages,
    testConnection,
  };
}

export default useWhatsApp;
