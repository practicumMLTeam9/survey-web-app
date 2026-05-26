import { apiRequest } from "./client"

export function getMyPolls() {
    return apiRequest("/api/v1/polls/?use_cookie=false&token_type=access")
}

export function getPollById(id) {
    return apiRequest(`/api/v1/polls/${id}`)
}

export function createPoll(data) {
    return apiRequest("/api/v1/polls/?use_cookie=false&token_type=access", {
        method: "POST",
        body: JSON.stringify(data),
    })
}

export function updatePollStatus(id, status) {
    return apiRequest(`/api/v1/polls/${id}/status?use_cookie=false&token_type=access`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
    })
}

export function getPollResults(id) {
    return apiRequest(`/api/v1/polls/${id}/results?use_cookie=false&token_type=access`)
}

export function updatePoll(pollId, data) {
    return apiRequest(`/api/v1/polls/${pollId}?use_cookie=false&token_type=access`, {
        method: "POST",
        body: JSON.stringify(data),
    })
}