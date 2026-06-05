const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8765'

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL

export const API_BASE_URL = configuredApiBaseUrl.replace(/\/$/, '')
export const WS_URL = import.meta.env.VITE_WS_URL || `${API_BASE_URL.replace(/^http/, 'ws')}/ws`
