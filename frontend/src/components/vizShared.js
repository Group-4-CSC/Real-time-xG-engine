// Shared helpers for the Shot Map and Match Summary screens.
// Shot format (agreed by the team): id, match_id, player, team, minute, period,
// x, y, outcome, body_part, assist_type, xg. x and y run 0-100, every shot attacks toward x = 100.
// xg may be null: the screens show "xG pending" instead of a number.

export const OUTCOMES = ['goal', 'saved', 'blocked', 'off_target', 'post']
export const OUTCOME_LABELS = { goal: 'Goal', saved: 'Saved', blocked: 'Blocked', off_target: 'Off target', post: 'Hit the post' }
export const outcomeLabel = o => OUTCOME_LABELS[o] ?? o
export const prettify = text => String(text ?? '').replace(/_/g, ' ')

export const HALF_OPTIONS = [
  { value: 'all', label: 'Both halves' },
  { value: '1', label: '1st half' },
  { value: '2', label: '2nd half' },
  { value: 'et', label: 'Extra time' },
]
export const periodMatches = (period, half) =>
  half === 'all' || (half === 'et' ? period >= 3 : String(period) === half)

// Team colors follow the team, never its rank: the home team is always blue.
const TEAM_PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#8a8984']
export function teamColors(shots, homeTeam) {
  const names = [...new Set(shots.map(s => s.team))]
  names.sort((a, b) => (a === homeTeam ? -1 : b === homeTeam ? 1 : 0))
  return Object.fromEntries(names.map((n, i) => [n, TEAM_PALETTE[Math.min(i, TEAM_PALETTE.length - 1)]]))
}

export const shotKey = s => `${s.match_id}-${s.id}`

// xg is null when any shot in the group is still pending.
export function statsFor(shots) {
  return {
    shots: shots.length,
    goals: shots.filter(s => s.outcome === 'goal').length,
    xg: shots.some(s => s.xg === null || s.xg === undefined || s.xg === '')
      ? null : shots.reduce((total, s) => total + Number(s.xg), 0),
  }
}
export const formatXg = v => (v === null || v === undefined ? 'xG pending' : v.toFixed(2))
export const formatSigned = v => (v === null ? 'xG pending' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(2)}`)
