
import { useEffect, useState } from 'react'

export default function AIMatchSummary({ matchId, half, teams }) {
  const [summary, setSummary] = useState('Generating AI match summary...')

  const teamsKey = JSON.stringify(teams)

  useEffect(() => {
    if (!matchId || !teams || teams.length !== 2) return

    setSummary('Generating AI match summary...')

    const controller = new AbortController()

    fetch('/api/ai/match-summary/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        match_id: matchId,
        half: half,
        teams: JSON.parse(teamsKey)
      })
    })
      .then(response => {
        if (!response.ok) throw new Error('Summary request failed')
        return response.json()
      })
      .then(data => setSummary(data.summary))
      .catch(error => {
        if (error.name !== 'AbortError') {
          setSummary('AI summary is temporarily unavailable.')
        }
      })

    return () => controller.abort()
  }, [matchId, half, teamsKey])

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
