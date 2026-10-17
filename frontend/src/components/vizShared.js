
 // Shared helpers for the Shot Map and Match Summary screens.
 // Shot format: id, match_id, player, team, minute, period, x, y,
 // outcome, body_part, assist_type, xg. Backend also returns xg_status.
 // Coordinates are 0–100 with attacks toward x=100.

export const OUTCOMES = ['goal', 'saved', 'blocked', 'off_target', 'post']

export const OUTCOME_LABELS = {
  goal: 'Goal',
  saved: 'Saved',
  blocked: 'Blocked',
  off_target: 'Off target',
  post: 'Hit the post',
}

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

const TEAM_PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#8a8984']

export function teamColors(shots, homeTeam) {
  const names = [...new Set(shots.map(s => s.team))]
  names.sort((a, b) => (a === homeTeam ? -1 : b === homeTeam ? 1 : 0))

  return Object.fromEntries(
    names.map((n, i) => [
      n,
      TEAM_PALETTE[Math.min(i, TEAM_PALETTE.length - 1)],
    ])
  )
}

export const shotKey = s => `${s.match_id}-${s.id}`

// Normalize backend and frontend xG statuses.
export function getXgStatus(shot) {
  const status = shot.xg_status

  if (status === 'unsupported' || status === 'outside_model') {
    return 'outside_model'
  }

  if (status === 'computed' || status === 'calculated') {
    return 'calculated'
  }

  if (
    shot.xg !== null &&
    shot.xg !== undefined &&
    shot.xg !== '' &&
    Number.isFinite(Number(shot.xg))
  ) {
    return 'calculated'
  }

  return 'pending'
}

// Use numeric xG only for shots with calculated values.
// Unsupported shots do not count as zero predictions.
// Pending shots are tracked separately.
export function statsFor(shots) {
  const calculated = shots.filter(
    s =>
      getXgStatus(s) === 'calculated' &&
      s.xg !== null &&
      s.xg !== undefined &&
      s.xg !== '' &&
      Number.isFinite(Number(s.xg))
  )

  return {
    shots: shots.length,

    goals: shots.filter(s => s.outcome === 'goal').length,

    xg: calculated.reduce(
      (total, s) => total + Number(s.xg),
      0
    ),

    calculatedShots: calculated.length,

    outsideModelShots: shots.filter(
      s => getXgStatus(s) === 'outside_model'
    ).length,

    pendingShots: shots.filter(
      s =>
        getXgStatus(s) === 'pending' ||
        (
          getXgStatus(s) === 'calculated' &&
          (s.xg === null ||
            s.xg === undefined ||
            s.xg === '' ||
            !Number.isFinite(Number(s.xg)))
        )
    ).length,
  }
}

export const formatXg = v =>
  v === null || v === undefined
    ? 'xG unavailable'
    : v.toFixed(2)

export const formatSigned = v =>
  v === null || v === undefined
    ? 'xG unavailable'
    : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(2)}`
