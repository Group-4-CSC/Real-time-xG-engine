import { statsFor } from '../components/vizShared.js'

// Shared calculation used by the Coach Dashboard and its acceptance tests.
export function dashboardMetrics(shots, team) {
  const own = shots.filter(s => s.team === team)
  const opponent = shots.filter(s => s.team !== team)
  return {
    matches: new Set(shots.map(s => s.match_id)).size,
    homeStats: statsFor(own),
    awayStats: statsFor(opponent),
    playerStats: [...new Set(own.map(s => s.player))].map(name => ({
      name,
      ...statsFor(own.filter(s => s.player === name)),
    })),
  }
}
