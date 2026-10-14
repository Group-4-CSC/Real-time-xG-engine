import { useMemo, useState } from 'react'
import './viz.css'
import { HALF_OPTIONS, OUTCOMES, formatXg, outcomeLabel, periodMatches, prettify, shotKey, statsFor, teamColors } from './vizShared.js'
import Marker from './Marker.jsx'

// Half pitch, attacking goal at the top. Real pitch is about 105 m x 68 m, so
// x (50-100) maps to the 52.5 m length and y (0-100) to the 68 m width.
const SCALE = 9, PAD = 22
const W = 68 * SCALE, H = 52.5 * SCALE
const VB_W = W + PAD * 2, VB_H = H + PAD * 2 + 6
const LINE = '#b9c4b6'
const px = y => PAD + (y / 100) * W
const py = x => PAD + 6 + ((100 - x) / 50) * H

function Pitch() {
  const ox = PAD, oy = PAD + 6
  const boxW = 40.32 * SCALE, boxH = 16.5 * SCALE, sixW = 18.32 * SCALE, sixH = 5.5 * SCALE
  const goalW = 7.32 * SCALE, spotY = oy + 11 * SCALE, r = 9.15 * SCALE
  const dy = boxH - 11 * SCALE, dx = Math.sqrt(r * r - dy * dy)
  const mid = ox + W / 2
  const stroke = { fill: 'none', stroke: LINE, strokeWidth: 2 }
  return <g>
    <rect x={ox} y={oy} width={W} height={H} rx="10" fill="#eef3ec" stroke={LINE} strokeWidth="2" />
    <rect x={mid - boxW / 2} y={oy} width={boxW} height={boxH} {...stroke} />
    <rect x={mid - sixW / 2} y={oy} width={sixW} height={sixH} {...stroke} />
    <rect x={mid - goalW / 2} y={oy - 6} width={goalW} height="6" {...stroke} />
    <path d={`M ${mid - dx} ${oy + boxH} A ${r} ${r} 0 0 0 ${mid + dx} ${oy + boxH}`} {...stroke} />
    <circle cx={mid} cy={spotY} r="2.5" fill={LINE} />
    <path d={`M ${mid - r} ${oy + H} A ${r} ${r} 0 0 1 ${mid + r} ${oy + H}`} {...stroke} />
  </g>
}

export default function ShotMap({ shots, homeTeam, onBack }) {
  const matchIds = useMemo(() => [...new Set(shots.map(s => s.match_id))], [shots])
  const [matchId, setMatchId] = useState(matchIds[0] ?? '')
  const [team, setTeam] = useState('all')
  const [player, setPlayer] = useState('all')
  const [half, setHalf] = useState('all')
  const [outcome, setOutcome] = useState('all')
  const [activeKey, setActiveKey] = useState(null)

  const currentMatch = matchIds.includes(matchId) ? matchId : matchIds[0]
  const matchShots = useMemo(() => shots.filter(s => s.match_id === currentMatch), [shots, currentMatch])
  const colors = useMemo(() => teamColors(matchShots, homeTeam), [matchShots, homeTeam])
  const teams = Object.keys(colors)
  const players = useMemo(
    () => [...new Set(matchShots.filter(s => team === 'all' || s.team === team).map(s => s.player))],
    [matchShots, team],
  )
  const visible = useMemo(() => matchShots
    .filter(s => (team === 'all' || s.team === team) && (player === 'all' || s.player === player)
      && periodMatches(s.period, half) && (outcome === 'all' || s.outcome === outcome))
    .sort((a, b) => a.minute - b.minute), [matchShots, team, player, half, outcome])
  const plotted = visible.filter(s => s.x >= 50)
  const hiddenCount = visible.length - plotted.length
  const active = plotted.find(s => shotKey(s) === activeKey)
  const filtersOn = team !== 'all' || player !== 'all' || half !== 'all' || outcome !== 'all'

  function reset() { setTeam('all'); setPlayer('all'); setHalf('all'); setOutcome('all') }
  function changeTeam(value) { setTeam(value); setPlayer('all') }

  const tipLeft = active ? (px(active.y) / VB_W) * 100 : 0
  const tipTop = active ? (py(active.x) / VB_H) * 100 : 0

  return <main>
    <button className="back" onClick={onBack}>← Back to Dashboard</button>
    <div className="page-title"><div>
      <span className="eyebrow">MATCH ANALYSIS</span><h1>Shot Map</h1>
      <p>Every shot shown attacking the goal at the top. Marker size is the shot's xG.</p>
    </div></div>

    <div className="viz-filters">
      {matchIds.length > 1 && <label>Match<select value={currentMatch} onChange={e => { setMatchId(e.target.value); reset() }}>{matchIds.map(m => <option key={m} value={m}>{m}</option>)}</select></label>}
      <label>Team<select value={team} onChange={e => changeTeam(e.target.value)}><option value="all">Both teams</option>{teams.map(t => <option key={t} value={t}>{t}</option>)}</select></label>
      <label>Player<select value={player} onChange={e => setPlayer(e.target.value)}><option value="all">All players</option>{players.map(p => <option key={p} value={p}>{p}</option>)}</select></label>
      <label>Half<select value={half} onChange={e => setHalf(e.target.value)}>{HALF_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select></label>
      <label>Outcome<select value={outcome} onChange={e => setOutcome(e.target.value)}><option value="all">All outcomes</option>{OUTCOMES.map(o => <option key={o} value={o}>{outcomeLabel(o)}</option>)}</select></label>
      <button className="secondary" onClick={reset} disabled={!filtersOn}>Reset</button>
    </div>

    <div className="viz-layout">
      <section className="card">
        {matchShots.length === 0 ? <div className="viz-empty">No shots yet. Upload a match CSV to see the shot map.</div> : <>
          <div className="viz-pitch-wrap">
            <svg viewBox={`0 0 ${VB_W} ${VB_H}`} role="img" aria-label={`Shot map showing ${plotted.length} shots`}>
              <Pitch />
              {plotted.map(s => {
                const cx = px(s.y), cy = py(s.x)
                const label = `${s.player}, minute ${s.minute}, ${outcomeLabel(s.outcome)}, ${s.xg == null ? 'xG pending' : `xG ${s.xg.toFixed(2)}`}`
                return <g key={shotKey(s)} className="viz-marker" tabIndex={0} role="img" aria-label={label}
                  onMouseEnter={() => setActiveKey(shotKey(s))} onMouseLeave={() => setActiveKey(null)}
                  onFocus={() => setActiveKey(shotKey(s))} onBlur={() => setActiveKey(null)}>
                  <circle className="viz-focus" cx={cx} cy={cy} r="26" />
                  <Marker cx={cx} cy={cy} outcome={s.outcome} xg={s.xg} color={colors[s.team]} />
                </g>
              })}
            </svg>
            {active && <div className="viz-tooltip" style={tipLeft > 60
              ? { right: `${100 - tipLeft + 4}%`, top: `${Math.min(tipTop, 70)}%` }
              : { left: `${tipLeft + 4}%`, top: `${Math.min(tipTop, 70)}%` }}>
              <strong><span className="viz-swatch" style={{ background: colors[active.team] }} />{active.player} · {active.minute}'</strong>
              <div>{outcomeLabel(active.outcome)}</div>
              <div>{active.xg == null ? 'xG pending' : `xG ${active.xg.toFixed(2)}`}</div>
              <div className="muted">{prettify(active.body_part)}{active.assist_type && active.assist_type !== 'none' ? ` · ${prettify(active.assist_type)}` : ''} · half {active.period}</div>
              <div className="muted">x {active.x} · y {active.y}</div>
            </div>}
            {plotted.length === 0 && <div className="viz-empty">No shots match these filters.</div>}
          </div>
          <p className="viz-note">Own half is below the pitch edge. y = 0 is the left side when facing the goal.{hiddenCount > 0 ? ` ${hiddenCount} shot${hiddenCount > 1 ? 's' : ''} from the own half ${hiddenCount > 1 ? 'are' : 'is'} not drawn but listed in the table.` : ''}</p>
        </>}
      </section>

      <div>
        <section className="card">
          <h2>Legend</h2>
          <div className="viz-teams">{teams.map(t => <span key={t}><i className="viz-swatch" style={{ background: colors[t] }} />{t}</span>)}</div>
          <div className="viz-legend">
            {OUTCOMES.map(o => <div className="viz-legend-row" key={o}>
              <svg viewBox="0 0 26 26" aria-hidden="true"><Marker cx={13} cy={13} outcome={o} xg={0.04} color="#52514e" size={7} /></svg>{outcomeLabel(o)}
            </div>)}
          </div>
          <div className="viz-sizes" aria-label="Marker size scale">
            {[0.05, 0.15, 0.4].map(v => <div key={v}><svg width="48" height="48" viewBox="-24 -24 48 48" aria-hidden="true"><circle r={7 + Math.sqrt(v) * 20} fill="#8a8984" stroke="#fff" strokeWidth="2" /></svg>{v.toFixed(2)} xG</div>)}
          </div>
          <p className="viz-note">Faded markers have xG pending.</p>
        </section>

        <section className="card">
          <h2>Shots in view ({visible.length})</h2>
          <div className="viz-teams">{teams.map(t => { const st = statsFor(visible.filter(s => s.team === t)); return <span key={t}><i className="viz-swatch" style={{ background: colors[t] }} />{st.shots} shots · {st.goals} goals · {formatXg(st.xg)}{st.xg == null ? '' : ' xG'}</span> })}</div>
          <div className="table-scroll"><table>
            <thead><tr><th>Min</th><th>Player</th><th>Outcome</th><th>xG</th></tr></thead>
            <tbody>{visible.map(s => <tr key={shotKey(s)}>
              <td>{s.minute}'</td>
              <td><span className="viz-cell"><i className="viz-swatch" style={{ background: colors[s.team] }} />{s.player}</span></td>
              <td>{outcomeLabel(s.outcome)}</td>
              <td>{s.xg == null ? 'pending' : s.xg.toFixed(2)}</td>
            </tr>)}</tbody>
          </table></div>
        </section>
      </div>
    </div>
  </main>
}
