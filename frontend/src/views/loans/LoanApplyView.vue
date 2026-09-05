<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Request a Loan</h1>
        <div class="page-subtitle">Submit a loan or salary advance request</div>
      </div>
      <router-link to="/loans" class="sk-btn sk-btn-ghost">
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
        before applying for a loan.
      </p>
    </div>

    <div v-else class="row g-4">
      <!-- Application form -->
      <div class="col-lg-7">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-wallet2" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Loan Application</h5>
          </div>
          <div class="sk-card-body">
            <!-- Employee info banner (auto-linked) -->
            <div class="mb-4 p-3 d-flex align-items-center gap-3"
              style="background:var(--sk-gray-50);border:1px solid var(--sk-gray-200);border-radius:10px">
              <div class="avatar">{{ initials }}</div>
              <div>
                <div style="font-weight:600;font-size:14px">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</div>
                <div style="font-size:12px;color:var(--sk-gray-500)">
                  Your loan will be automatically linked to your employee profile.
                </div>
              </div>
              <span class="ms-auto sk-badge badge-active">
                <i class="bi bi-check-circle-fill me-1"></i>Linked
              </span>
            </div>

            <form @submit.prevent="submit">
              <!-- Loan Type -->
              <div class="sk-form-group">
                <label class="sk-label">Loan Type <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="form.loan_type" required @change="onTypeChange">
                  <option value="">Select loan type…</option>
                  <option v-for="t in loanTypes" :key="t.id" :value="t.id">
                    {{ t.name }} — Max GHS {{ formatAmt(t.max_amount) }}
                    ({{ t.interest_type === 'none' ? 'Interest-free' : `${(t.interest_rate * 100).toFixed(1)}% ${t.interest_type}` }})
                  </option>
                </select>
                <div v-if="loanTypes.length === 0 && !typesLoading"
                  style="font-size:11.5px;color:var(--sk-warning);margin-top:4px">
                  <i class="bi bi-exclamation-triangle me-1"></i>
                  No loan types configured. Contact HR to set up loan types.
                </div>
              </div>

              <div class="row g-3">
                <!-- Amount -->
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Principal Amount (GHS) <span class="text-danger">*</span></label>
                    <div class="sk-input-group">
                      <i class="bi bi-currency-dollar input-icon"></i>
                      <input
                        type="number" class="sk-input"
                        v-model.number="form.principal_amount"
                        :max="selectedType?.max_amount || 999999"
                        :min="100"
                        step="50"
                        required
                        @input="calcRepayment"
                      />
                    </div>
                    <div v-if="selectedType"
                      style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                      Max: GHS {{ formatAmt(selectedType.max_amount) }}
                    </div>
                  </div>
                </div>

                <!-- Repayment months -->
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Repayment Period (months) <span class="text-danger">*</span></label>
                    <select class="sk-select" v-model.number="form.repayment_months" required @change="calcRepayment">
                      <option v-for="m in availableMonths" :key="m" :value="m">
                        {{ m }} month{{ m > 1 ? 's' : '' }}
                      </option>
                    </select>
                    <div v-if="selectedType"
                      style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                      Max: {{ selectedType.max_months }} months
                    </div>
                  </div>
                </div>
              </div>

              <!-- Repayment preview card -->
              <div v-if="monthlyRepayment > 0" class="mb-4">
                <div class="p-4" style="background:linear-gradient(135deg,var(--sk-blue),var(--sk-blue-mid));border-radius:12px;color:white">
                  <div style="font-size:12px;opacity:.7;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px">Repayment Summary</div>
                  <div class="row g-3 text-center">
                    <div class="col-4">
                      <div style="font-size:11px;opacity:.65;margin-bottom:4px">Principal</div>
                      <div style="font-size:17px;font-weight:700;font-family:var(--font-mono)">
                        GHS {{ formatAmt(form.principal_amount) }}
                      </div>
                    </div>
                    <div class="col-4">
                      <div style="font-size:11px;opacity:.65;margin-bottom:4px">Monthly Payment</div>
                      <div style="font-size:17px;font-weight:700;font-family:var(--font-mono)">
                        GHS {{ formatAmt(monthlyRepayment) }}
                      </div>
                    </div>
                    <div class="col-4">
                      <div style="font-size:11px;opacity:.65;margin-bottom:4px">Total Payable</div>
                      <div style="font-size:17px;font-weight:700;font-family:var(--font-mono)">
                        GHS {{ formatAmt(totalAmount) }}
                      </div>
                    </div>
                  </div>
                  <div v-if="totalAmount > form.principal_amount" class="mt-3"
                    style="font-size:11.5px;opacity:.6;text-align:center">
                    Interest: GHS {{ formatAmt(totalAmount - form.principal_amount) }}
                  </div>
                </div>
              </div>

              <!-- Purpose -->
              <div class="sk-form-group">
                <label class="sk-label">Purpose / Reason <span class="text-danger">*</span></label>
                <textarea
                  class="sk-textarea"
                  v-model="form.purpose"
                  placeholder="Explain the purpose of this loan request…"
                  required
                ></textarea>
              </div>

              <!-- Error -->
              <div v-if="submitError" class="mb-3 p-3"
                style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;font-size:13px;color:var(--sk-danger)">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ submitError }}
              </div>

              <div class="d-flex gap-2 mt-2">
                <router-link to="/loans" class="sk-btn sk-btn-ghost flex-fill">Cancel</router-link>
                <button type="submit" class="sk-btn sk-btn-primary flex-fill" :disabled="submitting || !form.loan_type">
                  <span v-if="submitting" class="spinner-border spinner-border-sm"></span>
                  <i v-else class="bi bi-send-fill"></i>
                  Submit Application
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Right panel: loan type details -->
      <div class="col-lg-5">
        <div class="sk-card mb-4">
          <div class="sk-card-header">
            <i class="bi bi-info-circle" style="color:var(--sk-accent)"></i>
            <h5 class="sk-card-title">Available Loan Types</h5>
          </div>
          <div class="sk-card-body" style="padding-top:8px">
            <div v-if="typesLoading" class="text-center p-4">
              <div class="spinner-border spinner-border-sm text-primary"></div>
            </div>
            <div v-else-if="loanTypes.length === 0" class="empty-state" style="padding:24px">
              <i class="bi bi-bank2"></i>
              <h5>No loan types</h5>
              <p>Contact HR to configure loan types</p>
            </div>
            <div
              v-for="t in loanTypes" :key="t.id"
              class="loan-type-card"
              :class="{ active: form.loan_type === t.id }"
              @click="form.loan_type = t.id; onTypeChange()"
            >
              <div class="d-flex justify-content-between align-items-start">
                <div style="font-weight:600;font-size:13.5px">{{ t.name }}</div>
                <span class="sk-badge badge-active" style="font-size:10px">
                  {{ t.interest_type === 'none' ? 'Interest-free' : `${(t.interest_rate * 100).toFixed(1)}%` }}
                </span>
              </div>
              <div class="mt-2" style="font-size:12px;color:var(--sk-gray-500)">
                <span class="me-3"><i class="bi bi-currency-dollar me-1"></i>Max GHS {{ formatAmt(t.max_amount) }}</span>
                <span><i class="bi bi-calendar me-1"></i>Up to {{ t.max_months }} months</span>
              </div>
              <div v-if="t.min_service_months > 0" style="font-size:11.5px;color:var(--sk-gray-400);margin-top:4px">
                <i class="bi bi-clock me-1"></i>Min {{ t.min_service_months }} months service required
              </div>
            </div>
          </div>
        </div>

        <!-- Policy note -->
        <div class="sk-card" style="background:linear-gradient(135deg,var(--sk-dark),#1a3c6e);color:white">
          <div class="sk-card-body">
            <div style="font-size:13.5px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px">
              <i class="bi bi-shield-fill-check" style="color:var(--sk-accent)"></i>
              Loan Policy
            </div>
            <ul style="font-size:12.5px;opacity:.8;line-height:1.7;padding-left:18px;margin:0">
              <li>Applications are reviewed within 3 working days</li>
              <li>Repayments are deducted automatically from monthly salary</li>
              <li>Maximum of {{ maxActiveLoans }} active loan(s) at a time</li>
              <li>Approval subject to HR and management discretion</li>
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
import { loanApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const toast  = useToastStore()
const auth   = useAuthStore()

const loanTypes   = ref([])
const typesLoading = ref(true)
const submitting  = ref(false)
const submitError = ref('')

// ── Employee profile check ─────────────────────────────────────────────────────
// The backend auto-sets employee from request.user.employee_profile
// We just need to verify the user has one before showing the form
const hasEmployeeProfile = computed(() => !!auth.user?.employee_profile_id)

const initials = computed(() => {
  const f = auth.user?.first_name?.[0] || ''
  const l = auth.user?.last_name?.[0]  || ''
  return (f + l).toUpperCase() || '?'
})

const maxActiveLoans = computed(() => {
  if (!loanTypes.value.length) return 1
  return Math.max(...loanTypes.value.map(t => t.max_active_loans || 1))
})

// ── Form ───────────────────────────────────────────────────────────────────────
const form = ref({
  loan_type:         '',
  principal_amount:  0,
  repayment_months:  12,
  purpose:           '',
  total_amount:      0,
  monthly_repayment: 0,
})

// ── Computed helpers ───────────────────────────────────────────────────────────
const selectedType = computed(() =>
  loanTypes.value.find(t => t.id === form.value.loan_type) || null
)

const availableMonths = computed(() => {
  const max = selectedType.value?.max_months || 24
  return Array.from({ length: max }, (_, i) => i + 1)
})

const monthlyRepayment = computed(() => {
  const p = form.value.principal_amount
  const n = form.value.repayment_months
  if (!p || !n || n < 1) return 0

  const rate = parseFloat(selectedType.value?.interest_rate || 0)
  if (rate === 0) return p / n

  // Reducing balance formula
  return (p * rate) / (1 - Math.pow(1 + rate, -n))
})

const totalAmount = computed(() =>
  monthlyRepayment.value * form.value.repayment_months
)

// ── Methods ────────────────────────────────────────────────────────────────────
function onTypeChange() {
  if (!selectedType.value) return
  // Clamp months to type maximum
  if (form.value.repayment_months > selectedType.value.max_months) {
    form.value.repayment_months = selectedType.value.max_months
  }
  // Clamp amount to type maximum
  if (form.value.principal_amount > selectedType.value.max_amount) {
    form.value.principal_amount = selectedType.value.max_amount
  }
  calcRepayment()
}

function calcRepayment() {
  form.value.monthly_repayment = monthlyRepayment.value
  form.value.total_amount      = totalAmount.value
}

async function submit() {
  if (!form.value.loan_type) {
    submitError.value = 'Please select a loan type.'
    return
  }
  if (!form.value.principal_amount || form.value.principal_amount < 100) {
    submitError.value = 'Please enter a valid loan amount (min GHS 100).'
    return
  }
  if (!form.value.purpose.trim()) {
    submitError.value = 'Please provide a reason for the loan.'
    return
  }

  submitError.value = ''
  submitting.value  = true

  try {
    // NOTE: employee is set server-side from request.user.employee_profile
    // We do NOT send employee in the payload
    await loanApi.apply({
      loan_type:         form.value.loan_type,
      principal_amount:  form.value.principal_amount,
      repayment_months:  form.value.repayment_months,
      purpose:           form.value.purpose.trim(),
      total_amount:      totalAmount.value,
      monthly_repayment: monthlyRepayment.value,
    })

    toast.success('Application submitted', 'Your loan request is pending HR approval')
    router.push('/loans')
  } catch (e) {
    submitError.value = e.message || 'Failed to submit loan application. Please try again.'
  } finally {
    submitting.value = false
  }
}

function formatAmt(v) {
  if (!v && v !== 0) return '0.00'
  return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 })
}

// ── Load loan types ────────────────────────────────────────────────────────────
onMounted(async () => {
  typesLoading.value = true
  try {
    const data        = await loanApi.types()
    loanTypes.value   = data.results || data || []
  } catch (e) {
    toast.error('Failed to load loan types', e.message)
  } finally {
    typesLoading.value = false
  }
})
</script>

<style scoped>
.loan-type-card {
  padding: 12px 14px;
  border: 1.5px solid var(--sk-gray-200);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  cursor: pointer;
  transition: var(--transition);
}
.loan-type-card:hover {
  border-color: var(--sk-blue-light);
  background: #f7faff;
}
.loan-type-card.active {
  border-color: var(--sk-blue-mid);
  background: #EEF4FF;
}
</style>
