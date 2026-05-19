import { apiRequest } from "./client"

export function loginUser(data) {
    return apiRequest("/api/v1/auth/login?use_cookie=false", {
        method: "POST",
        body: JSON.stringify(data),
    })
}

export function registerUser(data) {
    return apiRequest("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
    })
}

export function getMe() {
    return apiRequest("/api/v1/auth/me?use_cookie=false&token_type=access")
}

export function logoutUser() {
    localStorage.clear()
}