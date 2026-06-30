const API_BASE = '/api'

async function request(path, options = {}, token) {
  const headers = { ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

const jsonBody = (data) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  createCompany: (data) => request('/companies', jsonBody(data)),
  loginCompany: (data) => request('/companies/login', jsonBody(data)),
  createStudent: (data) => request('/students', jsonBody(data)),
  loginStudent: (data) => request('/students/login', jsonBody(data)),
  uploadResume: (studentId, file, token) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/students/${studentId}/resume`, { method: 'POST', body: form }, token)
  },
  listInternships: () => request('/internships'),
  createInternship: (data, token) => request('/internships', jsonBody(data), token),
  getRankedCandidates: (internshipId, token) => request(`/internships/${internshipId}/candidates`, {}, token),
  getRecommendations: (studentId, token) => request(`/students/${studentId}/recommendations`, {}, token),
}
