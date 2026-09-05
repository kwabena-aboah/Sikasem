<template>
  <div>
    <div class="page-header">
      <div class="d-flex align-items-center gap-3">
        <router-link to="/employees" class="sk-btn sk-btn-ghost sk-btn-icon"><i class="bi bi-arrow-left"></i></router-link>
        <div>
          <h1 class="page-title" style="font-size:20px">{{ employee?.get_full_name || `${employee?.first_name} ${employee?.last_name}` }}</h1>
          <div class="page-subtitle">{{ employee?.job_title }} &bull; {{ employee?.department_name }}</div>
        </div>
      </div>
      <div class="d-flex gap-2" v-if="auth.isHR">
        <router-link :to="`/employees/${route.params.id}/edit`" class="sk-btn sk-btn-ghost sk-btn-sm"><i class="bi bi-pencil"></i> Edit</router-link>
      </div>
    </div>

    <div v-if="loading" class="text-center p-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="employee" class="row g-4">
      <!-- Left: Profile card -->
      <div class="col-lg-4">
        <div class="sk-card mb-4" style="text-align:center;padding:28px 20px">
          <div class="avatar avatar-lg mx-auto mb-3" style="width:72px;height:72px;font-size:26px">
            {{ `${employee.first_name?.[0]||''}${employee.last_name?.[0]||''}`.toUpperCase() }}
          </div>
          <h4 style="font-size:17px;font-weight:700;margin-bottom:2px">{{ employee.first_name }} {{ employee.middle_name || '' }} {{ employee.last_name }}</h4>
          <div style="font-size:13px;color:var(--sk-gray-500)">{{ employee.job_title }}</div>
          <code style="font-size:12px;background:var(--sk-gray-100);padding:3px 8px;border-radius:4px;margin-top:6px;display:inline-block">{{ employee.employee_id }}</code>
          <div class="mt-3"><span class="sk-badge" :class="statusBadge(employee.status)">{{ employee.status }}</span></div>
          <div class="mt-4 text-start" style="border-top:1px solid var(--sk-gray-100);padding-top:16px">
            <div v-for="info in quickInfo" :key="info.label" class="info-row">
              <span class="info-label"><i class="bi me-2" :class="info.icon"></i>{{ info.label }}</span>
              <span class="info-val">{{ info.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Tabs -->
      <div class="col-lg-8">
        <div class="sk-tabs mb-0">
          <button v-for="t in tabs" :key="t.id" class="sk-tab" :class="{ active: activeTab === t.id }" @click="activeTab = t.id; loadTabData(t.id)">
            <i class="bi" :class="t.icon"></i> {{ t.label }}
          </button>
        </div>

        <!-- Employment -->
        <div v-if="activeTab === 'employment'" class="sk-card" style="border-radius:0 var(--radius-lg) var(--radius-lg)">
          <div class="sk-card-body">
            <div class="row g-3">
              <div v-for="f in employmentFields" :key="f.label" class="col-md-6">
                <div class="sk-form-group mb-0">
                  <label class="sk-label">{{ f.label }}</label>
                  <div style="font-size:13.5px;font-weight:500;padding:8px 0">{{ f.value || '–' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Payslips tab -->
        <div v-if="activeTab === 'payslips'" class="sk-card" style="border-radius:0 var(--radius-lg) var(--radius-lg)">
          <div class="sk-table-wrapper">
            <table class="sk-table">
              <thead><tr><th>Period</th><th>Gross</th><th>Net</th><th>Status</th><th>PDF</th></tr></thead>
              <tbody>
                <tr v-if="!payslips.length"><td colspan="5"><div class="empty-state" style="padding:24px"><i class="bi bi-receipt-cutoff"></i><h5>No payslips yet</h5></div></td></tr>
                <tr v-for="ps in payslips" :key="ps.id">
                  <td>{{ ps.period_name }}</td>
                  <td class="text-mono">GHS {{ fmt(ps.gross_pay) }}</td>
                  <td class="text-mono fw-600 text-success">GHS {{ fmt(ps.net_pay) }}</td>
                  <td><span class="sk-badge" :class="`badge-${ps.status}`">{{ ps.status }}</span></td>
                  <td><button class="sk-btn sk-btn-ghost sk-btn-sm" @click="downloadPayslip(ps.id)"><i class="bi bi-download"></i></button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Leave balances tab -->
        <div v-if="activeTab === 'leaves'" class="sk-card" style="border-radius:0 var(--radius-lg) var(--radius-lg)">
          <div class="sk-card-body">
            <div class="row g-3">
              <div v-for="b in leaveBalances" :key="b.leave_type" class="col-md-6">
                <div style="background:var(--sk-gray-50);border:1px solid var(--sk-gray-200);border-radius:10px;padding:14px 16px">
                  <div style="font-weight:600;font-size:13.5px;margin-bottom:8px">{{ b.leave_type }}</div>
                  <div class="d-flex justify-content-between mb-2" style="font-size:12px;color:var(--sk-gray-500)">
                    <span>Available: <strong style="color:var(--sk-success)">{{ b.available }}</strong></span>
                    <span>Taken: <strong>{{ b.taken }}</strong></span>
                  </div>
                  <div class="sk-progress"><div class="sk-progress-bar" :style="`width:${Math.min((b.taken/b.entitled)*100,100)}%;background:var(--sk-blue-mid)`"></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loans tab -->
        <div v-if="activeTab === 'loans'" class="sk-card" style="border-radius:0 var(--radius-lg) var(--radius-lg)">
          <div class="sk-table-wrapper">
            <table class="sk-table">
              <thead><tr><th>Loan #</th><th>Amount</th><th>Monthly</th><th>Outstanding</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-if="!loans.length"><td colspan="5"><div class="empty-state" style="padding:24px"><i class="bi bi-bank2"></i><h5>No loans</h5></div></td></tr>
                <tr v-for="l in loans" :key="l.id">
                  <td><code style="font-size:12px">{{ l.loan_number }}</code></td>
                  <td class="text-mono">GHS {{ fmt(l.principal_amount) }}</td>
                  <td class="text-mono">GHS {{ fmt(l.monthly_repayment) }}</td>
                  <td class="text-mono text-danger">GHS {{ fmt(l.outstanding_balance) }}</td>
                  <td><span class="sk-badge" :class="`badge-${l.status}`">{{ l.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { employeeApi, payrollApi, loanApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()
const employee = ref(null)
const loading = ref(true)
const activeTab = ref('employment')
const payslips = ref([])
const leaveBalances = ref([])
const loans = ref([])

const tabs = [
  { id: 'employment', label: 'Employment', icon: 'bi-briefcase' },
  { id: 'payslips', label: 'Payslips', icon: 'bi-receipt-cutoff' },
  { id: 'leaves', label: 'Leave', icon: 'bi-calendar-check' },
  { id: 'loans', label: 'Loans', icon: 'bi-bank2' },
]

const quickInfo = computed(() => {
  if (!employee.value) return []
  return [
    { label: 'Department', icon: 'bi-diagram-3', value: employee.value.department_name },
    { label: 'Branch', icon: 'bi-building', value: employee.value.branch_name },
    { label: 'Type', icon: 'bi-person-badge', value: employee.value.employment_type?.replace('_', ' ') },
    { label: 'Hire Date', icon: 'bi-calendar', value: fmtDate(employee.value.hire_date) },
    { label: 'Years of Service', icon: 'bi-clock-history', value: `${(employee.value.years_of_service || 0).toFixed(1)} yrs` },
    { label: 'Email', icon: 'bi-envelope', value: employee.value.work_email || employee.value.personal_email },
  ]
})

const employmentFields = computed(() => {
  if (!employee.value) return []
  return [
    { label: 'Employee ID', value: employee.value.employee_id },
    { label: 'Job Title', value: employee.value.job_title },
    { label: 'Employment Type', value: employee.value.employment_type?.replace('_', ' ') },
    { label: 'Department', value: employee.value.department_name },
    { label: 'Manager', value: employee.value.manager_name },
    { label: 'Hire Date', value: fmtDate(employee.value.hire_date) },
    { label: 'Tax Treatment', value: employee.value.tax_treatment?.replace('_', ' ') },
    { label: 'SSNIT Number', value: employee.value.ssnit_number },
    { label: 'TIN', value: employee.value.tin },
    { label: 'Bank', value: employee.value.bank_name },
    { label: 'Account', value: employee.value.account_number },
    { label: 'Payment Method', value: employee.value.payment_method?.replace('_', ' ') },
  ]
})

async function loadTabData(tab) {
  const id = route.params.id
  if (tab === 'payslips' && !payslips.value.length) {
    try { payslips.value = await employeeApi.payslips(id) } catch {}
  }
  if (tab === 'leaves' && !leaveBalances.value.length) {
    try { leaveBalances.value = await employeeApi.leaveBalances(id) } catch {}
  }
  if (tab === 'loans' && !loans.value.length) {
    try { const d = await loanApi.list({ employee: id }); loans.value = d.results || d } catch {}
  }
}

async function downloadPayslip(id) {
  try { await payrollApi.downloadPayslip(id); toast.success('Download started') }
  catch (e) { toast.error('Download failed', e.message) }
}

function statusBadge(s) { return { active: 'badge-active', probation: 'badge-processing', on_leave: 'badge-pending', terminated: 'badge-rejected' }[s] || 'badge-inactive' }
function fmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }
function fmtDate(d) { if (!d) return '–'; return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' }) }

onMounted(async () => {
  try { employee.value = await employeeApi.get(route.params.id) }
  catch (e) { toast.error('Failed to load employee', e.message) }
  finally { loading.value = false }
})
</script>

<style scoped>
.info-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--sk-gray-100); font-size: 12.5px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--sk-gray-500); }
.info-val { font-weight: 500; text-align: right; max-width: 55%; word-break: break-all; }
</style>
