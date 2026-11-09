import { useState } from 'react'
import './App.css'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import UploadCSV from './pages/UploadCSV.jsx'
import MatchSummary from './components/MatchSummary.jsx'
import ShotMap from './components/ShotMap.jsx'
import { sampleShots } from './data/mockShots.js'
import { parseCsv } from './utils/csv.js'

export default function App() {
  const [page, setPage] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [shots, setShots] = useState(sampleShots)
  const [team, setTeam] = useState('Farmingdale State')
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [notice, setNotice] = useState('')
  const teams = [...new Set(shots.map(s => s.team).filter(Boolean))]

  function navTo(target) { setNotice(''); setPage(target) }
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
    setShots(preview)
    if (!preview.some(s => s.team === team)) setTeam(preview[0]?.team || '')
    setNotice(`${preview.length} shots imported into this local demo.`)
    setPage('dashboard')
  }
  function loadSample() {
    setPreview(sampleShots); setFileName('sample_shots.csv'); setUploadError('')
  }

  if (page === 'login') return <Login
    email={email} setEmail={setEmail} password={password} setPassword={setPassword}
    loginError={loginError} onLogin={login} onDemo={() => navTo('dashboard')}
  />

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand">◉ xG <strong>Insights</strong></div><span className="nav-heading">WORKSPACE</span><nav><button className={page === 'dashboard' ? 'active' : ''} onClick={() => navTo('dashboard')}>Dashboard</button><button onClick={() => navTo('dashboard')}>Matches <small>(summary)</small></button><button className={page === 'matchsummary' ? 'active' : ''} onClick={() => navTo('matchsummary')}>Match Summary</button><button className={page === 'shotmap' ? 'active' : ''} onClick={() => navTo('shotmap')}>Shot Map</button><button onClick={() => navTo('dashboard')}>Players <small>(below)</small></button><button className={page === 'upload' ? 'active' : ''} onClick={() => navTo('upload')}>Upload CSV</button></nav><div className="side-bottom">Demo Coach <button onClick={() => navTo('login')}>Log out</button></div></aside>
    <div className="workspace"><header><span>xG Insights › {{ upload: 'Upload CSV', matchsummary: 'Match Summary', shotmap: 'Shot Map' }[page] ?? 'Dashboard'}</span><strong>2026 SEASON</strong></header>
      {page === 'matchsummary' ? <MatchSummary shots={shots} homeTeam={team} onBack={() => navTo('dashboard')} onOpenShotMap={() => navTo('shotmap')} />
        : page === 'shotmap' ? <ShotMap shots={shots} homeTeam={team} onBack={() => navTo('dashboard')} />
        : page === 'dashboard' ? <Dashboard shots={shots} team={team} teams={teams} onTeamChange={setTeam} notice={notice} onUpload={() => navTo('upload')} />
        : <UploadCSV preview={preview} fileName={fileName} uploadError={uploadError}
            onBack={() => navTo('dashboard')} onFile={loadFile} onSample={loadSample} onImport={importPreview} />}
    </div>
  </div>
}
