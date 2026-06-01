import { apiRequest } from "./client"

export function generatePoll(data) {
    return apiRequest("/api/v1/ai/generate_poll?use_cookie=false&token_type=access", {
        method: "POST",
        body: JSON.stringify(data),
    })
}