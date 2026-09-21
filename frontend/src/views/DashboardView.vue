<template>
  <div>
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- EMPLOYEE SELF-SERVICE DASHBOARD                                 -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <template v-if="auth.isEmployee">
      <!-- Header -->
      <div class="page-header">
        <div>
          <div class="d-flex align-items-center gap-2 mb-1">
            <h1 class="page-title">{{ greeting }}, {{ auth.user?.first_name }} 👋</h1>
            <span v-if="stats?.employee?.status" class="sk-badge badge-active" style="text-transform: capitalize;">
              {{ stats.employee.status }}
            </span>
          </div>
          <div class="page-subtitle text-muted">
            <span v-if="stats?.employee">
              {{ stats.employee.job_title || auth.user?.job_title || 'Team Member' }}
              <span v-if="stats.employee.department"> • {{ stats.employee.department }}</span>
              <span v-if="stats.employee.employee_id"> • ID: <strong class="text-mono">{{ stats.employee.employee_id }}</strong></span>
            </span>
            <span v-else>Welcome to your personal employee portal.</span>
          </div>
        </div>
        <div class="d-flex gap-2">
          <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="loadData">
            <i class="bi bi-arrow-clockwise"></i> Refresh
          </button>
          <router-link to="/leaves/apply" class="sk-btn sk-btn-primary sk-btn-sm">
            <i class="bi bi-calendar-plus-fill"></i> Apply for Leave
          </router-link>
        </div>
      </div>

      <!-- No profile alert if unlinked -->
      <div v-if="!loading && stats && !stats.has_profile" class="alert alert-warning mb-4 d-flex align-items-center gap-3">
        <i class="bi bi-exclamation-triangle-fill fs-4"></i>
        <div>
          <strong>Account Not Linked to Employee Profile</strong>
          <div style="font-size:13px">Your user account is not yet connected to an employee record. Please contact your HR administrator to link your profile.</div>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="row g-3 mb-4">
        <div v-for="i in 4" :key="i" class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="skeleton" style="width:44px;height:44px;border-radius:10px;margin-bottom:14px"></div>
            <div class="skeleton" style="width:60%;height:28px;margin-bottom:8px"></div>
            <div class="skeleton" style="width:80%;height:14px"></div>
          </div>
        </div>
      </div>

      <!-- Employee KPI Cards -->
      <div v-else class="row g-3 mb-4">
        <!-- 1. Latest Net Pay -->
        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-success),#2ECC71)"></div>
            <div class="kpi-icon" style="background:#D1FAE5;color:var(--sk-success)">
              <i class="bi bi-cash-coin"></i>
            </div>
            <div class="kpi-value text-success">GHS {{ formatAmount(stats?.latest_payroll?.net_pay) }}</div>
            <div class="kpi-label">Last Net Pay</div>
            <div class="kpi-change up">
              <i class="bi bi-calendar-check"></i>
              {{ stats?.latest_payroll?.name || 'No payslip yet' }}
            </div>
          </div>
        </div>

        <!-- 2. Leave Days Available -->
        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-blue-mid),var(--sk-blue-light))"></div>
            <div class="kpi-icon" style="background:#EEF4FF;color:var(--sk-blue-mid)">
              <i class="bi bi-calendar2-check-fill"></i>
            </div>
            <div class="kpi-value">{{ stats?.total_leave_available ?? 0 }} <span style="font-size:14px;font-weight:500;color:var(--sk-gray-500)">days</span></div>
            <div class="kpi-label">Available Leave Balance</div>
            <div class="kpi-change" :class="stats?.pending_leaves > 0 ? 'up' : ''">
              <i class="bi bi-clock"></i>
              {{ stats?.pending_leaves || 0 }} pending request(s)
            </div>
          </div>
        </div>

        <!-- 3. Active Loan Balance -->
        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,#7C3AED,#A855F7)"></div>
            <div class="kpi-icon" style="background:#EDE9FE;color:#7C3AED">
              <i class="bi bi-bank2"></i>
            </div>
            <div class="kpi-value">GHS {{ formatAmount(stats?.active_loans?.total_outstanding) }}</div>
            <div class="kpi-label">Outstanding Loans</div>
            <div class="kpi-change" style="color:#7C3AED">
              <i class="bi bi-arrow-repeat"></i>
              Monthly: GHS {{ formatAmount(stats?.active_loans?.monthly_deduction) }}
            </div>
          </div>
        </div>

        <!-- 4. Attendance This Month -->
        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-warning),var(--sk-accent))"></div>
            <div class="kpi-icon" style="background:#FEF3C7;color:var(--sk-warning)">
              <i class="bi bi-clock-history"></i>
            </div>
            <div class="kpi-value">{{ stats?.attendance?.present || 0 }} <span style="font-size:14px;font-weight:500;color:var(--sk-gray-500)">days</span></div>
            <div class="kpi-label">Attendance This Month</div>
            <div class="kpi-change" style="color:var(--sk-gray-600)">
              <i class="bi bi-person-check"></i>
              {{ stats?.attendance?.late || 0 }} late • {{ (stats?.attendance?.overtime || 0).toFixed(1) }}h OT
            </div>
          </div>
        </div>
      </div>

      <!-- Employee Content Rows -->
      <div class="row g-4 mb-4">
        <!-- Earnings History Chart -->
        <div class="col-lg-8">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-graph-up" style="color:var(--sk-blue-mid)"></i>
              <h5 class="sk-card-title">My Earnings History</h5>
              <router-link to="/payslips" class="sk-btn sk-btn-ghost sk-btn-sm ms-auto">All Payslips</router-link>
            </div>
            <div class="sk-card-body">
              <div v-if="stats?.payroll_trend?.length">
                <canvas ref="payrollChartRef" style="max-height:260px"></canvas>
              </div>
              <div v-else class="empty-state" style="padding:40px">
                <i class="bi bi-graph-up text-muted" style="font-size:32px"></i>
                <h6 class="mt-2">No earnings history yet</h6>
                <p class="text-muted" style="font-size:13px">Your monthly payslip history will appear here once payroll runs are processed.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Leave Balances Progress -->
        <div class="col-lg-4">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-calendar-check" style="color:var(--sk-accent)"></i>
              <h5 class="sk-card-title">My Leave Balances</h5>
              <router-link to="/leaves" class="sk-btn sk-btn-ghost sk-btn-sm ms-auto">Details</router-link>
            </div>
            <div class="sk-card-body">
              <div v-if="stats?.leave_balances?.length" class="d-flex flex-column gap-3">
                <div v-for="b in stats.leave_balances" :key="b.leave_type_id" class="leave-balance-item">
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <span style="font-weight:600;font-size:13px;color:var(--sk-gray-800)">{{ b.leave_type }}</span>
                    <span style="font-weight:700;font-size:13px;color:var(--sk-blue-mid)">{{ b.available }} days left</span>
                  </div>
                  <div class="sk-progress">
                    <div
                      class="sk-progress-bar"
                      :style="`width:${b.entitled > 0 ? Math.min(100, (b.taken / b.entitled) * 100) : 0}%;background:${leaveProgressColor(b.taken, b.entitled)}`"
                    ></div>
                  </div>
                  <div class="d-flex justify-content-between mt-1" style="font-size:11px;color:var(--sk-gray-500)">
                    <span>{{ b.taken }} taken</span>
                    <span>{{ b.entitled }} entitled</span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state" style="padding:30px">
                <i class="bi bi-calendar3 text-muted"></i>
                <h6>No leave balances allocated</h6>
                <p class="text-muted" style="font-size:12px">Contact HR to initialize your annual leave entitlements.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Payslips Table & Recent Leave Requests -->
      <div class="row g-4 mb-4">
        <!-- Recent Payslips Table -->
        <div class="col-lg-7">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-receipt-cutoff" style="color:var(--sk-blue-mid)"></i>
              <h5 class="sk-card-title">Recent Payslips</h5>
              <router-link to="/payslips" class="sk-btn sk-btn-ghost sk-btn-sm ms-auto">View All</router-link>
            </div>
            <div class="sk-table-wrapper">
              <table class="sk-table">
                <thead>
                  <tr>
                    <th>Period</th>
                    <th>Gross</th>
                    <th>Deductions</th>
                    <th>Net Pay</th>
                    <th>Status</th>
                    <th style="text-align:right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!stats?.recent_payslips?.length">
                    <td colspan="6" class="text-center py-4 text-muted">No payslips available</td>
                  </tr>
                  <tr v-for="ps in stats?.recent_payslips" :key="ps.id">
                    <td>
                      <div class="fw-600">{{ ps.period_name }}</div>
                      <div style="font-size:11px;color:var(--sk-gray-500)">Pay date: {{ formatDate(ps.pay_date) }}</div>
                    </td>
                    <td class="text-mono">GHS {{ formatAmount(ps.gross_pay) }}</td>
                    <td class="text-mono text-danger">-{{ formatAmount(ps.total_deductions) }}</td>
                    <td class="text-mono fw-600 text-success">GHS {{ formatAmount(ps.net_pay) }}</td>
                    <td>
                      <span class="sk-badge" :class="`badge-${ps.status}`">{{ ps.status }}</span>
                    </td>
                    <td style="text-align:right">
                      <button class="sk-btn sk-btn-ghost sk-btn-sm" title="Download PDF" @click="downloadPayslip(ps.id)">
                        <i class="bi bi-download"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Recent Leave Requests & Quick Actions -->
        <div class="col-lg-5">
          <div class="sk-card h-100 d-flex flex-column">
            <div class="sk-card-header">
              <i class="bi bi-calendar-event" style="color:var(--sk-warning)"></i>
              <h5 class="sk-card-title">Recent Leave Requests</h5>
              <router-link to="/leaves" class="sk-btn sk-btn-ghost sk-btn-sm ms-auto">All Requests</router-link>
            </div>
            <div class="sk-card-body flex-grow-1">
              <div v-if="stats?.recent_leaves?.length" class="d-flex flex-column gap-2">
                <div v-for="l in stats.recent_leaves" :key="l.id" class="p-2 border rounded d-flex justify-content-between align-items-center">
                  <div>
                    <div style="font-weight:600;font-size:13px">{{ l.leave_type__name }}</div>
                    <div style="font-size:11.5px;color:var(--sk-gray-500)">
                      {{ formatDate(l.start_date) }} – {{ formatDate(l.end_date) }} ({{ l.days_requested }} day{{ l.days_requested > 1 ? 's' : '' }})
                    </div>
                  </div>
                  <div>
                    <span class="sk-badge" :class="`badge-${l.status}`">{{ l.status }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state" style="padding:20px">
                <i class="bi bi-calendar-check text-muted"></i>
                <h6>No leave requests submitted</h6>
              </div>
            </div>
            <div class="p-3 border-top bg-light rounded-bottom">
              <div class="d-flex gap-2">
                <router-link to="/leaves/apply" class="sk-btn sk-btn-primary sk-btn-sm flex-grow-1 text-center">
                  <i class="bi bi-calendar-plus"></i> Request Leave
                </router-link>
                <router-link to="/loans/apply" class="sk-btn sk-btn-ghost sk-btn-sm flex-grow-1 text-center">
                  <i class="bi bi-wallet2"></i> Request Loan
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- MANAGEMENT / ADMIN / HR / PAYROLL DASHBOARD                     -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <template v-else>
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Dashboard</h1>
          <div class="page-subtitle">{{ greeting }}, {{ auth.user?.first_name }}. Here's your payroll &amp; organization overview.</div>
        </div>
        <div class="d-flex gap-2">
          <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="loadData">
            <i class="bi bi-arrow-clockwise"></i> Refresh
          </button>
          <router-link v-if="auth.isPayroll" to="/payroll/periods" class="sk-btn sk-btn-primary sk-btn-sm">
            <i class="bi bi-plus-lg"></i> New Payroll Run
          </router-link>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="row g-3 mb-4">
        <div v-for="i in 4" :key="i" class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="skeleton" style="width:44px;height:44px;border-radius:10px;margin-bottom:14px"></div>
            <div class="skeleton" style="width:60%;height:28px;margin-bottom:8px"></div>
            <div class="skeleton" style="width:80%;height:14px"></div>
          </div>
        </div>
      </div>

      <!-- KPI Row -->
      <div v-else class="row g-3 mb-4">
        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-blue-mid),var(--sk-blue-light))"></div>
            <div class="kpi-icon" style="background:#EEF4FF;color:var(--sk-blue-mid)">
              <i class="bi bi-people-fill"></i>
            </div>
            <div class="kpi-value">{{ stats?.employees?.active || 0 }}</div>
            <div class="kpi-label">Active Employees</div>
            <div class="kpi-change up">
              <i class="bi bi-people"></i>
              {{ stats?.employees?.total || 0 }} total
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-success),#2ECC71)"></div>
            <div class="kpi-icon" style="background:#D1FAE5;color:var(--sk-success)">
              <i class="bi bi-cash-stack"></i>
            </div>
            <div class="kpi-value">GHS {{ formatAmount(stats?.latest_payroll?.total_net) }}</div>
            <div class="kpi-label">Last Net Payroll</div>
            <div class="kpi-change" :class="stats?.latest_payroll ? 'up' : ''">
              <i class="bi bi-calendar-month"></i>
              {{ stats?.latest_payroll?.name || 'No payroll yet' }}
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,var(--sk-warning),var(--sk-accent))"></div>
            <div class="kpi-icon" style="background:#FEF3C7;color:var(--sk-warning)">
              <i class="bi bi-calendar-check"></i>
            </div>
            <div class="kpi-value">{{ stats?.pending_leaves || 0 }}</div>
            <div class="kpi-label">Pending Leave Requests</div>
            <div class="kpi-change up">
              <i class="bi bi-clock"></i>
              Awaiting approval
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:linear-gradient(90deg,#7C3AED,#A855F7)"></div>
            <div class="kpi-icon" style="background:#EDE9FE;color:#7C3AED">
              <i class="bi bi-bank2"></i>
            </div>
            <div class="kpi-value">{{ stats?.active_loans?.count || 0 }}</div>
            <div class="kpi-label">Active Loans</div>
            <div class="kpi-change" style="color:#7C3AED">
              <i class="bi bi-currency-dollar"></i>
              GHS {{ formatAmount(stats?.active_loans?.total_outstanding) }} outstanding
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="row g-4 mb-4">
        <!-- Payroll trend -->
        <div class="col-lg-8">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-graph-up" style="color:var(--sk-blue-mid)"></i>
              <h5 class="sk-card-title">Payroll Cost Trend</h5>
              <span style="font-size:12px;color:var(--sk-gray-400);margin-left:auto">Last 6 months</span>
            </div>
            <div class="sk-card-body">
              <canvas ref="payrollChartRef" style="max-height:260px"></canvas>
            </div>
          </div>
        </div>

        <!-- Dept headcount -->
        <div class="col-lg-4">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-diagram-3" style="color:var(--sk-accent)"></i>
              <h5 class="sk-card-title">By Department</h5>
            </div>
            <div class="sk-card-body">
              <canvas ref="deptChartRef" style="max-height:260px"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Row -->
      <div class="row g-4 mb-4">
        <!-- Latest payroll info -->
        <div class="col-lg-6">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-receipt-cutoff" style="color:var(--sk-blue-mid)"></i>
              <h5 class="sk-card-title">Latest Payroll</h5>
              <router-link to="/payroll/periods" class="sk-btn sk-btn-ghost sk-btn-sm ms-auto">View All</router-link>
            </div>
            <div class="sk-card-body">
              <div v-if="stats?.latest_payroll" class="payroll-summary-grid">
                <div class="psummary-item">
                  <div class="psummary-label">Period</div>
                  <div class="psummary-val">{{ stats.latest_payroll.name }}</div>
                </div>
                <div class="psummary-item">
                  <div class="psummary-label">Total Gross</div>
                  <div class="psummary-val fw-600">GHS {{ formatAmount(stats.latest_payroll.total_gross) }}</div>
                </div>
                <div class="psummary-item">
                  <div class="psummary-label">Net Pay</div>
                  <div class="psummary-val fw-600 text-success">GHS {{ formatAmount(stats.latest_payroll.total_net) }}</div>
                </div>
                <div class="psummary-item">
                  <div class="psummary-label">Employees</div>
                  <div class="psummary-val">{{ stats.latest_payroll.employee_count }}</div>
                </div>
                <div class="psummary-item">
                  <div class="psummary-label">Pay Date</div>
                  <div class="psummary-val">{{ formatDate(stats.latest_payroll.pay_date) }}</div>
                </div>
                <div class="psummary-item">
                  <div class="psummary-label">Status</div>
                  <div><span class="sk-badge" :class="`badge-${stats.latest_payroll.status}`">{{ stats.latest_payroll.status }}</span></div>
                </div>
              </div>
              <div v-else class="empty-state" style="padding:30px">
                <i class="bi bi-cash-stack"></i>
                <h5>No payroll runs yet</h5>
                <router-link to="/payroll/periods" class="sk-btn sk-btn-primary sk-btn-sm mt-3">Create First Payroll</router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick actions -->
        <div class="col-lg-6">
          <div class="sk-card h-100">
            <div class="sk-card-header">
              <i class="bi bi-lightning-fill" style="color:var(--sk-accent)"></i>
              <h5 class="sk-card-title">Quick Actions</h5>
            </div>
            <div class="sk-card-body">
              <div class="quick-actions-grid">
                <router-link to="/employees/new" class="quick-action" v-if="auth.isHR">
                  <i class="bi bi-person-plus-fill"></i>
                  <span>Add Employee</span>
                </router-link>
                <router-link to="/payroll/periods" class="quick-action" v-if="auth.isPayroll">
                  <i class="bi bi-play-circle-fill"></i>
                  <span>Run Payroll</span>
                </router-link>
                <router-link v-if="auth.user?.employee_profile_id" to="/leaves/apply" class="quick-action">
                  <i class="bi bi-calendar-plus-fill"></i>
                  <span>Apply Leave</span>
                </router-link>
                <router-link v-if="auth.user?.employee_profile_id" to="/loans/apply" class="quick-action">
                  <i class="bi bi-wallet2"></i>
                  <span>Request Loan</span>
                </router-link>
                <router-link to="/payslips" class="quick-action">
                  <i class="bi bi-download"></i>
                  <span>Download Payslip</span>
                </router-link>
                <router-link v-if="!auth.isEmployee" to="/ai-advisor" class="quick-action ai-action">
                  <i class="bi bi-stars"></i>
                  <span>AI Advisor</span>
                </router-link>
                <router-link to="/reports" class="quick-action" v-if="auth.isHR">
                  <i class="bi bi-bar-chart-line-fill"></i>
                  <span>Reports</span>
                </router-link>
                <router-link to="/attendance" class="quick-action">
                  <i class="bi bi-clock-fill"></i>
                  <span>Attendance</span>
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { reportsApi, payrollApi } from '@/utils/api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const auth = useAuthStore()
const loading = ref(true)
const stats = ref(null)
const payrollChartRef = ref(null)
const deptChartRef = ref(null)
let payrollChart = null
let deptChart = null

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
})

function formatAmount(val) {
  if (!val && val !== 0) return '0.00'
  return Number(val).toLocaleString('en-GH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

function leaveProgressColor(taken, entitled) {
  if (!entitled) return 'var(--sk-gray-400)'
  const pct = (taken / entitled) * 100
  if (pct >= 85) return 'var(--sk-danger)'
  if (pct >= 60) return 'var(--sk-warning)'
  return 'var(--sk-success)'
}

async function downloadPayslip(id) {
  try {
    await payrollApi.downloadPayslip(id)
  } catch (e) {
    console.error('Payslip download failed:', e)
  }
}

async function loadData() {
  loading.value = true
  try {
    stats.value = await reportsApi.dashboard()
    await nextTick()
    renderCharts()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (!stats.value) return

  const trend = stats.value.payroll_trend || []

  // Employee personal earnings trend chart
  if (auth.isEmployee) {
    if (payrollChartRef.value && trend.length) {
      if (payrollChart) payrollChart.destroy()
      payrollChart = new Chart(payrollChartRef.value, {
        type: 'bar',
        data: {
          labels: trend.map(t => t.name),
          datasets: [
            {
              label: 'Gross Pay',
              data: trend.map(t => t.gross),
              backgroundColor: 'rgba(58,123,213,.2)',
              borderColor: 'rgba(58,123,213,.9)',
              borderWidth: 2,
              borderRadius: 6,
            },
            {
              label: 'Net Pay',
              data: trend.map(t => t.net),
              backgroundColor: 'rgba(30,140,90,.2)',
              borderColor: 'rgba(30,140,90,.9)',
              borderWidth: 2,
              borderRadius: 6,
            },
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { position: 'top' },
            tooltip: {
              callbacks: {
                label: ctx => `${ctx.dataset.label}: GHS ${Number(ctx.raw).toFixed(2)}`
              }
            }
          },
          scales: {
            y: {
              ticks: { callback: v => `GHS ${Number(v).toLocaleString()}` },
              grid: { color: 'rgba(0,0,0,.04)' }
            },
            x: { grid: { display: false } }
          }
        }
      })
    }
    return
  }

  // Management company payroll trend chart
  if (payrollChartRef.value && trend.length) {
    if (payrollChart) payrollChart.destroy()
    payrollChart = new Chart(payrollChartRef.value, {
      type: 'bar',
      data: {
        labels: trend.map(t => t.name),
        datasets: [
          {
            label: 'Gross Pay',
            data: trend.map(t => t.gross),
            backgroundColor: 'rgba(58,123,213,.15)',
            borderColor: 'rgba(58,123,213,.8)',
            borderWidth: 2,
            borderRadius: 6,
          },
          {
            label: 'Net Pay',
            data: trend.map(t => t.net),
            backgroundColor: 'rgba(30,140,90,.15)',
            borderColor: 'rgba(30,140,90,.8)',
            borderWidth: 2,
            borderRadius: 6,
          },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: 'top' } },
        scales: {
          y: { ticks: { callback: v => `GHS ${(v/1000).toFixed(0)}k` }, grid: { color: 'rgba(0,0,0,.04)' } },
          x: { grid: { display: false } }
        }
      }
    })
  }

  // Dept chart
  const depts = stats.value.department_headcount || []
  if (deptChartRef.value && depts.length) {
    if (deptChart) deptChart.destroy()
    const colors = ['#3A7BD5','#F5A623','#1E8C5A','#7C3AED','#E74C3C','#2980B9','#D4851A','#27AE60']
    deptChart = new Chart(deptChartRef.value, {
      type: 'doughnut',
      data: {
        labels: depts.map(d => d.department__name || 'Unassigned'),
        datasets: [{
          data: depts.map(d => d.count),
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#fff',
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: 'bottom', labels: { padding: 16, font: { size: 11 } } } },
        cutout: '65%',
      }
    })
  }
}

onMounted(loadData)
</script>

<style scoped>
.payroll-summary-grid {
  display: grid; grid-template-columns: 1fr 1fr 1fr;
  gap: 14px 20px;
}

.psummary-item {}
.psummary-label { font-size: 11px; color: var(--sk-gray-500); text-transform: uppercase; letter-spacing: .4px; font-weight: 600; }
.psummary-val { font-size: 14px; color: var(--sk-gray-900); margin-top: 2px; font-weight: 500; }

.leave-balance-item {
  background: var(--sk-gray-50);
  border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
}

.quick-actions-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}

.quick-action {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 14px 8px;
  background: var(--sk-gray-50); border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-md); text-decoration: none;
  color: var(--sk-gray-700); font-size: 12px; font-weight: 500;
  transition: var(--transition); cursor: pointer; text-align: center;
}

.quick-action:hover {
  background: var(--sk-blue-mid); color: white; border-color: var(--sk-blue-mid);
  transform: translateY(-2px); box-shadow: var(--shadow-md);
}

.quick-action i { font-size: 20px; }
.ai-action i { color: var(--sk-accent); }
.ai-action:hover i { color: white; }
</style>
