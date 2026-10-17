// Shared helpers for the Shot Map and Match Summary screens.
// Shot format (agreed by the team): id, match_id, player, team, minute, period,
// x, y, outcome, body_part, assist_type, xg. x and y run 0-100, every shot attacks toward x = 100.
// xg may be null. The API also sends xg_status: 'calculated' | 'unsupported'.
// null + 'unsupported' = outside the xG model (shot not supported by the model): shown as "no xG", never as 0.
// null with no status = the model has not run yet: shown as "xG pending".

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

// 'calculated' (has a number), 'unsupported' (outside the model) or 'pending' (model not run yet).
// 'outside_model' is accepted as an older name for 'unsupported'.
export function xgStatus(s) {
  if (typeof s.xg === 'number' && Number.isFinite(s.xg)) return 'calculated'
  if (s.xg_status === 'unsupported' || s.xg_status === 'outside_model') return 'unsupported'
  return 'pending'
}
export const hasXg = s => xgStatus(s) === 'calculated'
export function xgShotText(s) {
  const st = xgStatus(s)
  return st === 'calculated' ? `xG ${s.xg.toFixed(2)}` : st === 'unsupported' ? 'No xG (outside the model)' : 'xG pending'
}
export function xgCellText(s) {
  const st = xgStatus(s)
  return st === 'calculated' ? s.xg.toFixed(2) : st === 'unsupported' ? '–' : 'pending'
}

// xg is the sum over shots that have an xG value (null if none do). goalsCalc counts goals among
// those same shots, so "goals minus xG" compares like with like. calculated < shots means partial.
export function statsFor(shots) {
  const calc = shots.filter(hasXg)
  return {
    shots: shots.length,
    goals: shots.filter(s => s.outcome === 'goal').length,
    calculated: calc.length,
    unsupported: shots.filter(s => xgStatus(s) === 'unsupported').length,
    pending: shots.filter(s => xgStatus(s) === 'pending').length,
    goalsCalc: calc.filter(s => s.outcome === 'goal').length,
    xg: calc.length ? calc.reduce((total, s) => total + s.xg, 0) : null,
  }
}
export const formatXg = v => (v === null || v === undefined ? 'xG pending' : v.toFixed(2))
// Headline text for a group's xG: a number, or why there is none.
export const xgText = st => (st.xg !== null ? st.xg.toFixed(2) : st.pending > 0 ? 'xG pending' : st.unsupported > 0 ? 'No xG' : '–')
// Short note under a partial total, e.g. "xG from 12 of 20 shots".
export function coverageText(st) {
  if (st.shots === 0 || st.calculated === st.shots) return ''
  const parts = []
  if (st.unsupported > 0) parts.push(`${st.unsupported} outside the model`)
  if (st.pending > 0) parts.push(`${st.pending} pending`)
  return `xG from ${st.calculated} of ${st.shots} shots (${parts.join(', ')})`
}
// Label for a headline that mixes in partial totals. '' when every shot has an xG value.
export function xgScopeLabel(...groups) {
  if (groups.every(g => g.calculated === g.shots)) return ''
  return groups.some(g => g.unsupported > 0) ? 'supported shots only' : 'some shots pending'
}
export const formatSigned = v => (v === null ? 'xG pending' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(2)}`)
