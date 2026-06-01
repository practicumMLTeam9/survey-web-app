import { apiRequest } from "./client"

export async function getPollForVote(pollId) {
    const response = await fetch(`/api/v1/polls/${pollId}`, {
        credentials: "include",
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
        throw new Error(data?.detail || "Не удалось загрузить опрос")
    }

    return data
}

export async function startVote(pollId) {
    const response = await fetch(`/api/v1/polls/${pollId}/vote/start`, {
        method: "POST",
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Не удалось начать прохождение опроса")
    }

    return response.json()
}

export async function submitVote(pollId, answers) {
    const response = await fetch(`/api/v1/polls/${pollId}/vote`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ answers }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
        throw new Error(data?.detail || "Не удалось отправить ответы")
    }

    return data
}