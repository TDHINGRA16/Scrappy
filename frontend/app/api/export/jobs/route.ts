import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get("authorization")

    if (!authHeader) {
      return NextResponse.json({ detail: "Authorization header missing" }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const page = searchParams.get("page") || "1"
    const size = searchParams.get("size") || "10"

    // Forward the request to the actual API
    const response = await fetch(`http://127.0.0.1:8000/api/export/jobs?page=${page}&size=${size}`, {
      headers: {
        Authorization: authHeader,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ detail: data.detail || "Failed to fetch jobs" }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}
