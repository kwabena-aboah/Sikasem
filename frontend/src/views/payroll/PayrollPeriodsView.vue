<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Payroll Runs</h1>
        <div class="page-subtitle">Manage and process monthly payroll periods</div>
      </div>
      <button v-if="auth.isPayroll" class="sk-btn sk-btn-primary" @click="openNewPeriodModal">
        <i class="bi bi-plus-lg"></i> New Payroll Period
      </button>
    </div>

    <!-- Status overview -->
    <div class="row g-3 mb-4">
      <div class="col-sm-3" v-for="s in statusSummary" :key="s.status">
        <div class="kpi-card" style="padding:16px 18px">
          <div class="kpi-card-accent" :style="`background:${s.color}`"></div>
          <div style="font-size:22px;font-weight:700;color:var(--sk-gray-900)">{{ s.count }}</div>
          <div style="font-size:12px;color:var(--sk-gray-500);margin-top:2px">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- Periods table -->
    <div class="sk-card">
      <div class="sk-card-header">
        <i class="bi bi-cash-stack" style="color:var(--sk-blue-mid)"></i>
        <h5 class="sk-card-title">All Payroll Periods</h5>
        <div class="ms-auto d-flex gap-2">
          <select class="sk-select" v-model="yearFilter" @change="loadPeriods"
            style="width:auto;padding-right:28px">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Pay Date</th>
              <th>Employees</th>
              <th>Gross Pay</th>
              <th>Net Pay</th>
              <th>Status</th>
              <th>Anomalies</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="text-center p-4">
                <div class="spinner-border spinner-border-sm text-primary"></div>
              </td>
            </tr>
            <tr v-else-if="!filteredPeriods.length">
              <td colspan="8">
                <div class="empty-state">
                  <i class="bi bi-cash-stack"></i>
                  <h5>No payroll periods for {{ yearFilter }}</h5>
                  <p>Create a new payroll period to get started</p>
                  <button v-if="auth.isPayroll" class="sk-btn sk-btn-primary sk-btn-sm mt-3"
                    @click="openNewPeriodModal">
                    Create Payroll Period
                  </button>
                </div>
              </td>
            </tr>
            <tr v-for="period in filteredPeriods" :key="period.id">
              <td>
                <div style="font-weight:600">{{ period.name }}</div>
                <div style="font-size:11.5px;color:var(--sk-gray-400)">
                  {{ formatDate(period.period_start) }} – {{ formatDate(period.period_end) }}
                </div>
              </td>
              <td>{{ formatDate(period.pay_date) }}</td>
              <td>
                <span style="font-family:var(--font-mono)">{{ period.employee_count || '—' }}</span>
              </td>
              <td>
                <span class="text-mono fw-600">
                  {{ period.total_gross > 0 ? 'GHS ' + formatAmt(period.total_gross) : '—' }}
                </span>
              </td>
              <td>
                <span class="text-mono fw-600 text-success">
                  {{ period.total_net > 0 ? 'GHS ' + formatAmt(period.total_net) : '—' }}
                </span>
              </td>
              <td>
                <span class="sk-badge" :class="`badge-${period.status}`">
                  {{ period.status_display || period.status }}
                </span>
              </td>
              <td>
                <span v-if="period.ai_anomalies_detected?.length > 0"
                  class="sk-badge badge-anomaly">
                  <i class="bi bi-exclamation-triangle-fill me-1"></i>
                  {{ period.ai_anomalies_detected.length }}
                </span>
                <span v-else class="text-muted" style="font-size:12px">—</span>
              </td>
              <td>
                <div class="d-flex justify-content-end gap-1">
                  <router-link :to="`/payroll/periods/${period.id}`"
                    class="sk-btn sk-btn-ghost sk-btn-sm">
                    <i class="bi bi-eye"></i> View
                  </router-link>
                  <button
                    v-if="(period.effective_status || period.status) === 'draft' && auth.isPayroll"
                    class="sk-btn sk-btn-primary sk-btn-sm"
                    @click="processPeriod(period)"
                    :disabled="processing === period.id">
                    <span v-if="processing === period.id"
                      class="spinner-border spinner-border-sm"></span>
                    <i v-else class="bi bi-play-fill"></i>
                    Process
                  </button>
                  <button
                    v-if="['processing', 'review'].includes(period.effective_status || period.status) && auth.isPayroll"
                    class="sk-btn sk-btn-warning sk-btn-sm"
                    @click="resetAndProcessPeriod(period)"
                    :disabled="processing === period.id">
                    <span v-if="processing === period.id"
                      class="spinner-border spinner-border-sm"></span>
                    <i v-else class="bi bi-arrow-clockwise"></i>
                    Reset &amp; Regenerate
                  </button>
                  <button
                    v-if="(period.effective_status || period.status) === 'review' && auth.isAdmin"
                    class="sk-btn sk-btn-accent sk-btn-sm"
                    @click="startApproval(period)">
                    <i class="bi bi-check-lg"></i> Approve
                  </button>
                  <button
                    v-if="(period.effective_status || period.status) === 'approved' && !period.disbursement_completed && auth.isAdmin"
                    class="sk-btn sk-btn-primary sk-btn-sm"
                    @click="disbursePeriod(period)"
                    :disabled="disbursing === period.id">
                    <span v-if="disbursing === period.id"
                      class="spinner-border spinner-border-sm me-1"></span>
                    <i v-else class="bi bi-send-fill"></i>
                    {{ disbursing === period.id ? 'Disbursing...' : 'Disburse' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── New Period Modal ── -->
    <div v-if="showNewModal" class="sk-modal-backdrop" @click.self="showNewModal = false">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Create New Payroll Period</h5>
          <button class="sk-modal-close" @click="showNewModal = false"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <!-- Quick fill buttons -->
          <div class="mb-4">
            <div style="font-size:12px;font-weight:600;color:var(--sk-gray-600);margin-bottom:8px">Quick Fill</div>
            <div class="d-flex gap-2 flex-wrap">
              <button
                v-for="m in quickMonths" :key="m.label"
                class="sk-btn sk-btn-ghost sk-btn-sm"
                @click="fillMonth(m)">
                {{ m.label }}
              </button>
            </div>
          </div>

          <div class="row g-3">
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Period Name <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="newPeriod.name"
                  placeholder="e.g. June 2025" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Period Start <span class="text-danger">*</span></label>
                <input type="date" class="sk-input" v-model="newPeriod.period_start"
                  @change="autoFillDates" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Period End <span class="text-danger">*</span></label>
                <input type="date" class="sk-input" v-model="newPeriod.period_end" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Pay Date <span class="text-danger">*</span></label>
                <input type="date" class="sk-input" v-model="newPeriod.pay_date" />
              </div>
            </div>
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Notes <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span></label>
                <textarea class="sk-textarea" v-model="newPeriod.notes"
                  style="min-height:60px"
                  placeholder="Any notes for this payroll period…"></textarea>
              </div>
            </div>
          </div>

          <!-- Validation error -->
          <div v-if="createError" class="mt-3 p-3"
            style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:var(--sk-danger)">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ createError }}
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="showNewModal = false">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="createPeriod" :disabled="creating">
            <span v-if="creating" class="spinner-border spinner-border-sm"></span>
            Create Period
          </button>
        </div>
      </div>
    </div>

    <!-- ── Approval Modal (with AI summary) ── -->
    <div v-if="showApproveModal" class="sk-modal-backdrop" @click.self="showApproveModal = false">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Approve: {{ approvalPeriod?.name }}</h5>
          <button class="sk-modal-close" @click="showApproveModal = false"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div v-if="approvalLoading" class="text-center p-4">
            <div class="spinner-border text-primary mb-3"></div>
            <div style="font-size:13px;color:var(--sk-gray-500)">
              Running AI anomaly detection…
            </div>
          </div>
          <div v-else-if="approvalResult">
            <!-- Anomalies found -->
            <div v-if="approvalResult.anomalies_found > 0" class="mb-3 p-4"
              style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px">
              <div style="font-weight:600;color:var(--sk-danger);font-size:13.5px;margin-bottom:8px">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                {{ approvalResult.anomalies_found }} anomalies detected
              </div>
              <p style="font-size:13px;color:var(--sk-gray-700);margin:0;line-height:1.6">
                {{ approvalResult.ai_summary }}
              </p>
            </div>
            <!-- Clean -->
            <div v-else class="mb-3 p-4"
              style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px">
              <div style="font-weight:600;color:var(--sk-success);font-size:13.5px">
                <i class="bi bi-check-circle-fill me-2"></i>
                No anomalies detected — payroll looks clean
              </div>
            </div>
            <div style="font-size:13.5px;color:var(--sk-gray-700);line-height:1.6">
              Approving this payroll will <strong>lock all payslips</strong> and prepare the period
              for disbursement. <strong>This action cannot be undone.</strong>
            </div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="showApproveModal = false">Cancel</button>
          <button v-if="!approvalLoading && approvalResult"
            class="sk-btn sk-btn-accent"
            :disabled="approving"
            @click="confirmApprove">
            <span v-if="approving" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-lg"></i> Confirm Approval
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { payrollApi } from '@/utils/api'

const auth  = useAuthStore()
const toast = useToastStore()

const periods    = ref([])
const loading    = ref(true)
const processing = ref(null)
const creating   = ref(false)
const disbursing = ref(null)
const createError = ref('')
const showNewModal = ref(false)

const yearFilter = ref(new Date().getFullYear())
const years      = computed(() => {
  const c = new Date().getFullYear()
  return [c + 1, c, c - 1, c - 2]
})

const filteredPeriods = computed(() =>
  periods.value.filter(p =>
    new Date(p.period_start).getFullYear() === yearFilter.value
  )
)

const statusSummary = computed(() => {
  const counts = { draft: 0, review: 0, approved: 0, paid: 0 }
  periods.value.forEach(p => { const status = p.effective_status || p.status
    if (status in counts) counts[status]++ })
  return [
    { status: 'draft',    label: 'Draft',        count: counts.draft,    color: 'var(--sk-gray-400)' },
    { status: 'review',   label: 'Under Review',  count: counts.review,   color: 'var(--sk-warning)' },
    { status: 'approved', label: 'Approved',       count: counts.approved, color: 'var(--sk-blue-mid)' },
    { status: 'paid',     label: 'Paid',           count: counts.paid,     color: 'var(--sk-success)' },
  ]
})

// ── New Period ─────────────────────────────────────────────────────────────────
const newPeriod = ref({ name: '', period_start: '', period_end: '', pay_date: '', notes: '' })

// Quick fill with recent months
const quickMonths = computed(() => {
  const months = []
  const today  = new Date()
  for (let i = 0; i < 3; i++) {
    const d = new Date(today.getFullYear(), today.getMonth() - i, 1)
    months.push({
      label: d.toLocaleDateString('en-GH', { month: 'short', year: 'numeric' }),
      year: d.getFullYear(),
      month: d.getMonth(),
    })
  }
  return months
})

function fillMonth(m) {
  const start = new Date(m.year, m.month, 1)
  const end   = new Date(m.year, m.month + 1, 0)
  const pay   = new Date(m.year, m.month, 25)

  newPeriod.value.name         = start.toLocaleDateString('en-GH', { month: 'long', year: 'numeric' })
  newPeriod.value.period_start = toDateString(start)
  newPeriod.value.period_end   = toDateString(end)
  newPeriod.value.pay_date     = toDateString(pay)
}

function autoFillDates() {
  if (!newPeriod.value.period_start) return
  const d = new Date(newPeriod.value.period_start)
  const year = d.getFullYear(), month = d.getMonth()
  const end  = new Date(year, month + 1, 0)
  const pay  = new Date(year, month, 25)

  newPeriod.value.period_end = toDateString(end)
  newPeriod.value.pay_date   = toDateString(pay)
  newPeriod.value.name       = d.toLocaleDateString('en-GH', { month: 'long', year: 'numeric' })
}

function toDateString(d) {
  const y  = d.getFullYear()
  const m  = String(d.getMonth() + 1).padStart(2, '0')
  const dy = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dy}`
}

function openNewPeriodModal() {
  createError.value   = ''
  newPeriod.value     = { name: '', period_start: '', period_end: '', pay_date: '', notes: '' }
  showNewModal.value  = true
}

async function createPeriod() {
  createError.value = ''

  if (!newPeriod.value.name.trim()) {
    createError.value = 'Period name is required.'
    return
  }
  if (!newPeriod.value.period_start || !newPeriod.value.period_end) {
    createError.value = 'Start and end dates are required.'
    return
  }
  if (!newPeriod.value.pay_date) {
    createError.value = 'Pay date is required.'
    return
  }

  creating.value = true
  try {
    // company and created_by are read_only on serializer — set server-side
    await payrollApi.createPeriod({
      name:         newPeriod.value.name,
      period_start: newPeriod.value.period_start,
      period_end:   newPeriod.value.period_end,
      pay_date:     newPeriod.value.pay_date,
      notes:        newPeriod.value.notes,
    })
    toast.success('Payroll period created', `${newPeriod.value.name} is ready to process`)
    showNewModal.value = false
    await loadPeriods()
  } catch (e) {
    createError.value = e.message || 'Failed to create period. Please try again.'
  } finally {
    creating.value = false
  }
}

// ── Period actions ─────────────────────────────────────────────────────────────
async function resetAndProcessPeriod(period) {
  if (!confirm(
    `Reset and regenerate ${period.name}?\n\n` +
    'Any payslips currently attached to this failed run will be cleared, then payroll will be recalculated.'
  )) return

  processing.value = period.id
  try {
    await payrollApi.resetPeriod(period.id)
    const result = await payrollApi.processPeriod(period.id)
    const summary = result.result || result
    await loadPeriods()
    toast.success(
      'Payroll regenerated',
      `${summary.processed || 0} employee(s) calculated successfully`
    )
  } catch (e) {
    toast.error('Regeneration failed', e.message)
    await loadPeriods()
  } finally {
    processing.value = null
  }
}

async function processPeriod(period) {
  processing.value = period.id
  try {
    const result = await payrollApi.processPeriod(period.id)
    const summary = result.result || result
    await loadPeriods()
    if (summary.missing_salary_count > 0) {
      const names = (summary.errors || [])
        .filter(item => item.error?.includes('salary assignment'))
        .map(item => item.employee_name)
        .join(', ')
      toast.warning(
        `Payroll processed: ${summary.selected_count || 0} selected`,
        `${summary.missing_salary_count} employee(s) skipped for missing salary assignment${names ? `: ${names}` : ''}`
      )
    } else {
      toast.success('Payroll processed', `${summary.processed || 0} employees calculated successfully`)
    }
  } catch (e) {
    toast.error('Processing failed', e.message)
  } finally {
    processing.value = null
  }
}

// Approval flow
const showApproveModal = ref(false)
const approvalPeriod   = ref(null)
const approvalResult   = ref(null)
const approvalLoading  = ref(false)
const approving        = ref(false)

async function startApproval(period) {
  approvalPeriod.value  = period
  approvalResult.value  = null
  approvalLoading.value = true
  showApproveModal.value = true

  try {
    const data = await payrollApi.periodAnomalies(period.id)
    approvalResult.value = {
      anomalies_found: data.count || (data.anomalies || []).length,
      ai_summary: data.ai_summary || (data.anomalies?.length ? `${data.anomalies.length} anomaly/anomalies detected in this pay run.` : ''),
    }
  } catch (e) {
    approvalResult.value = { anomalies_found: 0, ai_summary: '' }
  } finally {
    approvalLoading.value = false
  }
}

async function confirmApprove() {
  if (!approvalPeriod.value) return
  approving.value = true
  try {
    await payrollApi.approvePeriod(approvalPeriod.value.id)
    toast.success(
      'Payroll approved',
      `${approvalPeriod.value.name} has been approved and is ready for disbursement`
    )
    showApproveModal.value = false
    approvalPeriod.value   = null
    approvalResult.value   = null
    await loadPeriods()
  } catch (e) {
    toast.error('Approval failed', e.message)
  } finally {
    approving.value = false
  }
}

async function disbursePeriod(period) {
  if (!confirm(
    `Disburse payments for ${period.name}?\n\n` +
    `This will initiate real money transfers to ${period.employee_count} employees. ` +
    `Total: GHS ${formatAmt(period.total_net)}`
  )) return

  disbursing.value = period.id
  toast.info('Disbursement started', 'Processing payments via Paystack. Please wait...')

  try {
    const data = await payrollApi.disbursePeriod(period.id)
    const result = data.result || data
    const successCount = result.success || 0
    const queuedCount  = result.queued  || 0
    const failedCount  = result.failed  || 0

    if (failedCount > 0 && successCount === 0 && queuedCount === 0) {
      toast.error('Disbursement failed', `All ${failedCount} payments failed. Check employee payment details.`)
    } else if (failedCount > 0) {
      toast.warning('Disbursement partially completed',
        `${successCount + queuedCount} sent, ${failedCount} failed. Review payment records for details.`)
    } else {
      toast.success('Disbursement completed',
        `${successCount + queuedCount} payments sent successfully via Paystack`)
    }
    await loadPeriods()
    window.dispatchEvent(new CustomEvent('notification-updated'))
  } catch (e) {
    toast.error('Disbursement failed', e.message || 'Paystack could not start this payout.')
  } finally {
    disbursing.value = null
    window.dispatchEvent(new CustomEvent('notification-updated'))
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────
async function loadPeriods() {
  loading.value = true
  try {
    const data     = await payrollApi.periods()
    periods.value  = data.results || data || []
  } catch (e) {
    toast.error('Failed to load payroll periods', e.message)
  } finally {
    loading.value = false
  }
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmt(v) {
  if (!v && v !== 0) return '0.00'
  return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 })
}

onMounted(loadPeriods)
</script>
