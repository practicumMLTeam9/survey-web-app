const API_URL = ""

export async function apiRequest(path, options = {}) {
    const token = localStorage.getItem("access_token")

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(options.headers || {}),
        },
    })

    if (response.status === 401) {
        localStorage.clear()
        window.location.href = "/login"
        return
    }

    const data = await response.json().catch(() => null)

    if (!response.ok) {
        console.log("API ERROR:", data)

        const message = Array.isArray(data?.detail)
            ? data.detail.map((e) => `${e.loc?.join(".")}: ${e.msg}`).join("\n")
            : data?.detail || "Ошибка запроса"

        throw new Error(message)
    }

    return data
}