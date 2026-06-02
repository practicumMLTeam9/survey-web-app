import { apiRequest } from "../api/client"

export function getPollResults(id) {
    return apiRequest(
        `/api/v1/polls/${id}/results?use_cookie=false&token_type=access`
    )
}