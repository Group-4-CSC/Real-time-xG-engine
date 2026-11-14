// Convert the matches API response into the shot records shared by all three views.
// This is a provisional contract until the backend matches endpoint is finalized.
export function shotsFromMatches(payload) {
  const matches = Array.isArray(payload) ? payload : payload?.matches
  if (!Array.isArray(matches)) {
    throw new Error('Matches API must return an array of matches (or { matches: [...] }).')
  }

  return matches.flatMap((match, matchIndex) => {
    if (!match || !Array.isArray(match.shots)) {
      throw new Error(`Match ${matchIndex + 1} is missing a shots array.`)
    }
    const matchId = match.match_id ?? match.id
    if (matchId == null || String(matchId).trim() === '') {
      throw new Error(`Match ${matchIndex + 1} is missing a match ID.`)
    }

    return match.shots.map((shot, shotIndex) => {
      if (!shot || !shot.team || !shot.player || !shot.outcome) {
        throw new Error(`Match ${matchId}, shot ${shotIndex + 1} is missing team, player, or outcome.`)
      }
      for (const key of ['x', 'y', 'minute', 'period']) {
        if (shot[key] == null || shot[key] === '' || !Number.isFinite(Number(shot[key]))) {
          throw new Error(`Match ${matchId}, shot ${shotIndex + 1} has invalid ${key}.`)
        }
      }
      const xg = shot.xg == null || shot.xg === '' ? null : Number(shot.xg)
      if (xg !== null && (!Number.isFinite(xg) || xg < 0 || xg > 1)) {
        throw new Error(`Match ${matchId}, shot ${shotIndex + 1} has invalid xG.`)
      }

      return {
        ...shot,
        id: shot.id ?? shot.shot_id ?? `${matchId}-S${shotIndex + 1}`,
        match_id: String(matchId),
        x: Number(shot.x),
        y: Number(shot.y),
        minute: Number(shot.minute),
        period: Number(shot.period),
        xg,
        xg_status: shot.xg_status ?? (xg == null ? 'pending' : 'calculated'),
      }
    })
  })
}
