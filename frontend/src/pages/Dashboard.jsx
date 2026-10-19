
import { useMemo } from 'react'
import { statsFor, xgText } from '../components/vizShared.js'

export default function Dashboard({ shots, team, teams, onTeamChange, notice, onUpload }) {
  const own = useMemo(() => shots.filter(s => s.team === team), [shots, team])
  const opponent = useMemo(() => shots.filter(s => s.team !== team), [shots, team])

  const homeStats = statsFor(own)
  const awayStats = statsFor(opponent)

  const playerStats = useMemo(
    () => [...new Set(own.map(s => s.player))].map(name => ({
      name,
      ...statsFor(own.filter(s => s.player === name)),
    })),
    [own]
  )

  const matches = new Set(shots.map(s => s.match_id)).size

  return (
    <main>
      <div className="page-title">
        <div>
          <span className="eyebrow">TEAM OVERVIEW</span>
          <h1>Coach Dashboard</h1>
          <p>{team} • Local demo analytics</p>
        </div>
        <div>
          <label>
            Team{' '}
            <select
              aria-label="Choose team"
              value={team}
              onChange={e => onTeamChange(e.target.value)}
            >
              {teams.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </label>{' '}
          <button className="primary" onClick={onUpload}>
            ↑ Upload match data
          </button>
        </div>
      </div>

      {notice && <div className="success">{notice}</div>}

      <div className="stats">
        <article>
          <span>Matches</span>
          <strong>{matches}</strong>
        </article>
        <article>
          <span>Goals</span>
          <strong>{homeStats.goals}</strong>
        </article>
        <article>
          <span>Shots</span>
          <strong>{homeStats.shots}</strong>
        </article>
        <article>
          <span>xG (box shots)</span>
          <strong>{xgText(homeStats)}</strong>
        </article>
      </div>

      <div className="two-col">
        <section className="card">
          <h2>Match comparison</h2>
          <p>{team} vs. opponents (demo data)</p>

          <div className="comparison">
            <div>
              <span>{team}</span>
              <strong>{homeStats.goals} goals</strong>
              <b>{xgText(homeStats)} xG (box shots)</b>
            </div>
            <div>
              <span>Opponent teams</span>
              <strong>{awayStats.goals} goals</strong>
              <b>{xgText(awayStats)} xG (box shots)</b>
            </div>
          </div>

          <p className="hint">
            Use Match Summary and Shot Map for detailed shot analysis.
          </p>
        </section>

        <section className="card">
          <h2>Recent match</h2>
          <p>Match ID: {shots[0]?.match_id || '—'}</p>
          <div className="score">
            {homeStats.goals} – {awayStats.goals}
          </div>
          <p>{team} vs. opponent</p>
          <button className="secondary" onClick={onUpload}>
            Upload another CSV
          </button>
        </section>
      </div>

      <section className="card">
        <h2>Player performance</h2>
        <p>Totals calculated from available shot records</p>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Player</th>
                <th>Shots</th>
                <th>Goals</th>
                <th>xG (box shots)</th>
              </tr>
            </thead>
            <tbody>
              {playerStats.map(p => (
                <tr key={p.name}>
                  <td>{p.name}</td>
                  <td>{p.shots}</td>
                  <td>{p.goals}</td>
                  <td>{xgText(p)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  )
}
