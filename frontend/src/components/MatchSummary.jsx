import { useMemo, useState } from 'react'
import './viz.css'
import { HALF_OPTIONS, coverageText, formatSigned, formatXg, hasXg, periodMatches, shotKey, statsFor, teamColors, xgScopeLabel, xgStatus, xgText } from './vizShared.js'
import Marker from './Marker.jsx'

// Cumulative xG chart geometry
const CW = 760, CH = 330, ML = 52, MR = 128, MT = 20, MB = 40
const IW = CW - ML - MR, IH = CH - MT - MB

function Timeline({ shots, teams, colors }) {
  const usable = shots.filter(hasXg)
  const unsupported = shots.filter(s => xgStatus(s) === 'unsupported').length
  const pending = shots.filter(s => xgStatus(s) === 'pending').length
  const lastMinute = Math.max(90, ...shots.map(s => s.minute))
  const series = teams.map(name => {
    let total = 0
    const events = usable.filter(s => s.team === name).sort((a, b) => a.minute - b.minute)
    const points = [[0, 0]]
    events.forEach(s => { points.push([s.minute, total]); total += s.xg; points.push([s.minute, total]) })
    points.push([lastMinute, total])
    return { name, total, points, events }
  })
  const top = Math.max(0.25, ...series.map(s => s.total))
  const yMax = Math.ceil(top * 4) / 4
  const sx = m => ML + (m / lastMinute) * IW
  const sy = v => MT + IH - (v / yMax) * IH
  const ticks = Array.from({ length: Math.floor(yMax / 0.25) + 1 }, (_, i) => i * 0.25)
  const minutes = [0, 15, 30, 45, 60, 75, 90].filter(m => m <= lastMinute)
  if (usable.length === 0) return <div className="viz-empty">{pending > 0 && unsupported > 0 ? `No shot here has an xG to plot: ${unsupported} outside the xG model and ${pending} pending until the model runs.` : pending > 0 ? 'xG is pending for every shot, so the timeline will appear once the model has run.' : 'None of these shots are inside the xG model, so there is no timeline.'}</div>
  // keep the two end labels from overlapping
  const labelY = series.map(s => sy(s.total) + 4)
  if (labelY.length === 2 && Math.abs(labelY[0] - labelY[1]) < 16) { const lower = labelY[0] > labelY[1] ? 0 : 1; labelY[lower] += 16 - Math.abs(labelY[0] - labelY[1]) }
  return <>
    <svg viewBox={`0 0 ${CW} ${CH}`} role="img" aria-label={`Cumulative xG by minute. ${series.map(s => `${s.name} ${s.total.toFixed(2)}`).join(', ')}`}>
      {ticks.map(v => <g key={v}><line x1={ML} x2={ML + IW} y1={sy(v)} y2={sy(v)} stroke="#e3e4e1" /><text x={ML - 10} y={sy(v) + 4} textAnchor="end" fontSize="12" fill="#52514e">{v.toFixed(2)}</text></g>)}
      {minutes.map(m => <text key={m} x={sx(m)} y={MT + IH + 22} textAnchor="middle" fontSize="12" fill="#52514e">{m}'</text>)}
      <line x1={sx(45)} x2={sx(45)} y1={MT} y2={MT + IH} stroke="#8a8984" strokeDasharray="4 4" />
      <text x={sx(45) + 6} y={MT + 12} fontSize="11" fill="#8a8984">HT</text>
      {series.map((s, i) => <g key={s.name}>
        <path d={s.points.map(([m, v], j) => `${j ? 'L' : 'M'} ${sx(m).toFixed(1)} ${sy(v).toFixed(1)}`).join(' ')} fill="none" stroke={colors[s.name]} strokeWidth="2.5" strokeLinejoin="round" />
        {s.events.map(e => {
          const cum = s.events.filter(x => x.minute < e.minute || (x.minute === e.minute && shotKey(x) <= shotKey(e))).reduce((t, x) => t + x.xg, 0)
          return e.outcome === 'goal'
            ? <Marker key={shotKey(e)} cx={sx(e.minute)} cy={sy(cum)} outcome="goal" xg={0.1} color={colors[s.name]} size={8} />
            : <circle key={shotKey(e)} cx={sx(e.minute)} cy={sy(cum)} r="3.5" fill={colors[s.name]} stroke="#fff" strokeWidth="1.5" />
        })}
        <text x={ML + IW + 8} y={labelY[i]} fontSize="12" fontWeight="600" fill="#14223a">{s.name.split(' ')[0]} {s.total.toFixed(2)}</text>
      </g>)}
    </svg>
    <p className="viz-note">Stars are goals. {unsupported + pending > 0 ? `Left out: ${[unsupported > 0 && `${unsupported} shot${unsupported > 1 ? 's' : ''} outside the xG model`, pending > 0 && `${pending} with xG pending`].filter(Boolean).join(' and ')}.` : 'Each step is a shot.'}</p>
  </>
}

export default function MatchSummary({ shots, homeTeam, onOpenShotMap, onBack }) {
  const matchIds = useMemo(() => [...new Set(shots.map(s => s.match_id))], [shots])
  const [matchId, setMatchId] = useState(matchIds[0] ?? '')
  const [half, setHalf] = useState('all')
  const currentMatch = matchIds.includes(matchId) ? matchId : matchIds[0]
  const matchShots = useMemo(() => shots.filter(s => s.match_id === currentMatch), [shots, currentMatch])
  const colors = useMemo(() => teamColors(matchShots, homeTeam), [matchShots, homeTeam])
  const teams = Object.keys(colors)
  const home = teams.includes(homeTeam) ? homeTeam : teams[0]
  const away = teams.find(t => t !== home)

  const filtered = useMemo(() => matchShots.filter(s => periodMatches(s.period, half)), [matchShots, half])
  const full = { home: statsFor(matchShots.filter(s => s.team === home)), away: statsFor(matchShots.filter(s => s.team === away)) }
  const h = statsFor(filtered.filter(s => s.team === home))
  const a = statsFor(filtered.filter(s => s.team === away))
  const xgd = h.xg === null || a.xg === null ? null : h.xg - a.xg
  const diff = (goals, xg) => (xg === null ? null : goals - xg)
  const scope = xgScopeLabel(h, a)

  const players = useMemo(() => {
    const names = [...new Set(filtered.map(s => `${s.team}|${s.player}`))]
    return names.map(key => {
      const [t, name] = key.split('|')
      return { team: t, name, ...statsFor(filtered.filter(s => s.team === t && s.player === name)) }
    }).sort((x, y) => (x.team === home ? -1 : 1) - (y.team === home ? -1 : 1) || (y.xg ?? -1) - (x.xg ?? -1))
  }, [filtered, home])

  if (matchShots.length === 0) return <main>
    <button className="back" onClick={onBack}>← Back to Dashboard</button>
    <div className="page-title"><div><span className="eyebrow">MATCH ANALYSIS</span><h1>Match Summary</h1></div></div>
    <section className="card"><div className="viz-empty">No match data yet. Upload a match CSV to see the summary.</div></section>
  </main>

  const better = xgd === null ? '' : Math.abs(xgd) < 0.005 ? 'Both teams created chances of similar quality.' : `${xgd > 0 ? home : away} created better chances (${formatXg(xgd > 0 ? h.xg : a.xg)} vs ${formatXg(xgd > 0 ? a.xg : h.xg)} xG).`
  const barMax = 0.5, barHalf = 150
  const barLen = xgd === null ? 0 : Math.min(Math.abs(xgd) / barMax, 1) * barHalf

  return <main>
    <button className="back" onClick={onBack}>← Back to Dashboard</button>
    <div className="page-title"><div>
      <span className="eyebrow">MATCH ANALYSIS</span><h1>Match Summary</h1><p>Match ID: {currentMatch}</p>
    </div>
    <div className="viz-filters" style={{ marginBottom: 0 }}>
      {matchIds.length > 1 && <label>Match<select value={currentMatch} onChange={e => setMatchId(e.target.value)}>{matchIds.map(m => <option key={m} value={m}>{m}</option>)}</select></label>}
      <label>Half<select value={half} onChange={e => setHalf(e.target.value)}>{HALF_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select></label>
    </div></div>

    <section className="card viz-score" aria-label="Final score">
      <div><div className="team"><i className="viz-swatch" style={{ background: colors[home] }} />{home}</div><div className="goals">{full.home.goals}</div></div>
      <div className="dash">–</div>
      <div><div className="team">{away && <i className="viz-swatch" style={{ background: colors[away] }} />}{away ?? 'Opponent'}</div><div className="goals">{full.away.goals}</div></div>
    </section>

    <div className="viz-kpis">
      <article className="viz-kpi"><h3>Expected goals (xG){scope && <small className="viz-scope"> · {scope}</small>}</h3><div className="viz-kpi-row"><div><span><i className="viz-swatch" style={{ background: colors[home] }} />{home}</span><strong>{xgText(h)}</strong>{coverageText(h) && <small className="viz-cover">{coverageText(h)}</small>}</div><div><span>{away && <i className="viz-swatch" style={{ background: colors[away] }} />}{away ?? 'Opponent'}</span><strong>{xgText(a)}</strong>{coverageText(a) && <small className="viz-cover">{coverageText(a)}</small>}</div></div></article>
      <article className="viz-kpi"><h3>Shots</h3><div className="viz-kpi-row"><div><span><i className="viz-swatch" style={{ background: colors[home] }} />{home}</span><strong>{h.shots}</strong></div><div><span>{away && <i className="viz-swatch" style={{ background: colors[away] }} />}{away ?? 'Opponent'}</span><strong>{a.shots}</strong></div></div></article>
      <article className="viz-kpi"><h3>Goals minus xG{scope && <small className="viz-scope"> · {scope}</small>}</h3><div className="viz-kpi-row"><div><span><i className="viz-swatch" style={{ background: colors[home] }} />{home}</span><strong>{formatSigned(diff(h.goalsCalc, h.xg))}</strong></div><div><span>{away && <i className="viz-swatch" style={{ background: colors[away] }} />}{away ?? 'Opponent'}</span><strong>{formatSigned(diff(a.goalsCalc, a.xg))}</strong></div></div></article>
    </div>

    <section className="card">
      <h2>xG differential (xGD){scope && <small className="viz-scope"> · {scope}</small>}</h2>
      <div className="viz-xgd">
        <div className="value">{formatSigned(xgd)}</div>
        <p>{xgd === null ? 'xGD needs an xG value for at least one shot from each team.' : `${better} xGD is ${home}'s xG minus ${away ?? 'the opponent'}'s xG.`}</p>
        {xgd !== null && <svg viewBox="0 0 320 40" role="img" aria-label={`xGD ${formatSigned(xgd)}, favoring ${xgd >= 0 ? home : away}`}>
          <line x1="160" x2="160" y1="4" y2="36" stroke="#8a8984" strokeWidth="1.5" />
          <rect x={xgd >= 0 ? 160 : 160 - barLen} y="10" width={barLen} height="20" rx="4" fill={colors[xgd >= 0 ? home : away] ?? '#2a78d6'} />
        </svg>}
      </div>
      <p className="viz-note">Bar scale: full width = 0.50 xGD. Right favors {home}, left favors {away ?? 'the opponent'}. The half filter above applies to the numbers on this page, not the scoreline or timeline.</p>
    </section>

    <div className="viz-wide" style={{ marginTop: 16 }}>
      <section className="card viz-timeline">
        <h2>Cumulative xG by minute</h2>
        <p>How each team's chance quality built up through the match.</p>
        <Timeline shots={matchShots} teams={teams} colors={colors} />
      </section>
      <section className="card">
        <h2>Players: goals vs xG</h2>
        <div className="table-scroll"><table>
          <thead><tr><th>Player</th><th>Shots</th><th>xG</th><th>Goals</th></tr></thead>
          <tbody>{players.map(p => {
            const d = diff(p.goalsCalc, p.xg)
            return <tr key={`${p.team}-${p.name}`}>
              <td><span className="viz-cell"><i className="viz-swatch" style={{ background: colors[p.team] }} />{p.name}</span></td>
              <td>{p.shots}</td><td title={p.xg === null && p.pending === 0 ? 'Outside the xG model' : undefined}>{p.xg === null ? (p.pending > 0 ? 'pending' : '–') : p.xg.toFixed(2)}{p.xg !== null && p.calculated < p.shots && <small className="viz-pos" style={{ color: 'var(--muted)' }}> *</small>}</td>
              <td>{p.goals}{d !== null && d !== 0 && <small className={d > 0 ? 'viz-pos' : 'viz-neg'}> ({formatSigned(d)})</small>}</td>
            </tr>
          })}</tbody>
        </table></div>
        <p className="viz-note">The number in brackets is goals minus xG: positive means scoring more than the chances suggest.{players.some(p => p.unsupported > 0) ? ' A dash means the shots are outside the xG model; * means some of the player\u2019s shots are.' : ''}</p>
        <button className="secondary" style={{ width: '100%', marginTop: 16 }} onClick={onOpenShotMap}>View full shot map →</button>
      </section>
    </div>
  </main>
}
