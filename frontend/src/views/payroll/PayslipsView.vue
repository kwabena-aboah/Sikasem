<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">My Payslips</h1>
        <div class="page-subtitle">View and download your payment history</div>
      </div>
    </div>

    <!-- Year tabs -->
    <div class="sk-tabs mb-4">
      <button v-for="y in years" :key="y" class="sk-tab" :class="{ active: selectedYear === y }" @click="selectedYear = y; loadPayslips()">
        {{ y }}
      </button>
    </div>

    <!-- Summary for selected year -->
    <div v-if="yearSummary" class="row g-3 mb-4">
      <div class="col-sm-4">
        <div class="kpi-card">
          <div class="kpi-card-accent" style="background:var(--sk-blue-mid)"></div>
          <div class="kpi-value">GHS {{ formatAmt(yearSummary.totalGross) }}</div>
          <div class="kpi-label">Total Gross ({{ selectedYear }})</div>
        </div>
      </div>
      <div class="col-sm-4">
        <div class="kpi-card">
          <div class="kpi-card-accent" style="background:var(--sk-danger)"></div>
          <div class="kpi-value">GHS {{ formatAmt(yearSummary.totalDeductions) }}</div>
          <div class="kpi-label">Total Deductions</div>
        </div>
      </div>
      <div class="col-sm-4">
        <div class="kpi-card">
          <div class="kpi-card-accent" style="background:var(--sk-success)"></div>
          <div class="kpi-value">GHS {{ formatAmt(yearSummary.totalNet) }}</div>
          <div class="kpi-label">Total Net Pay</div>
        </div>
      </div>
    </div>

    <!-- Payslips table -->
    <div class="sk-card">
      <div class="sk-card-header">
        <i class="bi bi-receipt-cutoff" style="color:var(--sk-blue-mid)"></i>
        <h5 class="sk-card-title">Payslip History</h5>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Gross Pay</th>
              <th>PAYE</th>
              <th>SSNIT</th>
              <th>Deductions</th>
              <th>Net Pay</th>
              <th>Status</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-else-if="!payslips.length"><td colspan="8"><div class="empty-state"><i class="bi bi-receipt-cutoff"></i><h5>No payslips found</h5></div></td></tr>
            <tr v-for="ps in payslips" :key="ps.id">
              <td>
                <div style="font-weight:600">{{ ps.period_name }}</div>
                <div style="font-size:11.5px;color:var(--sk-gray-400)">Pay date: {{ formatDate(ps.payroll_period?.pay_date) }}</div>
              </td>
              <td class="text-mono">GHS {{ formatAmt(ps.gross_pay) }}</td>
              <td class="text-mono text-danger">GHS {{ formatAmt(ps.paye_tax) }}</td>
              <td class="text-mono text-warning">GHS {{ formatAmt(ps.ssnit_employee) }}</td>
              <td class="text-mono text-danger">GHS {{ formatAmt(ps.total_deductions) }}</td>
              <td class="text-mono fw-600 text-success">GHS {{ formatAmt(ps.net_pay) }}</td>
              <td><span class="sk-badge" :class="`badge-${ps.status}`">{{ ps.status }}</span></td>
              <td>
                <div class="d-flex justify-content-end gap-1">
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="viewPayslip(ps)">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="sk-btn sk-btn-primary sk-btn-sm" @click="downloadPayslip(ps.id)">
                    <i class="bi bi-download"></i> PDF
                  </button>
                  <button v-if="ps.status === 'paid'" class="sk-btn sk-btn-ghost sk-btn-sm" @click="openDispute(ps)">
                    <i class="bi bi-flag"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payslip detail modal -->
    <div v-if="selectedPayslip" class="sk-modal-backdrop" @click.self="selectedPayslip = null">
      <div class="sk-modal sk-modal-lg">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Payslip — {{ selectedPayslip.period_name }}</h5>
          <button class="sk-modal-close" @click="selectedPayslip = null"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="row g-4">
            <div class="col-md-6">
              <h6 style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--sk-gray-500);margin-bottom:12px">Earnings</h6>
              <div v-for="item in selectedPayslip.earnings_breakdown" :key="item.code" class="payslip-line">
                <span>{{ item.name }}</span>
                <span class="text-mono">GHS {{ formatAmt(item.amount) }}</span>
              </div>
              <div class="payslip-line fw-600" style="border-top:2px solid var(--sk-gray-300);padding-top:8px;margin-top:4px">
                <span>GROSS PAY</span>
                <span class="text-mono">GHS {{ formatAmt(selectedPayslip.gross_pay) }}</span>
              </div>
            </div>
            <div class="col-md-6">
              <h6 style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--sk-gray-500);margin-bottom:12px">Deductions</h6>
              <div v-for="item in selectedPayslip.deductions_breakdown?.filter(d => d.amount > 0)" :key="item.code" class="payslip-line">
                <span>{{ item.name }}</span>
                <span class="text-mono text-danger">GHS {{ formatAmt(item.amount) }}</span>
              </div>
              <div class="payslip-line fw-600" style="border-top:2px solid var(--sk-gray-300);padding-top:8px;margin-top:4px">
                <span>TOTAL DEDUCTIONS</span>
                <span class="text-mono text-danger">GHS {{ formatAmt(selectedPayslip.total_deductions) }}</span>
              </div>
            </div>
          </div>
          <div class="mt-4 p-4 text-center" style="background:var(--sk-blue-mid);border-radius:12px;color:white">
            <div style="font-size:12px;opacity:.7;margin-bottom:4px">NET PAY</div>
            <div style="font-size:32px;font-weight:800;font-family:var(--font-mono)">GHS {{ formatAmt(selectedPayslip.net_pay) }}</div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="selectedPayslip = null">Close</button>
          <button class="sk-btn sk-btn-primary" @click="downloadPayslip(selectedPayslip.id)">
            <i class="bi bi-download me-1"></i> Download PDF
          </button>
        </div>
      </div>
    </div>

    <!-- Dispute modal -->
    <div v-if="disputePayslip" class="sk-modal-backdrop" @click.self="disputePayslip = null">
      <div class="sk-modal sk-modal-sm">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Dispute Payslip</h5>
          <button class="sk-modal-close" @click="disputePayslip = null"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <p style="font-size:13.5px;color:var(--sk-gray-600)">Please describe the issue with your payslip for {{ disputePayslip.period_name }}.</p>
          <div class="sk-form-group">
            <label class="sk-label">Reason for Dispute</label>
            <textarea class="sk-textarea" v-model="disputeReason" placeholder="Describe the error or discrepancy..."></textarea>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="disputePayslip = null">Cancel</button>
          <button class="sk-btn sk-btn-danger" @click="submitDispute">
            <i class="bi bi-flag me-1"></i> Submit Dispute
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { payrollApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const payslips = ref([])
const loading = ref(true)
const selectedYear = ref(new Date().getFullYear())
const selectedPayslip = ref(null)
const disputePayslip = ref(null)
const disputeReason = ref('')

const years = computed(() => {
  const cur = new Date().getFullYear()
  return [cur, cur - 1, cur - 2]
})

const yearSummary = computed(() => {
  if (!payslips.value.length) return null
  return {
    totalGross: payslips.value.reduce((s, p) => s + Number(p.gross_pay || 0), 0),
    totalDeductions: payslips.value.reduce((s, p) => s + Number(p.total_deductions || 0), 0),
    totalNet: payslips.value.reduce((s, p) => s + Number(p.net_pay || 0), 0),
  }
})

async function loadPayslips() {
  loading.value = true
  try {
    const data = await payrollApi.payslips({ year: selectedYear.value })
    payslips.value = data.results || data
  } catch (e) {
    toast.error('Failed to load payslips', e.message)
  } finally {
    loading.value = false
  }
}

async function viewPayslip(ps) {
  const detail = await payrollApi.getPayslip(ps.id)
  selectedPayslip.value = detail
}

async function downloadPayslip(id) {
  try {
    await payrollApi.downloadPayslip(id)
    toast.success('Download started')
  } catch (e) {
    toast.error('Download failed', e.message)
  }
}

function openDispute(ps) {
  disputePayslip.value = ps
  disputeReason.value = ''
}

async function submitDispute() {
  try {
    await payrollApi.disputePayslip(disputePayslip.value.id, disputeReason.value)
    toast.success('Dispute submitted', 'HR will review your dispute shortly')
    disputePayslip.value = null
    loadPayslips()
  } catch (e) {
    toast.error('Failed to submit dispute', e.message)
  }
}

function formatDate(d) {
  if (!d) return '–'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmt(v) {
  if (!v && v !== 0) return '0.00'
  return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 })
}

onMounted(loadPayslips)
</script>

<style scoped>
.payslip-line {
  display: flex; justify-content: space-between;
  padding: 7px 0; border-bottom: 1px solid var(--sk-gray-100);
  font-size: 13.5px;
}
.payslip-line:last-child { border-bottom: none; }
</style>
