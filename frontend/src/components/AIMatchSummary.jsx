import { useEffect, useState } from 'react'

export default function AIMatchSummary() {
  const [summary, setSummary] = useState('Loading prototype summary...')

  useEffect(() => {
    fetch('/api/ai/match-summary/')
      .then(response => {
        if (!response.ok) throw new Error('Summary request failed')
        return response.json()
      })
      .then(data => setSummary(data.summary))
      .catch(() => setSummary('AI summary is temporarily unavailable.'))
  }, [])

  return (
    <section className="card">
      <h2>AI Match Summary (Prototype)</h2>
      <p>{summary}</p>
      <p className="viz-note">
        Placeholder analysis only. Real AI integration is coming later.
      </p>
    </section>
  )
}
