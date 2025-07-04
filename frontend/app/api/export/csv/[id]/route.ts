import { NextResponse } from "next/server"

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const authHeader = request.headers.get("authorization")

    if (!authHeader) {
      return NextResponse.json({ detail: "Authorization header missing" }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const includeMessages = searchParams.get("include_messages") || "false"

    // Forward the request to the actual API
    const response = await fetch(`http://127.0.0.1:8000/api/export/csv/${id}?include_messages=${includeMessages}`, {
      headers: {
        Authorization: authHeader,
      },
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ detail: errorData.detail || "Failed to export CSV" }, { status: response.status })
    }

    // For file downloads, we need to pass through the response
    const blob = await response.blob()
    const headers = new Headers()
    headers.set("Content-Type", "text/csv")
    headers.set("Content-Disposition", `attachment; filename="export_${id}.csv"`)

    return new NextResponse(blob, { headers })
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return GET(request, { params })
}
