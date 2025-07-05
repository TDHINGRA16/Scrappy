import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const authHeader = request.headers.get("authorization")

    if (!authHeader) {
      return NextResponse.json({ detail: "Authorization header missing" }, { status: 401 })
    }

    // Forward the request to the actual API
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/import/google-sheets`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ detail: data.detail || "Google Sheets import failed" }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}
