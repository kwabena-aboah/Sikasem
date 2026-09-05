<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Loans & Advances</h1>
        <div class="page-subtitle">Manage employee loans and salary advances</div>
      </div>
      <router-link v-if="auth.user?.employee_profile_id" to="/loans/apply" class="sk-btn sk-btn-primary">
        <i class="bi bi-wallet2"></i> Request Loan
      </router-link>
    </div>

    <!-- Summary stats -->
    <div class="row g-3 mb-4">
      <div class="col-sm-3" v-for="stat in loanStats" :key="stat.label">
        <div class="kpi-card" style="padding:16px 18px">
          <div class="kpi-card-accent" :style="`background:${stat.color}`"></div>
          <div class="kpi-icon" style="width:36px;height:36px;margin-bottom:10px;font-size:16px" :style="`background:${stat.bg};color:${stat.color}`">
            <i class="bi" :class="stat.icon"></i>
          </div>
          <div style="font-size:20px;font-weight:700">{{ stat.value }}</div>
          <div style="font-size:11.5px;color:var(--sk-gray-500);margin-top:2px">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="sk-tabs">
      <button class="sk-tab" :class="{ active: tab === 'my' }" @click="tab = 'my'">
        <i class="bi bi-person"></i> My Loans
      </button>
      <button v-if="auth.isHR" class="sk-tab" :class="{ active: tab === 'all' }" @click="tab = 'all'">
        <i class="bi bi-people"></i> All Loans
      </button>
    </div>

    <div class="sk-card">
      <div class="sk-card-header">
        <select class="sk-select ms-auto" v-model="filterStatus" @change="loadLoans" style="width:auto">
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th v-if="tab === 'all'">Employee</th>
              <th>Loan #</th>
              <th>Type</th>
              <th>Amount</th>
              <th>Monthly</th>
              <th>Outstanding</th>
              <th>Progress</th>
              <th>Status</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="9" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-else-if="!loans.length"><td colspan="9"><div class="empty-state"><i class="bi bi-bank2"></i><h5>No loans found</h5></div></td></tr>
            <tr v-for="loan in loans" :key="loan.id">
              <td v-if="tab === 'all'">
                <div class="d-flex align-items-center gap-2">
                  <div class="avatar avatar-sm">{{ initials(loan.employee_name) }}</div>
                  <span style="font-weight:500">{{ loan.employee_name }}</span>
                </div>
              </td>
              <td><code style="font-family:var(--font-mono);font-size:12px;background:var(--sk-gray-100);padding:2px 7px;border-radius:4px">{{ loan.loan_number }}</code></td>
              <td>{{ loan.loan_type_name }}</td>
              <td class="text-mono fw-600">GHS {{ formatAmt(loan.principal_amount) }}</td>
              <td class="text-mono">GHS {{ formatAmt(loan.monthly_repayment) }}</td>
              <td class="text-mono" :class="loan.outstanding_balance > 0 ? 'text-danger' : 'text-success'">
                GHS {{ formatAmt(loan.outstanding_balance) }}
              </td>
              <td style="min-width:100px">
                <div v-if="loan.total_amount > 0">
                  <div class="sk-progress mb-1">
                    <div class="sk-progress-bar" :style="`width:${repaidPct(loan)}%;background:var(--sk-success)`"></div>
                  </div>
                  <div style="font-size:10.5px;color:var(--sk-gray-400)">{{ repaidPct(loan) }}% repaid</div>
                </div>
              </td>
              <td><span class="sk-badge" :class="loanBadge(loan.status)">{{ loan.status }}</span></td>
              <td>
                <div class="d-flex justify-content-end gap-1">
                  <router-link :to="`/loans/${loan.id}`" class="sk-btn sk-btn-ghost sk-btn-sm">
                    <i class="bi bi-eye"></i>
                  </router-link>
                  <button v-if="loan.status === 'pending' && auth.isHR" class="sk-btn sk-btn-primary sk-btn-sm" @click="approveLoan(loan)">
                    <i class="bi bi-check-lg"></i> Approve
                  </button>
                  <button v-if="loan.status === 'approved' && auth.isHR" class="sk-btn sk-btn-accent sk-btn-sm" @click="disburseLoan(loan)">
                    <i class="bi bi-send-fill"></i> Disburse
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { loanApi } from '@/utils/api'

const auth = useAuthStore()
const toast = useToastStore()
const loans = ref([])
const loading = ref(true)
const tab = ref('my')
const filterStatus = ref('')

const loanStats = computed(() => {
  const active = loans.value.filter(l => l.status === 'active')
  return [
    { label: 'Active Loans', value: active.length, icon: 'bi-bank2', color: 'var(--sk-blue-mid)', bg: '#EEF4FF' },
    { label: 'Total Outstanding', value: `GHS ${formatAmt(active.reduce((s, l) => s + Number(l.outstanding_balance || 0), 0))}`, icon: 'bi-currency-dollar', color: 'var(--sk-danger)', bg: '#FEE2E2' },
    { label: 'Pending Approval', value: loans.value.filter(l => l.status === 'pending').length, icon: 'bi-clock-fill', color: 'var(--sk-warning)', bg: '#FEF3C7' },
    { label: 'Completed', value: loans.value.filter(l => l.status === 'completed').length, icon: 'bi-check-circle-fill', color: 'var(--sk-success)', bg: '#D1FAE5' },
  ]
})

async function loadLoans() {
  loading.value = true
  try {
    const params = { status: filterStatus.value || undefined }
    if (tab.value === 'my' && auth.user?.employee_profile_id) {
      params.employee = auth.user.employee_profile_id
    }
    const data = await loanApi.list(params)
    loans.value = data.results || data
  } catch (e) {
    toast.error('Failed to load loans', e.message)
  } finally {
    loading.value = false
  }
}

async function approveLoan(loan) {
  try {
    await loanApi.approve(loan.id)
    toast.success('Loan approved', `${loan.loan_number} approved for ${loan.employee_name}`)
    loadLoans()
  } catch (e) { toast.error('Approval failed', e.message) }
}

async function disburseLoan(loan) {
  if (!confirm(`Disburse ${loan.loan_number}? This will activate repayment schedule.`)) return
  try {
    await loanApi.disburse(loan.id)
    toast.success('Loan disbursed', 'Repayment schedule created')
    loadLoans()
  } catch (e) { toast.error('Disbursement failed', e.message) }
}

function repaidPct(loan) {
  if (!loan.total_amount || loan.total_amount == 0) return 0
  return Math.round(((loan.total_amount - loan.outstanding_balance) / loan.total_amount) * 100)
}

function loanBadge(s) {
  return { pending: 'badge-pending', approved: 'badge-approved', active: 'badge-active-loan', completed: 'badge-completed', rejected: 'badge-rejected', disbursed: 'badge-processing', cancelled: 'badge-cancelled', defaulted: 'badge-anomaly' }[s] || 'badge-inactive'
}

function formatAmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }
function initials(n) { if (!n) return '?'; return n.split(' ').map(x => x[0]).join('').toUpperCase().slice(0, 2) }

watch(tab, loadLoans)
onMounted(loadLoans)
</script>
