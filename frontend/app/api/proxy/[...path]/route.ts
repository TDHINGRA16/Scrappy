// ========================================
// API Proxy Route - Forwards requests to FastAPI with session token
// ========================================

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_URL || "http://localhost:8000";

// Better Auth session cookie name
const SESSION_COOKIE_NAME = "better-auth.session_token";

async function proxyRequest(request: NextRequest, path: string[]) {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (!sessionCookie) {
    return NextResponse.json(
      { error: "Unauthorized - No session token" },
      { status: 401 }
    );
  }

  // Better Auth stores signed tokens in format: {token}.{signature}
  // The database only stores the {token} part (before the dot)
  const sessionToken = sessionCookie.split('.')[0];

  if (!sessionToken) {
    return NextResponse.json(
      { error: "Unauthorized - Invalid session token format" },
      { status: 401 }
    );
  }

  // Build the target URL
  const targetPath = "/" + path.join("/");
  const url = new URL(targetPath, API_BASE_URL);
  
  // Copy search params
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value);
  });

  // Get request body if present
  let body: string | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    try {
      body = await request.text();
    } catch {
      body = undefined;
    }
  }

  // Forward the request to FastAPI
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${sessionToken}`,
  };

  try {
    const response = await fetch(url.toString(), {
      method: request.method,
      headers,
      body: body || undefined,
    });

    // Try to parse as JSON, fallback to text
    const contentType = response.headers.get("content-type") || "";
    let data;
    
    if (contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch {
        const text = await response.text();
        data = { error: text || "Invalid JSON response from backend" };
      }
    } else {
      const text = await response.text();
      // If it's an error status, wrap the text in an error object
      if (!response.ok) {
        data = { error: text || `Backend error: ${response.status}` };
      } else {
        // Try to parse as JSON anyway in case content-type is wrong
        try {
          data = JSON.parse(text);
        } catch {
          data = { message: text };
        }
      }
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("[API Proxy] Error:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 502 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}
