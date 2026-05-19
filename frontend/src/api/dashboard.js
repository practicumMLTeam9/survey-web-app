// api/dashboard.js

import { apiRequest } from "./client"

export function getDashboards() {
    return apiRequest("/api/v1/dashboard")
}