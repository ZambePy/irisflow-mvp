import { API_BASE_URL } from '../config/api'

async function request(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (e) {
    console.warn(`[API] ${path} falhou:`, e.message)
    return null
  }
}

export const api = {
  getProfiles:      ()       => request('/profiles/'),
  createProfile:    (data)   => request('/profiles/', { method: 'POST', body: JSON.stringify(data) }),
  getCategories:    ()       => request('/phrases/categories'),
  getPhrases:       (cat)    => request(`/phrases/${cat}`),
  newCalibSession:  ()       => request('/calibration/new_session', { method: 'POST' }),
  collectPoint:     (data)   => request('/calibration/collect_point', { method: 'POST', body: JSON.stringify(data) }),
  fitCalibration:   ()       => request('/calibration/fit', { method: 'POST' }),
  getCalibResult:   ()       => request('/calibration/result'),
}
