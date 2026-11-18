// A deterministic and clearly labeled fallback. Never invent match events.
function teamLine(team) {
  const coverage = team.xg_missing_shots > 0
    ? ` Only ${team.xg_calculated_shots} of ${team.shots} shots have xG.`
    : ''
  const xg = team.xg == null ? 'xG unavailable' : `${Number(team.xg).toFixed(2)} xG`
  return `${team.name}: ${team.goals} goals, ${team.shots} shots, ${xg}.${coverage}`
}

export function fallbackText(payload) {
  if (!payload || !Array.isArray(payload.teams) || payload.teams.length !== 2) {
    return 'The match statistics are unavailable right now.'
  }
  return `AI analysis is unavailable. Verified match statistics: ${payload.teams.map(teamLine).join(' ')}`
}

export function interpretAiResponse(data) {
  if (!data || typeof data.summary !== 'string' || !data.summary.trim() || data.is_placeholder === true) {
    throw new Error('AI response is missing a valid summary.')
  }
  const fallback = data.is_fallback === true || data.source === 'fallback'
  return {
    text: data.summary.trim(),
    mode: fallback ? 'fallback' : 'ai',
    message: fallback ? 'The AI provider was unavailable; this is a verified-statistics fallback.' : '',
  }
}

export async function loadAiSummary(payload, fetchSummary, signal) {
  try {
    const response = await fetchSummary(payload, { signal })
    return interpretAiResponse(response)
  } catch (error) {
    if (signal?.aborted || error?.name === 'AbortError') throw error
    return {
      text: fallbackText(payload),
      mode: 'fallback',
      message: 'The AI request failed or returned invalid output. Showing verified statistics instead.',
    }
  }
}
