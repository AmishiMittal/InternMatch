import { useEffect, useState } from 'react'
import { api } from '../api'

const TIER_BADGE = {
  'Highly Recommended': 'badge-highly',
  'Recommended': 'badge-recommended',
  'Eligible': 'badge-eligible',
}

const STORAGE_KEY = 'internmatch_student_auth'

export default function StudentPortal() {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
    } catch {
      return null
    }
  })
  const [mode, setMode] = useState('login')
  const [tab, setTab] = useState('upload')
  const [recommendations, setRecommendations] = useState([])
  const [resumeFile, setResumeFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
    location_preference: '',
    sector_interests: '',
    past_internships: 0,
  })

  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    else localStorage.removeItem(STORAGE_KEY)
  }, [auth])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await api.loginStudent(loginForm)
      setAuth(result)
      if (result.student.skills) {
        setTab('recommendations')
        const recs = await api.getRecommendations(result.student.id, result.token)
        setRecommendations(recs)
      } else {
        setTab('upload')
      }
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
      const result = await api.createStudent({
        ...registerForm,
        past_internships: Number(registerForm.past_internships),
      })
      setAuth(result)
      setSuccess('Profile created! Upload your resume (PDF) to get recommendations.')
      setTab('upload')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setAuth(null)
    setRecommendations([])
    setMode('login')
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!resumeFile) {
      setError('Choose a PDF resume to upload.')
      return
    }
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      await api.uploadResume(auth.student.id, resumeFile, auth.token)
      setSuccess('Resume uploaded and parsed successfully!')
      setResumeFile(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadRecommendations = async () => {
    setError('')
    setLoading(true)
    try {
      const recs = await api.getRecommendations(auth.student.id, auth.token)
      setRecommendations(recs)
      setTab('recommendations')
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
          <h2>Find Your Internship</h2>
          <p>Sign in or create a student profile to get started.</p>
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
            <h3 className="section-title">Student Log In</h3>
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label>Email</label>
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
            <h3 className="section-title">Create Student Profile</h3>
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label>Full Name</label>
                <input required value={registerForm.name} onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" required value={registerForm.email} onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input type="password" required minLength={8} value={registerForm.password} onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Location Preference</label>
                  <input required placeholder="e.g. San Francisco, CA" value={registerForm.location_preference} onChange={(e) => setRegisterForm({ ...registerForm, location_preference: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Past Internships</label>
                  <input type="number" min="0" value={registerForm.past_internships} onChange={(e) => setRegisterForm({ ...registerForm, past_internships: e.target.value })} />
                </div>
              </div>
              <div className="form-group">
                <label>Sector Interests</label>
                <input required placeholder="e.g. Technology, Finance" value={registerForm.sector_interests} onChange={(e) => setRegisterForm({ ...registerForm, sector_interests: e.target.value })} />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating…' : 'Create Profile'}
              </button>
            </form>
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Find Your Internship</h2>
        <p>
          Signed in as <strong>{auth.student.name}</strong>.{' '}
          <button className="link-btn" onClick={handleLogout}>Log out</button>
        </p>
        <p>
          Recommendations are shown as Highly Recommended, Recommended, or Eligible — match scores are not displayed.
        </p>
      </div>

      <div className="legend">
        <div className="legend-item">
          <span className="badge badge-highly">Highly Recommended</span>
          <span>Top fit for your profile</span>
        </div>
        <div className="legend-item">
          <span className="badge badge-recommended">Recommended</span>
          <span>Strong alignment with requirements</span>
        </div>
        <div className="legend-item">
          <span className="badge badge-eligible">Eligible</span>
          <span>Meets minimum qualification threshold</span>
        </div>
      </div>

      <div className="tabs">
        <button className={tab === 'upload' ? 'tab active' : 'tab'} onClick={() => setTab('upload')}>
          Upload Resume
        </button>
        <button className={tab === 'recommendations' ? 'tab active' : 'tab'} onClick={() => setTab('recommendations')}>
          My Recommendations
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {tab === 'upload' && (
        <div className="card" style={{ maxWidth: 560 }}>
          <h3 className="section-title">Upload Resume (PDF)</h3>
          <form onSubmit={handleUpload}>
            <div className="form-group file-input-wrapper">
              <label>Resume File</label>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              />
              <p className="file-hint">PDF format only. Skills and qualifications are extracted automatically.</p>
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Uploading…' : 'Upload Resume'}
            </button>
          </form>
        </div>
      )}

      {tab === 'recommendations' && (
        <div>
          <div className="card" style={{ marginBottom: '1.5rem', maxWidth: 560 }}>
            <button className="btn-primary" onClick={loadRecommendations} disabled={loading}>
              {loading ? 'Loading…' : 'Refresh Recommendations'}
            </button>
          </div>

          {recommendations.length === 0 ? (
            <div className="empty-state card">
              No eligible internships yet. Upload your resume and ensure your profile matches open roles.
            </div>
          ) : (
            recommendations.map((rec) => (
              <div key={rec.internship_id} className="internship-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
                  <h3>{rec.title}</h3>
                  <span className={`badge ${TIER_BADGE[rec.recommendation]}`}>{rec.recommendation}</span>
                </div>
                <div className="internship-meta">
                  <span>{rec.company_name}</span>
                  <span>·</span>
                  <span>{rec.location}</span>
                  <span>·</span>
                  <span>{rec.sector}</span>
                </div>
                <p className="internship-desc">{rec.description}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
