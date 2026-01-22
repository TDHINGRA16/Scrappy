// ========================================
// Google OAuth Callback Page
// ========================================
//
// Handles the OAuth callback from Google after user authorizes.
// Uses the API proxy which automatically handles authentication
// via httpOnly session cookies.
// ========================================

"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";

type CallbackStatus = "processing" | "success" | "error";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<CallbackStatus>("processing");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");

      // Handle error from Google
      if (error) {
        setStatus("error");
        setMessage(
          error === "access_denied"
            ? "You declined to connect Google Sheets. Please try again if this was a mistake."
            : `Google returned an error: ${error}`
        );
        return;
      }

      // Validate required params
      if (!code || !state) {
        setStatus("error");
        setMessage("Missing authorization code or state. Please try connecting again.");
        return;
      }

      try {
        // Exchange code for tokens (proxy handles authentication via cookies)
        const response = await apiClient.googleOAuthCallback({ code, state });

        if (response.data?.success) {
          setStatus("success");
          setMessage(response.data.message || "Google Sheets connected successfully!");
          setEmail(response.data.email || null);

          // Redirect to settings/integrations page after success
          setTimeout(() => {
            router.push("/dashboard/settings");
          }, 2500);
        } else if (response.status === 401) {
          setStatus("error");
          setMessage("You need to be logged in. Please log in and try again.");
        } else {
          setStatus("error");
          setMessage(response.error || "Failed to complete Google authorization");
        }
      } catch (err) {
        console.error("OAuth callback error:", err);
        setStatus("error");
        setMessage("An unexpected error occurred. Please try again.");
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="max-w-md w-full">
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        {/* Processing State */}
        {status === "processing" && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 relative">
              <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
              <div className="absolute inset-0 rounded-full border-4 border-green-500 border-t-transparent animate-spin"></div>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Connecting Google Sheets...
            </h1>
            <p className="text-gray-500">
              Please wait while we complete the authorization
            </p>
          </>
        )}

        {/* Success State */}
        {status === "success" && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-green-100 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Successfully Connected!
            </h1>
            <p className="text-gray-500 mb-4">{message}</p>
            {email && (
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-lg mb-4">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span className="text-sm text-gray-700">{email}</span>
              </div>
            )}
            <p className="text-sm text-gray-400">
              Redirecting to settings...
            </p>
          </>
        )}

        {/* Error State */}
        {status === "error" && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Connection Failed
            </h1>
            <p className="text-gray-500 mb-6">{message}</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={() => router.push("/dashboard/settings")}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back to Settings
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <p className="mt-6 text-center text-xs text-gray-400">
        Your Google Sheets credentials are encrypted and stored securely
      </p>
    </div>
  );
}

export default function GoogleOAuthCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Suspense fallback={
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 relative">
              <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
              <div className="absolute inset-0 rounded-full border-4 border-green-500 border-t-transparent animate-spin"></div>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Loading...
            </h1>
          </div>
        </div>
      }>
        <GoogleCallbackContent />
      </Suspense>
    </div>
  );
}
