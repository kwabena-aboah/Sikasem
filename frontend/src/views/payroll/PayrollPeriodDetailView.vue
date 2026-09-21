<template>
  <div>
    <div class="page-header">
      <div class="d-flex align-items-center gap-3">
        <router-link to="/payroll/periods" class="sk-btn sk-btn-ghost sk-btn-icon"><i class="bi bi-arrow-left"></i></router-link>
        <div>
          <h1 class="page-title" style="font-size:20px">{{ period?.name }}</h1>
          <div class="page-subtitle" v-if="period">
            {{ formatDate(period.period_start) }} – {{ formatDate(period.period_end) }} &bull; Pay date: {{ formatDate(period.pay_date) }}
          </div>
        </div>
      </div>
      <div class="d-flex gap-2" v-if="period">
        <span class="sk-badge" :class="`badge-${period.status}`" style="font-size:13px;padding:6px 14px">{{ period.status_display || period.status }}</span>
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="exportCsv">
          <i class="bi bi-download"></i> Export CSV
        </button>
        <button
          v-if="['processing', 'review'].includes(period.status)"
          class="sk-btn sk-btn-warning sk-btn-sm"
          :disabled="resetting"
          @click="resetAndProcess">
          <span v-if="resetting" class="spinner-border spinner-border-sm"></span>
          <i v-else class="bi bi-arrow-clockwise"></i> Reset &amp; Regenerate
        </button>
        <button v-if="period.status === 'approved'" class="sk-btn sk-btn-primary sk-btn-sm" @click="generateAllPdfs">
          <i class="bi bi-file-pdf"></i> Generate PDFs
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center p-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="summary">

      <!-- Summary KPIs -->
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-lg-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:var(--sk-blue-mid)"></div>
            <div class="kpi-icon" style="background:#EEF4FF;color:var(--sk-blue-mid)"><i class="bi bi-people-fill"></i></div>
            <div class="kpi-value">{{ summary.statistics?.count || 0 }}</div>
            <div class="kpi-label">Employees</div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:var(--sk-warning)"></div>
            <div class="kpi-icon" style="background:#FEF3C7;color:var(--sk-warning)"><i class="bi bi-cash"></i></div>
            <div class="kpi-value" style="font-size:18px">{{ fmtAmt(summary.statistics?.total_gross) }}</div>
            <div class="kpi-label">Total Gross</div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:var(--sk-danger)"></div>
            <div class="kpi-icon" style="background:#FEE2E2;color:var(--sk-danger)"><i class="bi bi-receipt"></i></div>
            <div class="kpi-value" style="font-size:18px">{{ fmtAmt(summary.statistics?.total_paye) }}</div>
            <div class="kpi-label">Total PAYE</div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="kpi-card">
            <div class="kpi-card-accent" style="background:var(--sk-success)"></div>
            <div class="kpi-icon" style="background:#D1FAE5;color:var(--sk-success)"><i class="bi bi-bank"></i></div>
            <div class="kpi-value" style="font-size:18px">{{ fmtAmt(summary.statistics?.total_net) }}</div>
            <div class="kpi-label">Total Net Pay</div>
          </div>
        </div>
      </div>

      <!-- Anomalies banner -->
      <div v-if="anomalies.length" class="mb-4 p-4"
        style="background:#FEF2F2;border:1px solid #FECACA;border-radius:12px;display:flex;align-items:flex-start;gap:14px">
        <i class="bi bi-exclamation-triangle-fill text-danger" style="font-size:22px;margin-top:2px"></i>
        <div>
          <div style="font-weight:700;color:var(--sk-danger);font-size:14px">{{ anomalies.length }} payslip anomalies detected</div>
          <div style="font-size:13px;color:var(--sk-gray-600);margin-top:4px">
            AI anomaly detection flagged these payslips for review. Check highlighted rows below.
          </div>
          <div class="d-flex gap-2 mt-2 flex-wrap">
            <span v-for="a in anomalies.slice(0, 5)" :key="a.payslip_id || a.id" class="sk-badge badge-anomaly">
              {{ a.employee_name }}
            </span>
            <span v-if="anomalies.length > 5" style="font-size:12px;color:var(--sk-danger)">+{{ anomalies.length - 5 }} more</span>
          </div>
          <div v-for="a in anomalies.slice(0, 3)" :key="`${a.payslip_id || a.id}-details`" class="mt-2" style="font-size:12px;color:var(--sk-gray-700)">
            <strong>{{ a.employee_name }}:</strong>
            <span v-for="issue in a.issues" :key="issue.type" class="d-block ms-2">
              {{ issue.message }} <span v-if="issue.resolution" style="color:var(--sk-gray-500)">— {{ issue.resolution }}</span>
            </span>
          </div>
          <div class="mt-3 d-flex gap-2 align-items-center flex-wrap">
            <button class="sk-btn sk-btn-warning sk-btn-sm" :disabled="rechecking" @click="recheckAnomalies">
              <span v-if="rechecking" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-arrow-clockwise me-1"></i> Recheck anomalies
            </button>
            <span style="font-size:12px;color:var(--sk-gray-600)">
              Fix the recommendation, regenerate payroll, or approve after confirming the result is intentional.
            </span>
          </div>
        </div>
      </div>

      <!-- By department breakdown -->
      <div class="row g-4 mb-4" v-if="summary.by_department?.length">
        <div class="col-lg-5">
          <div class="sk-card">
            <div class="sk-card-header">
              <i class="bi bi-diagram-3" style="color:var(--sk-blue-mid)"></i>
              <h5 class="sk-card-title">By Department</h5>
            </div>
            <div class="sk-table-wrapper">
              <table class="sk-table">
                <thead><tr><th>Department</th><th>Staff</th><th>Gross</th><th>Net</th></tr></thead>
                <tbody>
                  <tr v-for="d in summary.by_department" :key="d.employee__department__name">
                    <td style="font-weight:500">{{ d.employee__department__name || 'Unassigned' }}</td>
                    <td>{{ d.count }}</td>
                    <td class="text-mono">{{ fmtAmt(d.gross) }}</td>
                    <td class="text-mono text-success">{{ fmtAmt(d.net) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-lg-7">
          <div class="sk-card">
            <div class="sk-card-header">
              <i class="bi bi-bar-chart" style="color:var(--sk-accent)"></i>
              <h5 class="sk-card-title">Cost Breakdown</h5>
            </div>
            <div class="sk-card-body">
              <canvas ref="breakdownChart" style="max-height:240px"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Payslips table -->
      <div class="sk-card">
        <div class="sk-card-header">
          <i class="bi bi-receipt-cutoff" style="color:var(--sk-blue-mid)"></i>
          <h5 class="sk-card-title">Individual Payslips</h5>
          <div class="ms-auto d-flex gap-2">
            <div class="sk-input-group" style="width:200px">
              <i class="bi bi-search input-icon"></i>
              <input type="text" class="sk-input" v-model="search" placeholder="Search employee..." />
            </div>
            <select class="sk-select" v-model="filterStatus" style="width:auto">
              <option value="">All</option>
              <option value="generated">Generated</option>
              <option value="approved">Approved</option>
              <option value="paid">Paid</option>
              <option value="disputed">Disputed</option>
            </select>
          </div>
        </div>
        <div class="sk-table-wrapper">
          <table class="sk-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Basic</th>
                <th>Gross</th>
                <th>PAYE</th>
                <th>SSNIT</th>
                <th>Loans</th>
                <th>Net Pay</th>
                <th>Status</th>
                <th style="text-align:right">PDF</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="payslipsLoading"><td colspan="9" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
              <tr v-else-if="!filteredPayslips.length"><td colspan="9"><div class="empty-state"><i class="bi bi-receipt-cutoff"></i><h5>No payslips</h5></div></td></tr>
              <tr
                v-for="ps in filteredPayslips" :key="ps.id"
                :class="{ 'row-anomaly': ps.is_anomaly, 'row-disputed': ps.status === 'disputed' }"
              >
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <div class="avatar avatar-sm">{{ `${ps.employee_name?.split(' ')[0]?.[0]||''}${ps.employee_name?.split(' ').pop()?.[0]||''}`.toUpperCase() }}</div>
                    <div>
                      <div style="font-weight:500;font-size:13px">{{ ps.employee_name }}</div>
                      <div style="font-size:11px;color:var(--sk-gray-400)">{{ ps.department }}</div>
                    </div>
                    <i v-if="ps.is_anomaly" class="bi bi-exclamation-triangle-fill text-danger ms-1" title="Anomaly detected"></i>
                  </div>
                </td>
                <td class="text-mono">{{ fmtAmt(ps.basic_salary) }}</td>
                <td class="text-mono fw-600">{{ fmtAmt(ps.gross_pay) }}</td>
                <td class="text-mono text-danger">{{ fmtAmt(ps.paye_tax) }}</td>
                <td class="text-mono text-warning">{{ fmtAmt(ps.ssnit_employee) }}</td>
                <td class="text-mono">{{ fmtAmt(ps.loan_repayment) }}</td>
                <td class="text-mono fw-600 text-success">{{ fmtAmt(ps.net_pay) }}</td>
                <td><span class="sk-badge" :class="`badge-${ps.status}`">{{ ps.status }}</span></td>
                <td style="text-align:right">
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="downloadPayslip(ps.id)" title="Download PDF">
                    <i class="bi bi-download"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Totals footer -->
        <div v-if="filteredPayslips.length" class="payroll-footer">
          <div class="pf-item">
            <span>Total Employees</span>
            <strong>{{ filteredPayslips.length }}</strong>
          </div>
          <div class="pf-item">
            <span>Total Gross</span>
            <strong>GHS {{ fmtAmt(totals.gross) }}</strong>
          </div>
          <div class="pf-item text-danger">
            <span>Total PAYE</span>
            <strong>GHS {{ fmtAmt(totals.paye) }}</strong>
          </div>
          <div class="pf-item text-warning">
            <span>Total SSNIT</span>
            <strong>GHS {{ fmtAmt(totals.ssnit) }}</strong>
          </div>
          <div class="pf-item text-success">
            <span>Total Net</span>
            <strong style="font-size:16px">GHS {{ fmtAmt(totals.net) }}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { payrollApi, reportsApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const route = useRoute()
const toast = useToastStore()
const period = ref(null)
const summary = ref(null)
const payslips = ref([])
const anomalies = ref([])
const loading = ref(true)
const payslipsLoading = ref(false)
const resetting = ref(false)
const search = ref('')
const filterStatus = ref('')
const breakdownChart = ref(null)
let chart = null

const filteredPayslips = computed(() => {
  return payslips.value.filter(ps => {
    const matchSearch = !search.value || ps.employee_name?.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !filterStatus.value || ps.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

const totals = computed(() => ({
  gross: filteredPayslips.value.reduce((s, p) => s + Number(p.gross_pay || 0), 0),
  net: filteredPayslips.value.reduce((s, p) => s + Number(p.net_pay || 0), 0),
  paye: filteredPayslips.value.reduce((s, p) => s + Number(p.paye_tax || 0), 0),
  ssnit: filteredPayslips.value.reduce((s, p) => s + Number(p.ssnit_employee || 0), 0),
}))

async function load() {
  loading.value = true
  try {
    const id = route.params.id
    const [periodData, summaryData, anomalyData] = await Promise.all([
      payrollApi.getPeriod(id),
      reportsApi.payrollSummary(id).catch(() => null),
      payrollApi.periodAnomalies(id).catch(() => ({ anomalies: [] })),
    ])
    period.value = periodData
    // The reports endpoint returns aggregate values under `summary`, while
    // this view uses `statistics` for the KPI and chart bindings.
    summary.value = {
      ...(summaryData || {}),
      statistics: summaryData?.statistics || summaryData?.summary || {},
    }
    anomalies.value = anomalyData.anomalies || []

    payslipsLoading.value = true
    const psData = await payrollApi.payslips({ period_id: id })
    payslips.value = psData.results || psData
    payslipsLoading.value = false

    await nextTick()
    renderChart()
  } catch (e) {
    toast.error('Failed to load period', e.message)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!breakdownChart.value || !summary.value?.statistics) return
  const s = summary.value.statistics
  chart?.destroy()
  chart = new Chart(breakdownChart.value, {
    type: 'doughnut',
    data: {
      labels: ['Net Pay', 'PAYE Tax', 'SSNIT Employee', 'SSNIT Employer', 'Loan Repayments', 'Other Deductions'],
      datasets: [{
        data: [
          s.total_net, s.total_paye, s.total_ssnit_emp,
          s.total_ssnit_empr, s.total_loans, Math.max(0, s.total_deductions - s.total_paye - s.total_ssnit_emp - s.total_loans)
        ],
        backgroundColor: ['#1E8C5A','#C0392B','#F5A623','#3A7BD5','#7C3AED','#95A5A6'],
        borderWidth: 2, borderColor: '#fff',
      }]
    },
    options: {
      responsive: true, cutout: '62%',
      plugins: { legend: { position: 'right', labels: { padding: 12, font: { size: 11 } } } }
    }
  })
}

async function recheckAnomalies() {
  rechecking.value = true
  try {
    const result = await payrollApi.recheckAnomalies(route.params.id)
    anomalies.value = result.anomalies || []
    toast.success('Anomalies refreshed', anomalies.value.length ? `${anomalies.value.length} issue(s) still need review.` : 'No current anomalies remain.')
  } catch (e) {
    toast.error('Could not refresh anomalies', e.message)
  } finally {
    rechecking.value = false
  }
}

async function resetAndProcess() {
  if (!period.value || !confirm(
    `Reset and regenerate ${period.value.name}?\n\n` +
    'Any payslips currently attached to this failed run will be cleared, then payroll will be recalculated.'
  )) return

  resetting.value = true
  try {
    await payrollApi.resetPeriod(period.value.id)
    await payrollApi.processPeriod(period.value.id)
    toast.success('Payroll regenerated', 'The employee salaries have been recalculated.')
    await load()
  } catch (e) {
    toast.error('Regeneration failed', e.message)
    await load()
  } finally {
    resetting.value = false
  }
}

async function downloadPayslip(id) {
  try { await payrollApi.downloadPayslip(id); toast.success('Download started') }
  catch (e) { toast.error('Download failed', e.message) }
}

async function exportCsv() {
  try { await reportsApi.exportCsv(route.params.id); toast.success('Export started') }
  catch (e) { toast.error('Export failed', e.message) }
}

async function generateAllPdfs() {
  try {
    await payrollApi.generateAllPdfs(route.params.id)
    toast.success('Generating PDFs', 'Payslip PDFs are being generated in the background')
  } catch (e) {
    toast.error('Failed to generate PDFs', e.message)
  }
}

function formatDate(d) { if (!d) return '–'; return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' }) }
function fmtAmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }

onMounted(load)
</script>

<style scoped>
.row-anomaly td { background: #FFF7F7; }
.row-anomaly td:first-child { border-left: 3px solid var(--sk-danger); }
.row-disputed td { background: #FFFBEB; }

.payroll-footer {
  display: flex; gap: 0; border-top: 2px solid var(--sk-gray-200);
  background: var(--sk-gray-50);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}
.pf-item {
  flex: 1; padding: 14px 16px; text-align: center;
  border-right: 1px solid var(--sk-gray-200); font-size: 12.5px;
}
.pf-item:last-child { border-right: none; }
.pf-item span { display: block; color: var(--sk-gray-500); margin-bottom: 2px; }
.pf-item strong { font-size: 14px; font-family: var(--font-mono); }
</style>
