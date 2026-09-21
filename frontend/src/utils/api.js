/**
 * Sikasem API Client
 * Uses native fetch (no axios) with JWT auth, token refresh, and error handling.
 */

const BASE_URL = '/api'

// ── Token management ───────────────────────────────────────────────────────────
export const tokenStore = {
  get access()  { return localStorage.getItem('sk_access')  },
  get refresh() { return localStorage.getItem('sk_refresh') },
  set(access, refresh) {
    localStorage.setItem('sk_access', access)
    if (refresh) localStorage.setItem('sk_refresh', refresh)
  },
  clear() {
    localStorage.removeItem('sk_access')
    localStorage.removeItem('sk_refresh')
  },
}

let isRefreshing = false
let refreshQueue = []

async function refreshAccessToken() {
  const refresh = tokenStore.refresh
  if (!refresh) throw new Error('No refresh token')

  const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  if (!res.ok) {
    tokenStore.clear()
    window.location.href = '/login'
    throw new Error('Session expired. Please log in again.')
  }

  const data = await res.json()
  tokenStore.set(data.access, data.refresh || refresh)
  return data.access
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`
  const isFormData = options.body instanceof FormData

  const buildHeaders = (token) => ({
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  })

  const buildInit = (headers) => ({
    ...options,
    headers,
    body: isFormData
      ? options.body
      : options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  let response = await fetch(url, buildInit(buildHeaders(tokenStore.access)))

  // 401 — try token refresh once
  if (response.status === 401 && tokenStore.refresh) {
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const newToken = await refreshAccessToken()
        isRefreshing = false
        refreshQueue.forEach(cb => cb(newToken))
        refreshQueue = []
        response = await fetch(url, buildInit(buildHeaders(newToken)))
      } catch (e) {
        isRefreshing = false
        refreshQueue.forEach(cb => cb(null))
        refreshQueue = []
        throw e
      }
    } else {
      await new Promise((resolve, reject) => {
        refreshQueue.push(token => token ? resolve(token) : reject(new Error('Refresh failed')))
      })
    }
  }

  if (response.status === 204) return null

  if (!response.ok) {
    let errData = {}
    try { errData = await response.json() } catch {}
    const msg =
      errData.detail ||
      (errData.error && errData.details ? `${errData.error} ${errData.details}` : null) ||
      errData.error ||
      errData.message ||
      Object.entries(errData)
        .filter(([k]) => k !== 'non_field_errors')
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ') ||
      (errData.non_field_errors && errData.non_field_errors.join(', ')) ||
      `Request failed (${response.status})`
    const error = new Error(msg)
    error.status = response.status
    error.data = errData
    throw error
  }

  return response.json()
}

// ── HTTP helpers ───────────────────────────────────────────────────────────────
export const api = {
  get(url, params) {
    const defined = params
      ? Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
      : []
    const qs = defined.length ? '?' + new URLSearchParams(defined).toString() : ''
    return apiFetch(`${url}${qs}`)
  },
  post:   (url, body)       => apiFetch(url, { method: 'POST',   body }),
  put:    (url, body)       => apiFetch(url, { method: 'PUT',    body }),
  patch:  (url, body)       => apiFetch(url, { method: 'PATCH',  body }),
  delete: (url)             => apiFetch(url, { method: 'DELETE' }),
  upload: (url, formData)   => apiFetch(url, { method: 'POST',   body: formData }),

  async download(url, filename) {
    const headers = {}
    if (tokenStore.access) headers['Authorization'] = `Bearer ${tokenStore.access}`
    const res = await fetch(`${BASE_URL}${url}`, { headers })
    if (!res.ok) throw new Error(`Download failed (${res.status})`)
    const blob = await res.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  },
}

// ── Domain APIs ────────────────────────────────────────────────────────────────

export const authApi = {
  login:          (email, password) => api.post('/auth/login/', { email, password }),
  logout:         (refresh)         => api.post('/auth/logout/', { refresh }),
  me:             ()                => api.get('/auth/me/'),
  changePassword: (data)            => api.post('/auth/change-password/', data),
}

export const employeeApi = {
  list:          (params) => api.get('/employees/', params),
  get:           (id)     => api.get(`/employees/${id}/`),
  create:        (data)   => api.post('/employees/', data),
  update:        (id, data) => api.patch(`/employees/${id}/`, data),
  delete:        (id)     => api.delete(`/employees/${id}/`),
  payslips:      (id)     => api.get(`/employees/${id}/payslips/`),
  leaveBalances: (id, year) => api.get(`/employees/${id}/leave_balances/`, year ? { year } : {}),
  salaryHistory: (id)     => api.get(`/employees/${id}/salary_history/`),
  headcount:     ()       => api.get('/employees/headcount/'),
  orgChart:      ()       => api.get('/employees/org_chart/'),
}

export const payrollApi = {
  // Periods
  periods:       (params) => api.get('/payroll/periods/', params),
  getPeriod:     (id)     => api.get(`/payroll/periods/${id}/`),
  createPeriod:  (data)   => api.post('/payroll/periods/', data),
  processPeriod: (id)     => api.post(`/payroll/periods/${id}/process/`),
  resetPeriod:   (id)     => api.post(`/payroll/periods/${id}/reset/`),
  approvePeriod: (id)     => api.post(`/payroll/periods/${id}/approve/`),
  disbursePeriod:(id)     => api.post(`/payroll/periods/${id}/disburse/`),
  periodSummary: (id)     => api.get(`/payroll/periods/${id}/summary/`),
  periodAnomalies:(id)    => api.get(`/payroll/periods/${id}/anomalies/`),
  recheckAnomalies:(id)   => api.post(`/payroll/periods/${id}/recheck_anomalies/`),
  generateAllPdfs:(id)    => api.post(`/payroll/periods/${id}/generate_pdfs/`),

  // Payslips
  payslips:        (params) => api.get('/payroll/payslips/', params),
  getPayslip:      (id)     => api.get(`/payroll/payslips/${id}/`),
  downloadPayslip: (id)     => api.download(`/payroll/payslips/${id}/download/`, `payslip_${id}.pdf`),
  disputePayslip:  (id, reason) => api.post(`/payroll/payslips/${id}/dispute/`, { reason }),

  // Salary
  components:          (params) => api.get('/payroll/components/', params),
  createComponent:     (data)   => api.post('/payroll/components/', data),
  updateComponent:     (id, d)  => api.patch(`/payroll/components/${id}/`, d),
  structures:          ()       => api.get('/payroll/structures/'),
  createStructure:     (data)   => api.post('/payroll/structures/', data),
  updateStructure:     (id, d)  => api.patch(`/payroll/structures/${id}/`, d),
  employeeSalaries:    (params) => api.get('/payroll/employee-salaries/', params),
  setEmployeeSalary:   (data)   => api.post('/payroll/employee-salaries/', data),
  updateEmployeeSalary:(id, d)  => api.patch(`/payroll/employee-salaries/${id}/`, d),
  createEmployeeSalary:(data)   => api.post('/payroll/employee-salaries/', data),
  deleteEmployeeSalary:(id)     => api.delete(`/payroll/employee-salaries/${id}/`),

  // Rules
  rules:       ()       => api.get('/payroll/rules/'),
  createRule:  (data)   => api.post('/payroll/rules/', data),
  updateRule:  (id, d)  => api.patch(`/payroll/rules/${id}/`, d),
  deleteRule:  (id)     => api.delete(`/payroll/rules/${id}/`),

  // AI
  askCompliance: (question) => api.post('/payroll/ai/compliance_question/', { question }),
  forecast:      (months)   => api.get('/payroll/ai/forecast/', { months }),
}

export const attendanceApi = {
  list:           (params)  => api.get('/attendance/records/', params),
  create:         (data)    => api.post('/attendance/records/', data),
  update:         (id, d)   => api.patch(`/attendance/records/${id}/`, d),
  bulkImport:     (records) => api.post('/attendance/records/bulk_import/', { records }),
  monthlySummary: (params)  => api.get('/attendance/records/monthly_summary/', params),
  shifts:         ()        => api.get('/attendance/shifts/'),
  createShift:    (data)    => api.post('/attendance/shifts/', data),
}

export const leaveApi = {
  types:        ()       => api.get('/leaves/types/'),
  createType:   (data)   => api.post('/leaves/types/', data),
  applications: (params) => api.get('/leaves/applications/', params),
  apply:        (data)   => api.post('/leaves/applications/', data),
  approve:      (id)     => api.post(`/leaves/applications/${id}/approve/`),
  reject:       (id, reason) => api.post(`/leaves/applications/${id}/reject/`, { reason }),
  calendar:     ()       => api.get('/leaves/applications/calendar/'),
}

export const loanApi = {
  types:     ()       => api.get('/loans/types/'),
  list:      (params) => api.get('/loans/', params),
  get:       (id)     => api.get(`/loans/${id}/`),
  apply:     (data)   => api.post('/loans/', data),
  approve:   (id)     => api.post(`/loans/${id}/approve/`),
  disburse:  (id)     => api.post(`/loans/${id}/disburse/`),
  repayments:(id)     => api.get(`/loans/${id}/repayments/`),
}

// Fixed: all company sub-resources are company-scoped on backend;
// frontend just calls the endpoint — no need to pass company_id param.
export const companyApi = {
  list:        ()       => api.get('/companies/'),
  get:         (id)     => api.get(`/companies/${id}/`),
  update:      (id, d)  => api.patch(`/companies/${id}/`, d),
  getSettings: (id)     => api.get(`/companies/${id}/settings/`),
  saveSettings:(id, d)  => api.patch(`/companies/${id}/settings/`, d),

  // These endpoints return ONLY records belonging to the logged-in user's company
  branches:    (params) => api.get('/companies/branches/', params),
  departments: (params) => api.get('/companies/departments/', params),
  jobGrades:   (params) => api.get('/companies/job-grades/', params),
}

export const reportsApi = {
  dashboard:      ()         => api.get('/reports/dashboard/'),
  payrollSummary: (periodId) => api.get('/reports/payroll_summary/', { period_id: periodId }),
  taxReport:      (year)     => api.get('/reports/tax_report/', { year }),
  headcountReport:(year)     => api.get('/reports/headcount_report/', { year }),
  leaveReport:    (year)     => api.get('/reports/leave_report/', { year }),
  exportCsv:      (periodId) => api.download(`/reports/export_payroll_csv/?period_id=${periodId}`, `payroll_${periodId}.csv`),
}

export const notifApi = {
  list:       ()   => api.get('/notifications/'),
  unreadCount:()   => api.get('/notifications/unread_count/'),
  markRead:   (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead:()   => api.post('/notifications/mark_all_read/'),
}

export const userApi = {
  list:          (params) => api.get('/auth/users/', params),
  create:        (data)   => api.post('/auth/users/', data),
  update:        (id, d)  => api.patch(`/auth/users/${id}/`, d),
  toggleActive:  (id)     => api.post(`/auth/users/${id}/toggle_active/`),
  resetPassword: (id)     => api.post(`/auth/users/${id}/reset_password/`),
  auditLogs:     (params) => api.get('/auth/audit-logs/', params),
}
