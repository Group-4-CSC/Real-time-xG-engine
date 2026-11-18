// All frontend-to-Django requests belong here.
// Optional: set VITE_API_BASE_URL=http://localhost:8000 in frontend/.env.local
import { sampleShots } from './data/mockShots.js'

const API_BASE = (import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) throw new Error(`API request failed (${response.status}): ${path}`)
  return response.json()
}

// Available backend foundation; not yet invoked by the demo UI.
// Sprint 3: send only aggregate match statistics, not player names or API keys.
export function getAiMatchSummary(stats, { signal } = {}) {
  return request('/api/ai/match-summary/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(stats),
    signal,
  })
}

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

// The backend does not expose /api/matches/ yet. Use grouped demo shots by
// default, then pass { useMock: false } when the endpoint is available.
export async function getMatches({ useMock = true } = {}) {
  if (!useMock) return request('/api/matches/')

  const matches = new Map()
  for (const shot of sampleShots) {
    if (!matches.has(shot.match_id)) {
      matches.set(shot.match_id, { match_id: shot.match_id, teams: [], shots: [] })
    }
    const match = matches.get(shot.match_id)
    match.shots.push({ ...shot })
    if (shot.team && !match.teams.includes(shot.team)) match.teams.push(shot.team)
  }
  return [...matches.values()]
}
