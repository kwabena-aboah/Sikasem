<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <div class="page-subtitle">Configure company payroll and HR settings</div>
      </div>

      <button
        class="sk-btn sk-btn-primary"
        @click="saveSettings"
        :disabled="saving"
      >
        <span v-if="saving" class="spinner-border spinner-border-sm"></span>
        <i v-else class="bi bi-floppy-fill"></i>
        Save Changes
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center p-5">
      <div class="spinner-border text-primary mb-3"></div>
      <div style="font-size:13px;color:var(--sk-gray-500)">
        Loading company settings…
      </div>
    </div>

    <!-- Error -->
    <div
      v-else-if="loadError"
      class="mb-4 p-4"
      style="background:#FEE2E2;border:1px solid #FECACA;border-radius:12px;color:var(--sk-danger)"
    >
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ loadError }}
    </div>

    <div v-else class="row g-4">
      <!-- Sidebar navigation -->
      <div class="col-lg-3">
        <div class="sk-card" style="padding:8px">
          <button
            v-for="s in sections"
            :key="s.id"
            class="settings-nav-btn"
            :class="{ active: activeSection === s.id }"
            @click="activeSection = s.id"
          >
            <i class="bi" :class="s.icon"></i>
            {{ s.label }}
          </button>
        </div>

        <!-- Info pill -->
        <div
          class="mt-3 p-3"
          style="background:var(--sk-gray-50);border:1px solid var(--sk-gray-200);border-radius:10px;font-size:12px;color:var(--sk-gray-500)"
        >
          <i class="bi bi-building me-2"></i>
          <strong>{{ company.name || 'Your Company' }}</strong><br />
          <span v-if="company.tin" class="mt-1 d-block">
            TIN: {{ company.tin }}
          </span>
        </div>
      </div>

      <!-- Content panel -->
      <div class="col-lg-9">
        <!-- Company Info -->
        <div v-if="activeSection === 'company'" class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-building" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Company Information</h5>
          </div>

          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Company Name</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.name"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Trading Name</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.trading_name"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Registration Number</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.registration_number"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">TIN (Tax Identification Number)</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.tin"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">SSNIT Employer Code</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.ssnit_employer_code"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Email</label>
                  <input
                    type="email"
                    class="sk-input"
                    v-model="company.email"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Phone</label>
                  <input
                    type="tel"
                    class="sk-input"
                    v-model="company.phone"
                    placeholder="+233..."
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Website</label>
                  <input
                    type="url"
                    class="sk-input"
                    v-model="company.website"
                    placeholder="https://..."
                  />
                </div>
              </div>

              <div class="col-12">
                <div class="sk-form-group">
                  <label class="sk-label">Address</label>
                  <textarea
                    class="sk-textarea"
                    v-model="company.address"
                    style="min-height:70px"
                  ></textarea>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">City / Town</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.city"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Region</label>
                  <select class="sk-select" v-model="company.region">
                    <option value="">Select region…</option>
                    <option
                      v-for="r in ghanaRegions"
                      :key="r"
                      :value="r"
                    >
                      {{ r }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Currency</label>
                  <select class="sk-select" v-model="company.currency">
                    <option value="GHS">GHS — Ghana Cedi</option>
                    <option value="USD">USD — US Dollar</option>
                    <option value="GBP">GBP — British Pound</option>
                    <option value="EUR">EUR — Euro</option>
                  </select>
                </div>
              </div>

              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Timezone</label>
                  <select class="sk-select" v-model="company.timezone">
                    <option value="Africa/Accra">Africa/Accra (GMT+0)</option>
                    <option value="Africa/Lagos">Africa/Lagos (GMT+1)</option>
                    <option value="Africa/Nairobi">Africa/Nairobi (GMT+3)</option>
                  </select>
                </div>
              </div>

              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Fiscal Year Start</label>
                  <input
                    type="text"
                    class="sk-input"
                    v-model="company.fiscal_year_start"
                    placeholder="01-01"
                    maxlength="5"
                  />
                  <div style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                    Format: MM-DD
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Payroll Config -->
        <div v-if="activeSection === 'payroll'" class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-cash-stack" style="color:var(--sk-success)"></i>
            <h5 class="sk-card-title">Payroll Configuration</h5>
          </div>

          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Payroll Cycle</label>
                  <select class="sk-select" v-model="company.payroll_cycle">
                    <option value="monthly">Monthly</option>
                    <option value="bi_weekly">Bi-Weekly</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Payroll Day of Month</label>
                  <input
                    type="number"
                    class="sk-input"
                    v-model.number="company.payroll_day"
                    min="1"
                    max="31"
                  />
                  <div style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                    Day salaries are processed each month
                  </div>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Overtime Rate Multiplier</label>
                  <input
                    type="number"
                    class="sk-input"
                    v-model.number="payrollSettings.overtime_rate_multiplier"
                    min="1"
                    max="5"
                    step="0.1"
                  />
                  <div style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                    e.g. 1.5 = time and a half
                  </div>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Late Penalty (GHS per minute late)</label>
                  <input
                    type="number"
                    class="sk-input"
                    v-model.number="payrollSettings.late_penalty_per_minute"
                    min="0"
                    step="0.01"
                    :disabled="!payrollSettings.enable_late_penalty"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tax & Compliance -->
        <div v-if="activeSection === 'tax'" class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-receipt" style="color:var(--sk-warning)"></i>
            <h5 class="sk-card-title">Tax &amp; Compliance (Ghana)</h5>
          </div>

          <div class="sk-card-body">
            <div
              v-for="tog in taxToggles"
              :key="tog.key"
              class="toggle-row"
            >
              <div>
                <div style="font-weight:500;font-size:13.5px">
                  {{ tog.label }}
                </div>
                <div style="font-size:12px;color:var(--sk-gray-500)">
                  {{ tog.desc }}
                </div>
              </div>

              <label class="toggle-switch">
                <input
                  type="checkbox"
                  v-model="payrollSettings[tog.key]"
                />
                <span class="toggle-slider"></span>
              </label>
            </div>

            <!-- Tier 3 sub-settings -->
            <div
              v-if="payrollSettings.enable_tier3"
              class="mt-4 p-3"
              style="background:var(--sk-gray-50);border-radius:10px;border:1px solid var(--sk-gray-200)"
            >
              <div style="font-size:13px;font-weight:600;margin-bottom:12px;color:var(--sk-gray-800)">
                Tier 3 (Voluntary Pension) Contribution Rates
              </div>

              <div class="row g-3">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Employee Rate (%)</label>
                    <input
                      type="number"
                      class="sk-input"
                      v-model.number="tier3EmployeeRatePct"
                      min="0"
                      max="20"
                      step="0.5"
                    />
                  </div>
                </div>

                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Employer Rate (%)</label>
                    <input
                      type="number"
                      class="sk-input"
                      v-model.number="tier3EmployerRatePct"
                      min="0"
                      max="20"
                      step="0.5"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- GRA compliance note -->
            <div
              class="mt-4 p-3"
              style="background:#FFF8E1;border:1px solid #FFE082;border-radius:10px;font-size:12.5px;color:#795548"
            >
              <i class="bi bi-info-circle-fill me-2" style="color:#F57F17"></i>
              <strong>Ghana Compliance:</strong>
              PAYE must be remitted to GRA by the 15th of the following month.
              SSNIT contributions are due by the 14th via SSNIT's online portal.
            </div>
          </div>
        </div>

        <!-- Leave Policy -->
        <div v-if="activeSection === 'leave'" class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-calendar-check" style="color:var(--sk-success)"></i>
            <h5 class="sk-card-title">Leave Policy</h5>
          </div>

          <div class="sk-card-body">
            <div class="row g-3">
              <div
                class="col-md-6"
                v-for="lf in leaveFields"
                :key="lf.key"
              >
                <div class="sk-form-group">
                  <label class="sk-label">{{ lf.label }}</label>
                  <input
                    type="number"
                    class="sk-input"
                    v-model.number="payrollSettings[lf.key]"
                    min="0"
                  />
                  <div style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                    {{ lf.note }}
                  </div>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Leave Accrual Method</label>
                  <select
                    class="sk-select"
                    v-model="payrollSettings.leave_accrual_method"
                  >
                    <option value="monthly">Monthly (accrued each month)</option>
                    <option value="annual">Annual (granted at start of year)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Payment Settings -->
        <div v-if="activeSection === 'payment'" class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-credit-card" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Payment Settings</h5>
          </div>

          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Payment Provider</label>
                  <select
                    class="sk-select"
                    v-model="payrollSettings.payment_provider"
                  >
                    <option value="paystack">Paystack</option>
                    <option value="manual">Manual (Bank Transfer)</option>
                  </select>
                </div>
              </div>

              <div class="col-md-6 d-flex align-items-end pb-3">
                <label
                  class="d-flex align-items-center gap-2"
                  style="cursor:pointer;font-size:13.5px"
                >
                  <input
                    type="checkbox"
                    v-model="payrollSettings.auto_disburse"
                  />
                  <span>Auto-disburse after payroll approval</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { companyApi } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const activeSection = ref('company')

// Company data
const company = ref({
  id: '',
  name: '',
  trading_name: '',
  registration_number: '',
  tin: '',
  ssnit_employer_code: '',
  email: '',
  phone: '',
  website: '',
  address: '',
  city: '',
  region: '',
  currency: 'GHS',
  timezone: 'Africa/Accra',
  payroll_day: 25,
  payroll_cycle: 'monthly',
  fiscal_year_start: '01-01',
})

// Payroll settings
const payrollSettings = ref({
  overtime_rate_multiplier: 1.5,
  late_penalty_per_minute: 0,
  enable_late_penalty: false,
  enable_paye: true,
  enable_ssnit: true,
  enable_tier2: true,
  enable_tier3: false,
  tier3_employee_rate: 0.05,
  tier3_employer_rate: 0,
  annual_leave_days: 15,
  sick_leave_days: 14,
  maternity_leave_days: 84,
  paternity_leave_days: 5,
  leave_accrual_method: 'monthly',
  payment_provider: 'paystack',
  auto_disburse: false,
  notify_payslip_ready: true,
  notify_leave_approved: true,
  notify_loan_approved: true,
  notify_payroll_processed: true,
})

// Tier 3 rates shown as percentages in UI but stored as decimals
const tier3EmployeeRatePct = computed({
  get() {
    return Math.round((payrollSettings.value.tier3_employee_rate || 0) * 100 * 10) / 10
  },
  set(value) {
    payrollSettings.value.tier3_employee_rate = Number(value || 0) / 100
  },
})

const tier3EmployerRatePct = computed({
  get() {
    return Math.round((payrollSettings.value.tier3_employer_rate || 0) * 100 * 10) / 10
  },
  set(value) {
    payrollSettings.value.tier3_employer_rate = Number(value || 0) / 100
  },
})

// Static lists
const sections = [
  { id: 'company', label: 'Company Info', icon: 'bi-building' },
  { id: 'payroll', label: 'Payroll', icon: 'bi-cash-stack' },
  { id: 'tax', label: 'Tax & Compliance', icon: 'bi-receipt' },
  { id: 'leave', label: 'Leave Policy', icon: 'bi-calendar-check' },
  { id: 'payment', label: 'Payment', icon: 'bi-credit-card' },
]

const taxToggles = [
  {
    key: 'enable_paye',
    label: 'PAYE Tax',
    desc: 'Calculate and deduct PAYE from employee salaries (Ghana GRA)',
  },
  {
    key: 'enable_ssnit',
    label: 'SSNIT (Tier 1)',
    desc: 'Mandatory 5.5% employee + 13% employer SSNIT contribution',
  },
  {
    key: 'enable_tier2',
    label: 'Tier 2 Pension',
    desc: '2.5% employer contribution to occupational pension scheme (NPRA)',
  },
  {
    key: 'enable_tier3',
    label: 'Tier 3 (Voluntary)',
    desc: 'Voluntary provident fund — configure rates below',
  },
  {
    key: 'enable_late_penalty',
    label: 'Late Arrival Penalty',
    desc: 'Deduct from salary for late arrivals (configure minutes threshold in shifts)',
  },
]

const leaveFields = [
  {
    key: 'annual_leave_days',
    label: 'Annual Leave (days)',
    note: 'Ghana minimum: 15 days (Labour Act 2003, s.31)',
  },
  {
    key: 'sick_leave_days',
    label: 'Sick Leave (days)',
    note: 'Per calendar year',
  },
  {
    key: 'maternity_leave_days',
    label: 'Maternity Leave (days)',
    note: 'Ghana standard: 84 days (12 weeks)',
  },
  {
    key: 'paternity_leave_days',
    label: 'Paternity Leave (days)',
    note: 'For male employees',
  },
]

const ghanaRegions = [
  'Ahafo',
  'Ashanti',
  'Bono',
  'Bono East',
  'Central',
  'Eastern',
  'Greater Accra',
  'North East',
  'Northern',
  'Oti',
  'Savannah',
  'Upper East',
  'Upper West',
  'Volta',
  'Western',
  'Western North',
]

// Load company and settings
onMounted(async () => {
  loading.value = true
  loadError.value = ''

  try {
    const listData = await companyApi.list()
    const list = listData?.results || listData || []

    if (!Array.isArray(list) || list.length === 0) {
      loadError.value = 'No company linked to your account. Please contact your system administrator.'
      return
    }

    const c = list[0]

    company.value = {
      ...company.value,
      ...c,
      id: c.id,
    }

    if (c.id) {
      try {
        const settingsData = await companyApi.getSettings(c.id)

        if (settingsData) {
          Object.keys(payrollSettings.value).forEach((key) => {
            if (settingsData[key] !== undefined && settingsData[key] !== null) {
              payrollSettings.value[key] = settingsData[key]
            }
          })
        }
      } catch (error) {
        console.warn(
          'Could not load payroll settings, using defaults:',
          error?.message || error
        )
      }
    }
  } catch (error) {
    loadError.value = `Failed to load settings: ${error?.message || 'Unknown error'}`
    console.error('Settings load error:', error)
  } finally {
    loading.value = false
  }
})

// Save settings
async function saveSettings() {
  if (!company.value.id) {
    toast.error('Cannot save', 'No company ID found. Please refresh the page.')
    return
  }

  saving.value = true

  try {
    await companyApi.update(company.value.id, {
      name: company.value.name,
      trading_name: company.value.trading_name,
      registration_number: company.value.registration_number,
      tin: company.value.tin,
      ssnit_employer_code: company.value.ssnit_employer_code,
      email: company.value.email,
      phone: company.value.phone,
      website: company.value.website,
      address: company.value.address,
      city: company.value.city,
      region: company.value.region,
      currency: company.value.currency,
      timezone: company.value.timezone,
      payroll_day: company.value.payroll_day,
      payroll_cycle: company.value.payroll_cycle,
      fiscal_year_start: company.value.fiscal_year_start,
    })

    await companyApi.saveSettings(company.value.id, {
      ...payrollSettings.value,
    })

    toast.success(
      'Settings saved',
      'All company settings have been updated successfully.'
    )
  } catch (error) {
    toast.error('Save failed', error?.message || 'Unable to save settings.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  border-radius: var(--radius-sm);
  font-size: 13.5px;
  color: var(--sk-gray-700);
  cursor: pointer;
  transition: var(--transition);
  text-align: left;
  margin-bottom: 2px;
}

.settings-nav-btn:hover {
  background: var(--sk-gray-100);
}

.settings-nav-btn.active {
  background: #eef4ff;
  color: var(--sk-blue-mid);
  font-weight: 600;
}

.settings-nav-btn i {
  font-size: 15px;
  width: 18px;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--sk-gray-100);
  gap: 16px;
}

.toggle-row:last-child {
  border-bottom: none;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--sk-gray-300);
  border-radius: 24px;
  transition: 0.3s;
}

.toggle-slider::before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

input:checked + .toggle-slider {
  background: var(--sk-success);
}

input:checked + .toggle-slider::before {
  transform: translateX(20px);
}
</style>