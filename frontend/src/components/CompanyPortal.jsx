import { useEffect, useState } from 'react'
import { api } from '../api'

const STORAGE_KEY = 'internmatch_company_auth'

export default function CompanyPortal() {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
    } catch {
      return null
    }
  })
  const [mode, setMode] = useState('login')
  const [tab, setTab] = useState('post')
  const [internships, setInternships] = useState([])
  const [selectedInternshipId, setSelectedInternshipId] = useState('')
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
    sector: '',
    location: '',
  })

  const [internshipForm, setInternshipForm] = useState({
    title: '',
    description: '',
    required_skills: '',
    required_qualifications: '',
    location: '',
    sector: '',
    capacity: 1,
  })

  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    else localStorage.removeItem(STORAGE_KEY)
  }, [auth])

  useEffect(() => {
    if (auth) api.listInternships().then(setInternships).catch(() => {})
  }, [auth])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await api.loginCompany(loginForm)
      setAuth(result)
      setTab('post')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await api.createCompany(registerForm)
      setAuth(result)
      setSuccess('Company registered! Post an internship to start receiving ranked candidates.')
      setTab('post')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setAuth(null)
    setInternships([])
    setCandidates([])
    setMode('login')
  }

  const handlePostInternship = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const internship = await api.createInternship(
        { ...internshipForm, capacity: Number(internshipForm.capacity) },
        auth.token,
      )
      setInternships((prev) => [internship, ...prev])
      setSelectedInternshipId(String(internship.id))
      setSuccess('Internship posted! View ranked candidates in the Candidates tab.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadCandidates = async () => {
    if (!selectedInternshipId) {
      setError('Select an internship first.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const ranked = await api.getRankedCandidates(selectedInternshipId, auth.token)
      setCandidates(ranked)
      setTab('candidates')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!auth) {
    return (
      <div>
        <div className="page-header">
          <h2>Company Dashboard</h2>
          <p>Sign in or register your company to start posting internships.</p>
        </div>

        <div className="tabs">
          <button className={mode === 'login' ? 'tab active' : 'tab'} onClick={() => setMode('login')}>
            Log In
          </button>
          <button className={mode === 'register' ? 'tab active' : 'tab'} onClick={() => setMode('register')}>
            Register
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {mode === 'login' && (
          <div className="card" style={{ maxWidth: 560 }}>
            <h3 className="section-title">Company Log In</h3>
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label>HR Email</label>
                <input type="email" required value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input type="password" required value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Logging in…' : 'Log In'}
              </button>
            </form>
          </div>
        )}

        {mode === 'register' && (
          <div className="card" style={{ maxWidth: 560 }}>
            <h3 className="section-title">Register Company</h3>
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label>Company Name</label>
                <input required value={registerForm.name} onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>HR Email</label>
                <input type="email" required value={registerForm.email} onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input type="password" required minLength={8} value={registerForm.password} onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Sector</label>
                  <input required placeholder="e.g. Technology" value={registerForm.sector} onChange={(e) => setRegisterForm({ ...registerForm, sector: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Location</label>
                  <input required placeholder="e.g. Austin, TX" value={registerForm.location} onChange={(e) => setRegisterForm({ ...registerForm, location: e.target.value })} />
                </div>
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Registering…' : 'Register Company'}
              </button>
            </form>
          </div>
        )}
      </div>
    )
  }

  const myInternships = internships.filter((i) => i.company_id === auth.company.id)

  return (
    <div>
      <div className="page-header">
        <h2>Company Dashboard</h2>
        <p>
          Signed in as <strong>{auth.company.name}</strong>.{' '}
          <button className="link-btn" onClick={handleLogout}>Log out</button>
        </p>
        <p>
          Post internship openings and receive AI-ranked candidate lists with match scores.
          Rankings consider skills, qualifications, location, sector fit, past experience, and remaining capacity.
        </p>
      </div>

      <div className="tabs">
        <button className={tab === 'post' ? 'tab active' : 'tab'} onClick={() => setTab('post')}>
          Post Internship
        </button>
        <button className={tab === 'candidates' ? 'tab active' : 'tab'} onClick={() => setTab('candidates')}>
          Ranked Candidates
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {tab === 'post' && (
        <div className="card">
          <h3 className="section-title">Post Internship</h3>
          <form onSubmit={handlePostInternship}>
            <div className="form-group">
              <label>Title</label>
              <input required value={internshipForm.title} onChange={(e) => setInternshipForm({ ...internshipForm, title: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea required value={internshipForm.description} onChange={(e) => setInternshipForm({ ...internshipForm, description: e.target.value })} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Required Skills (comma-separated)</label>
                <input required placeholder="python, react, sql" value={internshipForm.required_skills} onChange={(e) => setInternshipForm({ ...internshipForm, required_skills: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Required Qualifications</label>
                <input placeholder="computer science, bachelor" value={internshipForm.required_qualifications} onChange={(e) => setInternshipForm({ ...internshipForm, required_qualifications: e.target.value })} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Location</label>
                <input required value={internshipForm.location} onChange={(e) => setInternshipForm({ ...internshipForm, location: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Sector</label>
                <input required value={internshipForm.sector} onChange={(e) => setInternshipForm({ ...internshipForm, sector: e.target.value })} />
              </div>
            </div>
            <div className="form-group" style={{ maxWidth: 200 }}>
              <label>Capacity (open slots)</label>
              <input type="number" min="1" required value={internshipForm.capacity} onChange={(e) => setInternshipForm({ ...internshipForm, capacity: e.target.value })} />
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Posting…' : 'Post Internship'}
            </button>
          </form>
        </div>
      )}

      {tab === 'candidates' && (
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>Internship</label>
              <select value={selectedInternshipId} onChange={(e) => setSelectedInternshipId(e.target.value)}>
                <option value="">Select internship…</option>
                {myInternships.map((i) => (
                  <option key={i.id} value={i.id}>{i.title}</option>
                ))}
              </select>
            </div>
            <button className="btn-primary" onClick={loadCandidates} disabled={loading}>
              {loading ? 'Loading…' : 'Load Ranked Candidates'}
            </button>
          </div>

          {candidates.length === 0 ? (
            <div className="empty-state card">
              No candidates yet. Students must upload PDF resumes before they appear in rankings.
            </div>
          ) : (
            <div className="card" style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Match Score</th>
                    <th>Skills</th>
                    <th>Qualifications</th>
                    <th>Location Pref.</th>
                    <th>Past Internships</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c, idx) => (
                    <tr key={c.student_id}>
                      <td className="rank-cell">#{idx + 1}</td>
                      <td>
                        <strong>{c.student_name}</strong>
                        <br />
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{c.student_email}</span>
                      </td>
                      <td>
                        <span className="badge badge-score">{c.match_score.toFixed(1)}%</span>
                        <div className="score-bar">
                          <div className="score-bar-fill" style={{ width: `${Math.min(c.match_score, 100)}%` }} />
                        </div>
                      </td>
                      <td style={{ maxWidth: 180, fontSize: '0.85rem' }}>{c.skills || '—'}</td>
                      <td style={{ maxWidth: 160, fontSize: '0.85rem' }}>{c.qualifications || '—'}</td>
                      <td>{c.location_preference}</td>
                      <td>{c.past_internships}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
