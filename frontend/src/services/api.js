const API_BASE_URL = "http://localhost:5000"

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("access_token")

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(data?.error || "Something went wrong")
  }

  return data
}