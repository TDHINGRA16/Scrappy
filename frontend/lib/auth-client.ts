// ========================================
// BetterAuth Client Configuration
// ========================================

import { createAuthClient } from "better-auth/client";

export const authClient = createAuthClient({
  // BetterAuth routes are in Next.js, not FastAPI backend
  // Use NEXT_PUBLIC_ prefix for client-side access
  baseURL: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
});

// Auth helper functions
export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;
