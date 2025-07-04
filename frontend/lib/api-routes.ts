export const API_BASE_URL = "http://127.0.0.1:8000"

export async function proxyGet(path: string, token: string) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `API error: ${response.status}`)
  }

  return response.json()
}

export async function proxyPost(path: string, token: string, body: any) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `API error: ${response.status}`)
  }

  return response.json()
}

export async function proxyFormData(path: string, token: string, formData: FormData) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `API error: ${response.status}`)
  }

  return response.json()
}
