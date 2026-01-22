// ========================================
// BetterAuth Client Configuration
// ========================================

import { createAuthClient } from "better-auth/client";

export const authClient = createAuthClient({
  // BetterAuth routes are in Next.js, not FastAPI backend
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
});

// Auth helper functions
export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;
