import { useMemo, useRef, useState } from 'react'
import './App.css'

const columns = ['id', 'match_id', 'player', 'team', 'minute', 'period', 'x', 'y', 'outcome', 'body_part', 'assist_type', 'xg']
const sampleShots = [
  { id: 'S1', match_id: 'M1', player: 'J. Rivera', team: 'Farmingdale State', minute: 12, period: 1, x: 88, y: 48, outcome: 'goal', body_part: 'right_foot', assist_type: 'through_ball', xg: 0.31 },
  { id: 'S2', match_id: 'M1', player: 'J. Rivera', team: 'Farmingdale State', minute: 29, period: 1, x: 76, y: 62, outcome: 'saved', body_part: 'left_foot', assist_type: 'cross', xg: 0.08 },
  { id: 'S3', match_id: 'M1', player: 'M. Chen', team: 'Farmingdale State', minute: 34, period: 1, x: 91, y: 50, outcome: 'goal', body_part: 'right_foot', assist_type: 'pass', xg: 0.42 },
  { id: 'S4', match_id: 'M1', player: 'M. Chen', team: 'Farmingdale State', minute: 41, period: 1, x: 67, y: 36, outcome: 'off_target', body_part: 'left_foot', assist_type: 'none', xg: 0.03 },
  { id: 'S5', match_id: 'M1', player: 'A. Reyes', team: 'Adelphi', minute: 52, period: 2, x: 74, y: 36, outcome: 'blocked', body_part: 'right_foot', assist_type: 'pass', xg: 0.09 },
  { id: 'S6', match_id: 'M1', player: 'A. Reyes', team: 'Adelphi', minute: 67, period: 2, x: 84, y: 52, outcome: 'post', body_part: 'right_foot', assist_type: 'cross', xg: 0.22 },
  { id: 'S7', match_id: 'M1', player: 'D. Park', team: 'Adelphi', minute: 73, period: 2, x: 79, y: 41, outcome: 'saved', body_part: 'left_foot', assist_type: 'through_ball', xg: 0.07 },
  { id: 'S8', match_id: 'M1', player: 'D. Park', team: 'Adelphi', minute: 88, period: 2, x: 93, y: 49, outcome: 'goal', body_part: 'right_foot', assist_type: 'pass', xg: 0.35 },
]
const allowedOutcomes = ['goal', 'saved', 'blocked', 'off_target', 'post']
function statsFor(shots) {
  return {
    shots: shots.length,
    goals: shots.filter(s => s.outcome === 'goal').length,
    xg: shots.some(s => s.xg === null || s.xg === undefined || s.xg === '')
      ? null : shots.reduce((total, s) => total + Number(s.xg), 0),
  }
}
const formatXg = value => value === null ? 'xG pending' : value.toFixed(2)

// Supports quoted CSV fields, including commas inside quotes.
function parseCsv(text) {
  const rows = []
  let row = [], field = '', quoted = false
  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++ } else quoted = !quoted
    } else if (char === ',' && !quoted) { row.push(field.trim()); field = '' }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i++
      row.push(field.trim()); if (row.some(Boolean)) rows.push(row)
      row = []; field = ''
    } else field += char
  }
  if (quoted) throw new Error('The CSV contains an unclosed quotation mark.')
  row.push(field.trim()); if (row.some(Boolean)) rows.push(row)
  if (rows.length < 2) throw new Error('The CSV must contain a header and at least one shot.')
  const headers = rows[0].map(h => h.toLowerCase())
  const missing = columns.filter(c => !headers.includes(c))
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(', ')}`)
  const shots = rows.slice(1).map((values, i) => {
    if (values.length !== headers.length) throw new Error(`Row ${i + 2} has the wrong number of columns.`)
    const s = Object.fromEntries(headers.map((h, j) => [h, values[j]]))
    for (const key of ['x', 'y', 'minute', 'period']) {
      if (s[key] === '' || !Number.isFinite(Number(s[key]))) throw new Error(`Invalid ${key} on row ${i + 2}.`)
      s[key] = Number(s[key])
    }
    if (s.x < 0 || s.x > 100 || s.y < 0 || s.y > 100) throw new Error(`Coordinates must be 0–100 (row ${i + 2}).`)
    if (!allowedOutcomes.includes(s.outcome)) throw new Error(`Invalid outcome on row ${i + 2}.`)
    if (s.xg === '') s.xg = null
    else {
      s.xg = Number(s.xg)
      if (!Number.isFinite(s.xg) || s.xg < 0 || s.xg > 1) throw new Error(`xg must be 0–1 or blank (row ${i + 2}).`)
    }
    return s
  })
  return shots
}

function App() {
  const [page, setPage] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [shots, setShots] = useState(sampleShots)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [notice, setNotice] = useState('')
  const fileInput = useRef(null)
  const team = 'Farmingdale State'
  const own = useMemo(() => shots.filter(s => s.team === team), [shots])
  const opponent = useMemo(() => shots.filter(s => s.team !== team), [shots])
  const homeStats = statsFor(own)
  const awayStats = statsFor(opponent)
  const playerStats = useMemo(() => [...new Set(own.map(s => s.player))].map(name => ({ name, ...statsFor(own.filter(s => s.player === name)) })), [own])
  const matches = new Set(shots.map(s => s.match_id)).size

  function login(e) {
    e.preventDefault()
    if (!email.trim() || !password.trim()) return setLoginError('Enter an email and password.')
    if (!email.includes('@')) return setLoginError('Enter a valid email address.')
    setLoginError(''); setPage('dashboard')
  }
  async function loadFile(file) {
    if (!file) return
    setUploadError(''); setPreview(null)
    if (!file.name.toLowerCase().endsWith('.csv')) return setUploadError('Please choose a .csv file.')
    if (file.size > 10 * 1024 * 1024) return setUploadError('File must be under 10 MB.')
    try { setPreview(parseCsv(await file.text())); setFileName(file.name) }
    catch (e) { setUploadError(e.message) }
  }
  function importPreview() {
    if (!preview) return
    setShots(preview); setNotice(`${preview.length} shots imported into this local demo.`)
    setPage('dashboard')
  }
  function navTo(target) { setNotice(''); setPage(target) }

  if (page === 'login') return <div className="login">
    <div className="login-brand"><div className="brand bright">◉ xG <strong>Insights</strong></div><div className="login-message"><span className="eyebrow">BUILT FOR THE TOUCHLINE</span><h1>Turn every shot into a smarter decision.</h1><p>One workspace for expected goals, player trends, and match-day insights.</p><div className="pitch">⚽  ─ ─ ─  ⚽  ─ ─ ─  ⚽</div></div><small>THE COACH'S ANALYTICS WORKSPACE</small></div>
    <div className="login-form"><form onSubmit={login}><span className="eyebrow">WELCOME BACK</span><h2>Log in to xG Insights</h2><p>Access your team's match and player analytics.</p><label>Email address<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="coach@club.com" /></label><label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" /></label>{loginError && <p className="error">{loginError}</p>}<button className="primary">Log In →</button><button className="demo" type="button" onClick={() => navTo('dashboard')}>Explore the demo workspace →<small>No account required</small></button><p className="hint">Demo only — no real authentication.</p></form></div>
  </div>

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand">◉ xG <strong>Insights</strong></div><span className="nav-heading">WORKSPACE</span><nav><button className={page === 'dashboard' ? 'active' : ''} onClick={() => navTo('dashboard')}>Dashboard</button><button onClick={() => navTo('dashboard')}>Matches <small>(summary)</small></button><button disabled title="Rory is building this screen">Match Summary <small>Coming soon</small></button><button disabled title="Rory is building this screen">Shot Map <small>Coming soon</small></button><button onClick={() => navTo('dashboard')}>Players <small>(below)</small></button><button className={page === 'upload' ? 'active' : ''} onClick={() => navTo('upload')}>Upload CSV</button></nav><div className="side-bottom">Demo Coach <button onClick={() => navTo('login')}>Log out</button></div></aside>
    <div className="workspace"><header><span>xG Insights › {page === 'upload' ? 'Upload CSV' : 'Dashboard'}</span><strong>2026 SEASON</strong></header>
      {page === 'dashboard' ? <main><div className="page-title"><div><span className="eyebrow">TEAM OVERVIEW</span><h1>Coach Dashboard</h1><p>Farmingdale State • Sample match analytics</p></div><button className="primary" onClick={() => navTo('upload')}>↑ Upload match data</button></div>{notice && <div className="success">{notice}</div>}
        <div className="stats"><article><span>Matches</span><strong>{matches}</strong></article><article><span>Goals</span><strong>{homeStats.goals}</strong></article><article><span>Shots</span><strong>{homeStats.shots}</strong></article><article><span>Total xG</span><strong>{formatXg(homeStats.xg)}</strong></article></div>
        <div className="two-col"><section className="card"><h2>Match comparison</h2><p>Farmingdale State vs. Adelphi (mock data)</p><div className="comparison"><div><span>Farmingdale State</span><strong>{homeStats.goals} goals</strong><b>{formatXg(homeStats.xg)} xG</b></div><div><span>Opponent teams</span><strong>{awayStats.goals} goals</strong><b>{formatXg(awayStats.xg)} xG</b></div></div><p className="hint">Match Summary and Shot Map pages are being designed by Rory.</p></section><section className="card"><h2>Recent match</h2><p>Match ID: {shots[0]?.match_id || '—'}</p><div className="score">{homeStats.goals} – {awayStats.goals}</div><p>{team} vs. opponent</p><button className="secondary" onClick={() => navTo('upload')}>Upload another CSV</button></section></div>
        <section className="card"><h2>Player performance</h2><p>Totals calculated directly from mock shot records</p><div className="table-scroll"><table><thead><tr><th>Player</th><th>Shots</th><th>Goals</th><th>xG</th></tr></thead><tbody>{playerStats.map(p => <tr key={p.name}><td>{p.name}</td><td>{p.shots}</td><td>{p.goals}</td><td>{formatXg(p.xg)}</td></tr>)}</tbody></table></div></section>
      </main> : <main><button className="back" onClick={() => navTo('dashboard')}>← Back to Dashboard</button><div className="page-title"><div><span className="eyebrow">DATA IMPORT</span><h1>Upload shot data</h1><p>Preview and validate a CSV locally. No backend connection yet.</p></div></div><div className="upload-layout"><section className="card"><h2>1. Select your CSV file</h2><p>Upload shot data using the agreed team format.</p><div className="dropzone" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); loadFile(e.dataTransfer.files[0]) }}><div className="upload-icon">↑</div><strong>Drag and drop your CSV here</strong><p>or choose a file from your computer</p><input ref={fileInput} type="file" accept=".csv,text/csv" hidden onChange={e => loadFile(e.target.files?.[0])} /><button className="secondary" onClick={() => fileInput.current?.click()}>Browse Files</button><small>CSV only · max 10 MB</small></div><button className="text-button" onClick={() => { setPreview(sampleShots); setFileName('sample_shots.csv'); setUploadError('') }}>Load sample shot data</button></section><aside className="card"><h2>CSV requirements</h2><p>Required columns:</p><div className="chips">{columns.map(c => <code key={c}>{c}</code>)}</div><p className="hint">x and y: 0–100 • attack toward x=100</p><p className="hint">xG: 0–1, or blank while pending</p><p className="hint">Outcomes: {allowedOutcomes.join(', ')}</p></aside></div>{uploadError && <p className="error">{uploadError}</p>}{preview && <section className="card"><div className="preview-title"><div><h2>2. Review your shot data</h2><p>{fileName} • {preview.length} rows • {preview.some(s => s.xg === null) ? 'xG pending for some shots' : 'All xG values present'}</p></div><button className="primary" onClick={importPreview}>Import into demo →</button></div><div className="table-scroll"><table><thead><tr>{['id', 'player', 'team', 'minute', 'x', 'y', 'outcome', 'xg'].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{preview.slice(0, 6).map((s, i) => <tr key={`${s.id}-${i}`}><td>{s.id}</td><td>{s.player}</td><td>{s.team}</td><td>{s.minute}</td><td>{s.x}</td><td>{s.y}</td><td>{s.outcome}</td><td>{s.xg ?? 'pending'}</td></tr>)}</tbody></table></div></section>}</main>}
    </div>
  </div>
}
export default App
