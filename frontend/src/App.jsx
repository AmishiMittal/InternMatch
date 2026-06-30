import { useState } from 'react'
import CompanyPortal from './components/CompanyPortal'
import StudentPortal from './components/StudentPortal'
import './App.css'

function App() {
  const [portal, setPortal] = useState('student')

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-icon">◈</span>
            <div>
              <h1 className="brand-title">InternMatch</h1>
              <p className="brand-tagline">AI-powered internship matchmaking</p>
            </div>
          </div>
          <nav className="portal-switch">
            <button
              className={portal === 'student' ? 'portal-btn active' : 'portal-btn'}
              onClick={() => setPortal('student')}
            >
              Student Portal
            </button>
            <button
              className={portal === 'company' ? 'portal-btn active' : 'portal-btn'}
              onClick={() => setPortal('company')}
            >
              Company Portal
            </button>
          </nav>
        </div>
      </header>

      <main className="main">
        {portal === 'student' ? <StudentPortal /> : <CompanyPortal />}
      </main>

      <footer className="footer">
        <p>Matches based on skills, qualifications, location, sector interests, experience &amp; capacity.</p>
      </footer>
    </div>
  )
}

export default App
