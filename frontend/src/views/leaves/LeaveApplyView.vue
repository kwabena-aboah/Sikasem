<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Apply for Leave</h1>
        <div class="page-subtitle">Submit a leave application for approval</div>
      </div>
      <router-link to="/leaves" class="sk-btn sk-btn-ghost">
        <i class="bi bi-arrow-left"></i> Back
      </router-link>
    </div>

    <!-- No employee profile warning -->
    <div v-if="!hasEmployeeProfile" class="mb-4 p-4"
      style="background:#FEF2F2;border:1px solid #FECACA;border-radius:12px">
      <div style="font-weight:600;color:var(--sk-danger);margin-bottom:6px">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>Account Not Linked
      </div>
      <p style="font-size:13.5px;color:var(--sk-gray-700);margin:0">
        Your user account is not linked to an employee profile. Please contact HR to link your account
        before applying for leave.
      </p>
    </div>

    <div v-else class="row g-4">
      <!-- Form -->
      <div class="col-lg-7">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-calendar-plus-fill" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Leave Application</h5>
          </div>
          <div class="sk-card-body">

            <!-- Employee info banner -->
            <div class="mb-4 p-3 d-flex align-items-center gap-3"
              style="background:var(--sk-gray-50);border:1px solid var(--sk-gray-200);border-radius:10px">
              <div class="avatar">{{ initials }}</div>
              <div>
                <div style="font-weight:600;font-size:14px">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</div>
                <div style="font-size:12px;color:var(--sk-gray-500)">
                  Leave will be automatically linked to your employee profile.
                </div>
              </div>
              <span class="ms-auto sk-badge badge-active">
                <i class="bi bi-check-circle-fill me-1"></i>Linked
              </span>
            </div>

            <form @submit.prevent="submit">
              <!-- Leave type -->
              <div class="sk-form-group">
                <label class="sk-label">Leave Type <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="form.leave_type" required @change="onTypeChange">
                  <option value="">Select leave type…</option>
                  <option
                    v-for="t in eligibleTypes"
                    :key="t.id"
                    :value="t.id"
                  >
                    {{ t.name }} ({{ t.days_per_year }} days/yr — {{ t.is_paid ? 'Paid' : 'Unpaid' }})
                  </option>
                </select>
              </div>

              <!-- Balance card for selected type -->
              <div v-if="selectedBalance" class="mb-4 p-3"
                style="background:var(--sk-gray-50);border:1px solid var(--sk-gray-200);border-radius:10px">
                <div style="font-size:12px;font-weight:600;color:var(--sk-gray-700);margin-bottom:10px">
                  Your {{ new Date().getFullYear() }} Balance
                </div>
                <div class="row g-3 text-center">
                  <div class="col-3">
                    <div style="font-size:22px;font-weight:700;color:var(--sk-success)">{{ selectedBalance.available }}</div>
                    <div style="font-size:11px;color:var(--sk-gray-500)">Available</div>
                  </div>
                  <div class="col-3">
                    <div style="font-size:22px;font-weight:700;color:var(--sk-blue-mid)">{{ selectedBalance.entitled }}</div>
                    <div style="font-size:11px;color:var(--sk-gray-500)">Entitled</div>
                  </div>
                  <div class="col-3">
                    <div style="font-size:22px;font-weight:700;color:var(--sk-warning)">{{ selectedBalance.taken }}</div>
                    <div style="font-size:11px;color:var(--sk-gray-500)">Taken</div>
                  </div>
                  <div class="col-3">
                    <div style="font-size:22px;font-weight:700;color:var(--sk-gray-400)">{{ selectedBalance.pending }}</div>
                    <div style="font-size:11px;color:var(--sk-gray-500)">Pending</div>
                  </div>
                </div>
                <div class="sk-progress mt-2">
                  <div class="sk-progress-bar"
                    :style="`width:${progressPct}%;background:${progressColor}`"></div>
                </div>
              </div>

              <!-- Dates -->
              <div class="row g-3">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Start Date <span class="text-danger">*</span></label>
                    <input type="date" class="sk-input" v-model="form.start_date"
                      required :min="minDate" @change="calcDays" />
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">End Date <span class="text-danger">*</span></label>
                    <input type="date" class="sk-input" v-model="form.end_date"
                      required :min="form.start_date || minDate" @change="calcDays" />
                  </div>
                </div>
              </div>

              <!-- Working days preview -->
              <div v-if="calculatedDays > 0" class="mb-3">
                <div class="p-3 d-flex align-items-center justify-content-between"
                  style="background:var(--sk-blue-mid);border-radius:10px;color:white">
                  <span style="font-size:13.5px">Working days requested</span>
                  <span style="font-size:26px;font-weight:700;font-family:var(--font-mono)">
                    {{ calculatedDays }}
                  </span>
                </div>

                <!-- Insufficient balance warning -->
                <div v-if="selectedBalance && calculatedDays > selectedBalance.available"
                  class="mt-2 p-3"
                  style="background:#FEF2F2;border-radius:8px;font-size:12.5px;color:var(--sk-danger);display:flex;gap:8px;align-items:center">
                  <i class="bi bi-exclamation-triangle-fill"></i>
                  You are requesting {{ calculatedDays }} days but only have {{ selectedBalance.available }} days available.
                  Your application may be rejected.
                </div>
              </div>

              <!-- Reason -->
              <div class="sk-form-group">
                <label class="sk-label">Reason <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span></label>
                <textarea class="sk-textarea" v-model="form.reason"
                  placeholder="Brief description of why you need this leave…"></textarea>
              </div>

              <!-- Handover notes -->
              <div class="sk-form-group">
                <label class="sk-label">
                  Handover Notes
                  <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span>
                </label>
                <textarea class="sk-textarea" v-model="form.handover_notes"
                  style="min-height:70px"
                  placeholder="Who will cover your duties, any pending tasks or handover arrangements…"></textarea>
              </div>

              <!-- Supporting document -->
              <div class="sk-form-group">
                <label class="sk-label">
                  Supporting Document
                  <span style="font-weight:400;color:var(--sk-gray-400)">(if required by leave type)</span>
                </label>
                <input type="file" class="sk-input" style="padding:6px 10px"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" />
              </div>

              <!-- Error -->
              <div v-if="submitError" class="mb-3 p-3"
                style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:var(--sk-danger)">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ submitError }}
              </div>

              <div class="d-flex gap-2 mt-2">
                <router-link to="/leaves" class="sk-btn sk-btn-ghost flex-fill">Cancel</router-link>
                <button type="submit" class="sk-btn sk-btn-primary flex-fill"
                  :disabled="submitting || !form.leave_type || calculatedDays < 1">
                  <span v-if="submitting" class="spinner-border spinner-border-sm"></span>
                  <i v-else class="bi bi-send-fill"></i>
                  Submit Application
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Right: policy info -->
      <div class="col-lg-5">
        <div class="sk-card mb-4">
          <div class="sk-card-header">
            <i class="bi bi-calendar-check" style="color:var(--sk-success)"></i>
            <h5 class="sk-card-title">Leave Balances</h5>
          </div>
          <div class="sk-card-body" style="padding-top:8px">
            <div v-if="balancesLoading" class="text-center p-3">
              <div class="spinner-border spinner-border-sm text-primary"></div>
            </div>
            <div v-else-if="!leaveBalances.length" class="empty-state" style="padding:20px">
              <i class="bi bi-calendar-x"></i>
              <h5>No balances found</h5>
              <p>Contact HR to set up your leave balances</p>
            </div>
            <div v-for="b in leaveBalances" :key="b.leave_type" class="balance-row">
              <div class="d-flex justify-content-between mb-1">
                <span style="font-weight:500;font-size:13px">{{ b.leave_type }}</span>
                <span style="font-size:13px;font-weight:700"
                  :class="b.available > 5 ? 'text-success' : b.available > 0 ? 'text-warning' : 'text-danger'">
                  {{ b.available }} days
                </span>
              </div>
              <div class="sk-progress" style="height:5px">
                <div class="sk-progress-bar"
                  :style="`width:${b.entitled > 0 ? Math.min((b.taken/b.entitled)*100, 100) : 0}%;
                           background:${b.available > 5 ? 'var(--sk-success)' : b.available > 0 ? 'var(--sk-warning)' : 'var(--sk-danger)'}`">
                </div>
              </div>
              <div style="font-size:11px;color:var(--sk-gray-400);margin-top:2px">
                {{ b.taken }} taken of {{ b.entitled }} entitled
              </div>
            </div>
          </div>
        </div>

        <div class="sk-card" style="background:linear-gradient(135deg,var(--sk-dark),#1a3c6e);color:white">
          <div class="sk-card-body">
            <div style="font-size:13.5px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px">
              <i class="bi bi-book-fill" style="color:var(--sk-accent)"></i>
              Ghana Labour Act (Act 651)
            </div>
            <ul style="font-size:12.5px;opacity:.8;line-height:1.7;padding-left:18px;margin:0">
              <li>Annual leave: minimum <strong>15 working days</strong> after 12 months service</li>
              <li>Leave must be taken within <strong>12 months</strong> of accrual</li>
              <li>Maternity leave: <strong>12 weeks</strong> fully paid</li>
              <li>Sick leave must be supported by a medical certificate</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { leaveApi, employeeApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'
import { useAuthStore }  from '@/stores/auth'

const router = useRouter()
const toast  = useToastStore()
const auth   = useAuthStore()

const leaveTypes    = ref([])
const leaveBalances = ref([])
const balancesLoading = ref(true)
const submitting    = ref(false)
const submitError   = ref('')

// ── Employee profile check ─────────────────────────────────────────────────────
const hasEmployeeProfile = computed(() => !!auth.user?.employee_profile_id)

const initials = computed(() => {
  const f = auth.user?.first_name?.[0] || ''
  const l = auth.user?.last_name?.[0]  || ''
  return (f + l).toUpperCase() || '?'
})

// ── Form ───────────────────────────────────────────────────────────────────────
const form = ref({
  leave_type:     '',
  start_date:     '',
  end_date:       '',
  days_requested: 0,
  reason:         '',
  handover_notes: '',
})

const calculatedDays = ref(0)

const minDate = computed(() => new Date().toISOString().split('T')[0])

// Only show leave types eligible for the employee's gender
const eligibleTypes = computed(() => {
  return leaveTypes.value.filter(t => {
    if (!t.gender_specific) return true
    // gender_specific '' = all, 'M' = male only, 'F' = female only
    return !t.gender_specific || t.gender_specific === auth.user?.gender
  })
})

const selectedBalance = computed(() =>
  leaveBalances.value.find(b => {
    const t = leaveTypes.value.find(lt => lt.id === form.value.leave_type)
    return t && b.leave_type === t.name
  }) || null
)

const progressPct = computed(() => {
  if (!selectedBalance.value || !selectedBalance.value.entitled) return 0
  return Math.min((selectedBalance.value.taken / selectedBalance.value.entitled) * 100, 100)
})

const progressColor = computed(() => {
  const avail = selectedBalance.value?.available || 0
  if (avail > 5)  return 'var(--sk-success)'
  if (avail > 0)  return 'var(--sk-warning)'
  return 'var(--sk-danger)'
})

// ── Methods ────────────────────────────────────────────────────────────────────
function onTypeChange() {
  calculatedDays.value = 0
  if (form.value.start_date && form.value.end_date) calcDays()
}

function calcDays() {
  if (!form.value.start_date || !form.value.end_date) return
  const start = new Date(form.value.start_date)
  const end   = new Date(form.value.end_date)
  if (end < start) { calculatedDays.value = 0; return }

  let days = 0
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const dow = d.getDay()
    if (dow !== 0 && dow !== 6) days++ // Mon-Fri only
  }
  calculatedDays.value   = days
  form.value.days_requested = days
}

async function submit() {
  submitError.value = ''

  if (!form.value.leave_type) {
    submitError.value = 'Please select a leave type.'
    return
  }
  if (calculatedDays.value < 1) {
    submitError.value = 'Please select valid start and end dates (minimum 1 working day).'
    return
  }

  submitting.value = true
  try {
    // NOTE: employee is auto-set server-side from request.user.employee_profile
    await leaveApi.apply({
      leave_type:     form.value.leave_type,
      start_date:     form.value.start_date,
      end_date:       form.value.end_date,
      days_requested: form.value.days_requested,
      reason:         form.value.reason,
      handover_notes: form.value.handover_notes,
    })

    toast.success('Application submitted', 'Your leave request is pending approval')
    router.push('/leaves')
  } catch (e) {
    submitError.value = e.message || 'Failed to submit. Please try again.'
  } finally {
    submitting.value = false
  }
}

// ── Load data ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  const empId = auth.user?.employee_profile_id
  balancesLoading.value = true

  try {
    const [typesData] = await Promise.all([
      leaveApi.types(),
    ])
    leaveTypes.value = typesData.results || typesData || []

    if (empId) {
      const balData    = await employeeApi.leaveBalances(empId)
      leaveBalances.value = Array.isArray(balData) ? balData : (balData.results || [])
    }
  } catch (e) {
    console.error('LeaveApplyView load error:', e)
    toast.error('Failed to load leave data', e.message)
  } finally {
    balancesLoading.value = false
  }
})
</script>

<style scoped>
.balance-row {
  padding: 10px 0;
  border-bottom: 1px solid var(--sk-gray-100);
}
.balance-row:last-child { border-bottom: none; }
</style>
