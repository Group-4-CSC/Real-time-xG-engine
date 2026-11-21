import { useEffect, useState } from 'react'
import { getAiMatchSummary } from '../api.js'
import { loadAiSummary } from '../utils/aiSummary.js'

export default function AIMatchSummary({ matchId, half, teams }) {
  const teamsKey = JSON.stringify(teams)
  const requestKey = JSON.stringify([matchId, half, teamsKey])
  const valid = Boolean(matchId && Array.isArray(teams) && teams.length === 2
    && teams.every(team => Boolean(team.name)))

  const [result, setResult] = useState(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (!valid) return
    const controller = new AbortController()
    const payload = {
      match_id: matchId,
      half,
      teams: JSON.parse(teamsKey),
    }

    loadAiSummary(payload, getAiMatchSummary, controller.signal)
      .then(next => {
        if (!controller.signal.aborted) setResult({ ...next, key: requestKey, retryCount })
      })
      .catch(error => {
        // Expected when switching matches/halves or leaving the page.
        if (!controller.signal.aborted && error.name !== 'AbortError') {
          setResult({
            key: requestKey,
            retryCount,
            text: 'The match summary is unavailable.',
            mode: 'fallback',
            message: 'Unable to display match statistics.',
          })
        }
      })

    return () => controller.abort()
  }, [matchId, half, teamsKey, requestKey, valid, retryCount])

  const current = result?.key === requestKey && result?.retryCount === retryCount
  const loading = valid && !current
  const mode = current ? result.mode : null

  return (
    <section className="card" aria-label="AI Match Summary">
      <div className="ai-summary-heading">
        <h2>AI Match Summary</h2>
        <span className={`ai-summary-label ${mode === 'fallback' ? 'ai-summary-fallback' : ''}`}>
          {loading ? 'Loading' : mode === 'ai' ? 'AI-generated' : mode === 'fallback' ? 'Fallback — match stats only' : 'Unavailable'}
        </span>
      </div>
      {!valid ? (
        <p role="status">Choose a match with two teams to view the summary.</p>
      ) : loading ? (
        <p role="status" aria-live="polite">Generating the match summary...</p>
      ) : (
        <>
          <p role="status" aria-live="polite">{result.text}</p>
          {result.message && <p className="viz-note" role="alert">{result.message}</p>}
        </>
      )}
      <p className="viz-note">
        {mode === 'ai' ? 'AI-generated analysis of the selected match statistics. Check the figures above for accuracy.'
          : 'The fallback uses supplied match statistics and does not make AI-generated claims.'}
      </p>
      {valid && <button className="secondary" type="button" disabled={loading}
        onClick={() => setRetryCount(count => count + 1)}>
        {loading ? 'Generating...' : 'Retry summary'}
      </button>}
    </section>
  )
}
