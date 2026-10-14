import { useMemo } from 'react'
import { statsFor, formatXg } from '../utils/stats.js'

export default function Dashboard({ shots, team, notice, onUpload }) {
  const own = useMemo(() => shots.filter(s => s.team === team), [shots, team])
  const opponent = useMemo(() => shots.filter(s => s.team !== team), [shots, team])
  const homeStats = statsFor(own)
  const awayStats = statsFor(opponent)
  const playerStats = useMemo(() => [...new Set(own.map(s => s.player))].map(name => ({ name, ...statsFor(own.filter(s => s.player === name)) })), [own])
  const matches = new Set(shots.map(s => s.match_id)).size
  return <main><div className="page-title"><div><span className="eyebrow">TEAM OVERVIEW</span><h1>Coach Dashboard</h1><p>Farmingdale State • Sample match analytics</p></div><button className="primary" onClick={() => onUpload()}>↑ Upload match data</button></div>{notice && <div className="success">{notice}</div>}
        <div className="stats"><article><span>Matches</span><strong>{matches}</strong></article><article><span>Goals</span><strong>{homeStats.goals}</strong></article><article><span>Shots</span><strong>{homeStats.shots}</strong></article><article><span>Total xG</span><strong>{formatXg(homeStats.xg)}</strong></article></div>
        <div className="two-col"><section className="card"><h2>Match comparison</h2><p>Farmingdale State vs. Adelphi (mock data)</p><div className="comparison"><div><span>Farmingdale State</span><strong>{homeStats.goals} goals</strong><b>{formatXg(homeStats.xg)} xG</b></div><div><span>Opponent teams</span><strong>{awayStats.goals} goals</strong><b>{formatXg(awayStats.xg)} xG</b></div></div><p className="hint">Match Summary and Shot Map pages are being designed by Rory.</p></section><section className="card"><h2>Recent match</h2><p>Match ID: {shots[0]?.match_id || '—'}</p><div className="score">{homeStats.goals} – {awayStats.goals}</div><p>{team} vs. opponent</p><button className="secondary" onClick={() => onUpload()}>Upload another CSV</button></section></div>
        <section className="card"><h2>Player performance</h2><p>Totals calculated directly from mock shot records</p><div className="table-scroll"><table><thead><tr><th>Player</th><th>Shots</th><th>Goals</th><th>xG</th></tr></thead><tbody>{playerStats.map(p => <tr key={p.name}><td>{p.name}</td><td>{p.shots}</td><td>{p.goals}</td><td>{formatXg(p.xg)}</td></tr>)}</tbody></table></div></section>
      </main>
}
