// ========================================
// Authentication Hook
// ========================================

"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { authClient } from "@/lib/auth-client";
import type { User, Session } from "@/types";

export interface UseAuthReturn {
  user: User | null;
  session: Session | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, name: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      console.log("[useAuth] Refreshing session...");
      const sessionData = await authClient.getSession();
      console.log("[useAuth] Session data:", sessionData);
      
      if (sessionData?.data) {
        setUser(sessionData.data.user as User);
        // Ensure the session object includes the 'expires' property
        setSession({
          user: sessionData.data.user,
          expires: (sessionData.data.session?.expiresAt ?? new Date()) as Date,
        } as Session);
        // Extract access token from session
        // BetterAuth typically stores the token in session.token or we need to extract from cookies
        const sessionToken = (sessionData.data.session as any)?.token || 
                           (sessionData.data.session as any)?.accessToken ||
                           (sessionData.data as any)?.token ||
                           null;
        console.log("[useAuth] Extracted token:", sessionToken ? "present" : "missing");
        setToken(sessionToken);
        
        if (!sessionToken) {
          console.warn("[useAuth] No access token found in session. Backend auth will fail.");
          console.log("[useAuth] Session structure:", JSON.stringify(sessionData.data, null, 2));
        }
      } else {
        console.log("[useAuth] No session data available");
        setUser(null);
        setSession(null);
        setToken(null);
      }
    } catch (error) {
      console.error("[useAuth] Failed to refresh session:", error);
      setUser(null);
      setSession(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const result = await authClient.signIn.email({
        email,
        password,
      });

      if (result.error) {
        return { error: result.error.message || "Sign in failed" };
      }

      await refreshSession();
      return {};
    } catch (error) {
      return { error: error instanceof Error ? error.message : "Sign in failed" };
    } finally {
      setIsLoading(false);
    }
  }, [refreshSession]);

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    try {
      setIsLoading(true);
      const result = await authClient.signUp.email({
        email,
        password,
        name,
      });

      if (result.error) {
        return { error: result.error.message || "Sign up failed" };
      }

      await refreshSession();
      return {};
    } catch (error) {
      return { error: error instanceof Error ? error.message : "Sign up failed" };
    } finally {
      setIsLoading(false);
    }
  }, [refreshSession]);

  const signOut = useCallback(async () => {
    try {
      setIsLoading(true);
      await authClient.signOut();
      setUser(null);
      setSession(null);
    } catch (error) {
      console.error("Sign out failed:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    user,
    session,
    token,
    isLoading,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
    refreshSession,
  };
}

export default useAuth;
