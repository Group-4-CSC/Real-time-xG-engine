
import { useEffect, useState } from 'react'

const LOADING = 'Generating AI match summary...'
const UNAVAILABLE = 'AI summary is temporarily unavailable.'

export default function AIMatchSummary({ matchId, half, teams }) {
  const teamsKey = JSON.stringify(teams)
  const requestKey = JSON.stringify([matchId, half, teamsKey])
  const valid = Boolean(matchId && Array.isArray(teams) && teams.length === 2)

  const [result, setResult] = useState(null)

  useEffect(() => {
    if (!valid) return

    const controller = new AbortController()

    fetch('/api/ai/match-summary/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        match_id: matchId,
        half,
        teams: JSON.parse(teamsKey)
      })
    })
      .then(response => {
        if (!response.ok) throw new Error('Summary request failed')
        return response.json()
      })
      .then(data => {
        if (!controller.signal.aborted) {
          setResult({ key: requestKey, text: data.summary })
        }
      })
      .catch(error => {
        if (error.name !== 'AbortError' && !controller.signal.aborted) {
          setResult({ key: requestKey, text: UNAVAILABLE })
        }
      })

    return () => controller.abort()
  }, [matchId, half, teamsKey, requestKey, valid])

  const summary = !valid
    ? UNAVAILABLE
    : result?.key === requestKey
      ? result.text
      : LOADING

  return (
    <section className="card">
      <h2>AI Match Summary</h2>
      <p>{summary}</p>
      <p className="viz-note">
        AI-generated analysis based on available match statistics.
      </p>
    </section>
  )
}
