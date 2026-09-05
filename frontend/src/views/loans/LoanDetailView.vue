<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Loan Details</h1>
        <div class="page-subtitle" v-if="loan">{{ loan.loan_number }} — {{ loan.loan_type_name }}</div>
      </div>
      <router-link to="/loans" class="sk-btn sk-btn-ghost"><i class="bi bi-arrow-left"></i> Back</router-link>
    </div>

    <div v-if="loading" class="text-center p-5"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="loan" class="row g-4">
      <!-- Loan summary -->
      <div class="col-lg-4">
        <div class="sk-card mb-4">
          <div class="sk-card-body" style="text-align:center;padding:28px">
            <div style="width:64px;height:64px;background:linear-gradient(135deg,var(--sk-blue-mid),var(--sk-blue-light));border-radius:16px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px;color:white">
              <i class="bi bi-bank2"></i>
            </div>
            <div style="font-size:30px;font-weight:800;font-family:var(--font-mono);color:var(--sk-gray-900)">GHS {{ formatAmt(loan.principal_amount) }}</div>
            <div style="font-size:13px;color:var(--sk-gray-500);margin-top:4px">Principal Amount</div>
            <div class="mt-3"><span class="sk-badge" :class="loanBadge(loan.status)">{{ loan.status }}</span></div>
          </div>
        </div>

        <div class="sk-card mb-4">
          <div class="sk-card-header"><i class="bi bi-info-circle" style="color:var(--sk-accent)"></i><h5 class="sk-card-title">Loan Info</h5></div>
          <div class="sk-card-body" style="padding-top:4px">
            <div v-for="item in loanInfo" :key="item.label" class="info-row">
              <span class="info-label">{{ item.label }}</span>
              <span class="info-val" :class="item.cls">{{ item.value }}</span>
            </div>
          </div>
        </div>

        <!-- Progress -->
        <div v-if="loan.status === 'active'" class="sk-card">
          <div class="sk-card-header"><i class="bi bi-graph-up" style="color:var(--sk-success)"></i><h5 class="sk-card-title">Repayment Progress</h5></div>
          <div class="sk-card-body">
            <div class="text-center mb-3">
              <div style="font-size:36px;font-weight:800;color:var(--sk-success)">{{ repaidPct }}%</div>
              <div style="font-size:12px;color:var(--sk-gray-500)">Repaid</div>
            </div>
            <div class="sk-progress" style="height:10px;border-radius:99px;margin-bottom:12px">
              <div class="sk-progress-bar" :style="`width:${repaidPct}%;background:var(--sk-success)`"></div>
            </div>
            <div class="d-flex justify-content-between" style="font-size:12px;color:var(--sk-gray-500)">
              <span>GHS {{ formatAmt(loan.amount_paid) }} paid</span>
              <span>GHS {{ formatAmt(loan.outstanding_balance) }} left</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Repayment schedule -->
      <div class="col-lg-8">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-calendar2-check" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Repayment Schedule</h5>
            <span style="font-size:12px;color:var(--sk-gray-400);margin-left:auto">{{ repayments.length }} installments</span>
          </div>
          <div class="sk-table-wrapper">
            <table class="sk-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Due Date</th>
                  <th>Amount</th>
                  <th>Principal</th>
                  <th>Interest</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!repayments.length"><td colspan="6"><div class="empty-state"><i class="bi bi-calendar-x"></i><h5>No schedule yet</h5><p>Schedule is created upon disbursement</p></div></td></tr>
                <tr v-for="r in repayments" :key="r.id" :class="{ 'row-overdue': r.status === 'overdue', 'row-paid': r.status === 'deducted' || r.status === 'paid_directly' }">
                  <td style="font-family:var(--font-mono);font-size:12px">{{ r.installment_number }}</td>
                  <td>{{ formatDate(r.due_date) }}</td>
                  <td class="text-mono fw-600">GHS {{ formatAmt(r.amount) }}</td>
                  <td class="text-mono">GHS {{ formatAmt(r.principal) }}</td>
                  <td class="text-mono">{{ r.interest > 0 ? `GHS ${formatAmt(r.interest)}` : '–' }}</td>
                  <td>
                    <span class="sk-badge" :class="repaymentBadge(r.status)">
                      <i class="bi me-1" :class="r.status === 'deducted' ? 'bi-check-circle-fill' : r.status === 'overdue' ? 'bi-exclamation-circle-fill' : 'bi-clock'"></i>
                      {{ repaymentLabel(r.status) }}
                    </span>
                  </td>
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
import { loanApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const toast = useToastStore()
const loan = ref(null)
const repayments = ref([])
const loading = ref(true)

const repaidPct = computed(() => {
  if (!loan.value?.total_amount) return 0
  return Math.round(((loan.value.total_amount - loan.value.outstanding_balance) / loan.value.total_amount) * 100)
})

const loanInfo = computed(() => {
  if (!loan.value) return []
  return [
    { label: 'Loan Number', value: loan.value.loan_number, cls: 'text-mono' },
    { label: 'Type', value: loan.value.loan_type_name },
    { label: 'Principal', value: `GHS ${formatAmt(loan.value.principal_amount)}`, cls: 'fw-600' },
    { label: 'Total Payable', value: `GHS ${formatAmt(loan.value.total_amount)}` },
    { label: 'Monthly', value: `GHS ${formatAmt(loan.value.monthly_repayment)}`, cls: 'text-success fw-600' },
    { label: 'Duration', value: `${loan.value.repayment_months} months` },
    { label: 'Interest', value: loan.value.interest_rate > 0 ? `${(loan.value.interest_rate * 100).toFixed(1)}%` : 'Interest-free' },
    { label: 'Applied', value: formatDate(loan.value.application_date) },
    { label: 'Disbursed', value: formatDate(loan.value.disbursement_date) || '–' },
  ]
})

async function load() {
  try {
    const [loanData, repData] = await Promise.all([
      loanApi.get(route.params.id),
      loanApi.repayments(route.params.id).catch(() => [])
    ])
    loan.value = loanData
    repayments.value = repData.results || repData
  } catch (e) { toast.error('Failed to load loan', e.message) } finally { loading.value = false }
}

function loanBadge(s) { return { pending: 'badge-pending', approved: 'badge-approved', active: 'badge-active-loan', completed: 'badge-completed', rejected: 'badge-rejected' }[s] || 'badge-inactive' }
function repaymentBadge(s) { return { pending: 'badge-pending', deducted: 'badge-paid', paid_directly: 'badge-paid', overdue: 'badge-anomaly', waived: 'badge-cancelled' }[s] || 'badge-inactive' }
function repaymentLabel(s) { return { pending: 'Pending', deducted: 'Deducted', paid_directly: 'Paid', overdue: 'Overdue', waived: 'Waived' }[s] || s }
function formatAmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }
function formatDate(d) { if (!d) return '–'; return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' }) }

onMounted(load)
</script>

<style scoped>
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--sk-gray-100); font-size: 13px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--sk-gray-500); }
.info-val { font-weight: 500; }
.row-paid td { background: #F0FDF4; }
.row-overdue td { background: #FEF2F2; }
</style>
