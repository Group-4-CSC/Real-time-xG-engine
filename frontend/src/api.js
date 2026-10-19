// All frontend-to-Django requests belong here.
// Optional: set VITE_API_BASE_URL=http://localhost:8000 in frontend/.env.local
const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) throw new Error(`API request failed (${response.status}): ${path}`)
  return response.json()
}

// Available backend foundation; not yet invoked by the demo UI.
export function getHealth() { return request('/api/health/') }
export function calculateXg(shot) {
  return request('/api/xg/calculate/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(shot),
  })
}

// Planned endpoint: use once Joseph confirms its response structure.
export function getMatch(matchId) {
  return request(`/api/matches/${encodeURIComponent(matchId)}/`)
}

// CSV upload endpoint is intentionally not invented here; Joseph has not finalized it.
