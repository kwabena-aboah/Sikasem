<template>
  <div>
    <div class="page-header">
      <div class="d-flex align-items-center gap-3">
        <router-link to="/employees" class="sk-btn sk-btn-ghost sk-btn-icon">
          <i class="bi bi-arrow-left"></i>
        </router-link>
        <div>
          <h1 class="page-title" style="font-size:20px">
            {{ isEditing ? 'Edit Employee' : 'Add New Employee' }}
          </h1>
          <div class="page-subtitle">
            {{ isEditing ? 'Update employee information' : 'Create a new employee record' }}
          </div>
        </div>
      </div>
      <div class="d-flex gap-2">
        <router-link to="/employees" class="sk-btn sk-btn-ghost">Cancel</router-link>
        <button class="sk-btn sk-btn-primary" @click="submitForm" :disabled="saving">
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>
          <i v-else class="bi bi-floppy-fill"></i>
          {{ isEditing ? 'Save Changes' : 'Create Employee' }}
        </button>
      </div>
    </div>

    <!-- Loading state while fetching reference data -->
    <div v-if="refLoading" class="text-center p-5">
      <div class="spinner-border text-primary mb-3"></div>
      <div style="font-size:13px;color:var(--sk-gray-500)">Loading company data...</div>
    </div>

    <!-- Error state -->
    <div v-else-if="refError" class="mb-4 p-4"
      style="background:#FEE2E2;border:1px solid #FECACA;border-radius:12px;color:var(--sk-danger)">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ refError }}
    </div>

    <template v-else>
      <!-- Step indicator -->
      <div class="step-bar mb-4">
        <div
          v-for="(step, i) in steps" :key="step.id"
          class="step-item"
          :class="{ active: activeStep === i, done: i < activeStep }"
        >
          <div class="step-dot">
            <i v-if="i < activeStep" class="bi bi-check-lg"></i>
            <span v-else>{{ i + 1 }}</span>
          </div>
          <div class="step-label">{{ step.label }}</div>
        </div>
      </div>

      <!-- Validation errors banner -->
      <div v-if="formErrors.length" class="mb-4 p-3"
        style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px">
        <div style="font-weight:600;color:var(--sk-danger);margin-bottom:6px">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>Please fix these errors:
        </div>
        <ul style="margin:0;padding-left:20px;font-size:13px;color:var(--sk-danger)">
          <li v-for="e in formErrors" :key="e">{{ e }}</li>
        </ul>
      </div>

      <!-- ── STEP 1: Personal Information ── -->
      <div v-show="activeStep === 0">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-person-fill" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Personal Information</h5>
          </div>
          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">First Name <span class="text-danger">*</span></label>
                  <input type="text" class="sk-input" v-model.trim="form.first_name" required />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Middle Name</label>
                  <input type="text" class="sk-input" v-model.trim="form.middle_name" />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Last Name <span class="text-danger">*</span></label>
                  <input type="text" class="sk-input" v-model.trim="form.last_name" required />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Gender <span class="text-danger">*</span></label>
                  <select class="sk-select" v-model="form.gender" required>
                    <option value="">Select...</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Date of Birth <span class="text-danger">*</span></label>
                  <input type="date" class="sk-input" v-model="form.date_of_birth" required />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Marital Status</label>
                  <select class="sk-select" v-model="form.marital_status">
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                  </select>
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Ghana Card Number</label>
                  <input type="text" class="sk-input" v-model.trim="form.national_id"
                    placeholder="GHA-XXXXXXXXX-X" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">SSNIT Number</label>
                  <input type="text" class="sk-input" v-model.trim="form.ssnit_number" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">TIN</label>
                  <input type="text" class="sk-input" v-model.trim="form.tin" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Personal Email</label>
                  <input type="email" class="sk-input" v-model.trim="form.personal_email" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Work Email</label>
                  <input type="email" class="sk-input" v-model.trim="form.work_email" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Personal Phone</label>
                  <input type="tel" class="sk-input" v-model.trim="form.personal_phone"
                    placeholder="+233..." />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">City / Town</label>
                  <input type="text" class="sk-input" v-model.trim="form.city" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Region</label>
                  <select class="sk-select" v-model="form.region">
                    <option value="">Select region...</option>
                    <option v-for="r in ghanaRegions" :key="r" :value="r">{{ r }}</option>
                  </select>
                </div>
              </div>
              <div class="col-12">
                <div class="sk-form-group">
                  <label class="sk-label">Residential Address</label>
                  <textarea class="sk-textarea" v-model="form.address" style="min-height:60px"></textarea>
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Emergency Contact Name</label>
                  <input type="text" class="sk-input" v-model.trim="form.emergency_contact_name" />
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Emergency Contact Phone</label>
                  <input type="tel" class="sk-input" v-model.trim="form.emergency_contact_phone" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── STEP 2: Employment Details ── -->
      <div v-show="activeStep === 1">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-briefcase-fill" style="color:var(--sk-success)"></i>
            <h5 class="sk-card-title">Employment Details</h5>
          </div>
          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Employee ID <span class="text-danger">*</span></label>
                  <input type="text" class="sk-input" v-model.trim="form.employee_id"
                    required :disabled="isEditing"
                    placeholder="e.g. EMP001" />
                  <div v-if="isEditing" style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                    Employee ID cannot be changed after creation
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Job Title <span class="text-danger">*</span></label>
                  <input type="text" class="sk-input" v-model.trim="form.job_title" required />
                </div>
              </div>

              <!-- Department — populated from company's departments -->
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Department</label>
                  <select class="sk-select" v-model="form.department">
                    <option value="">— No Department —</option>
                    <option v-for="d in departments" :key="d.id" :value="d.id">
                      {{ d.name }}
                    </option>
                  </select>
                  <div v-if="departments.length === 0" style="font-size:11.5px;color:var(--sk-warning);margin-top:3px">
                    <i class="bi bi-exclamation-triangle me-1"></i>
                    No departments found. Add departments in Settings first.
                  </div>
                </div>
              </div>

              <!-- Branch — populated from company's branches -->
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Branch / Office</label>
                  <select class="sk-select" v-model="form.branch">
                    <option value="">— No Branch —</option>
                    <option v-for="b in branches" :key="b.id" :value="b.id">
                      {{ b.name }}
                      <template v-if="b.city"> — {{ b.city }}</template>
                    </option>
                  </select>
                  <div v-if="branches.length === 0" style="font-size:11.5px;color:var(--sk-warning);margin-top:3px">
                    <i class="bi bi-exclamation-triangle me-1"></i>
                    No branches found. Add branches in Settings first.
                  </div>
                </div>
              </div>

              <!-- Job Grade -->
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Job Grade / Band</label>
                  <select class="sk-select" v-model="form.job_grade">
                    <option value="">— No Grade —</option>
                    <option v-for="g in jobGrades" :key="g.id" :value="g.id">
                      {{ g.name }}
                      <template v-if="g.min_salary"> (GHS {{ fmt(g.min_salary) }} – {{ fmt(g.max_salary) }})</template>
                    </option>
                  </select>
                </div>
              </div>

              <!-- Manager -->
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Reports To (Manager)</label>
                  <select class="sk-select" v-model="form.reports_to">
                    <option value="">— No Manager —</option>
                    <option
                      v-for="e in managers"
                      :key="e.id"
                      :value="e.id"
                      :disabled="e.id === form.id"
                    >
                      {{ e.full_name }} ({{ e.employee_id }})
                    </option>
                  </select>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Employment Type <span class="text-danger">*</span></label>
                  <select class="sk-select" v-model="form.employment_type" required>
                    <option value="full_time">Full Time</option>
                    <option value="part_time">Part Time</option>
                    <option value="contract">Contract</option>
                    <option value="intern">Intern</option>
                    <option value="casual">Casual</option>
                  </select>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Status</label>
                  <select class="sk-select" v-model="form.status">
                    <option value="probation">Probation</option>
                    <option value="active">Active</option>
                    <option value="on_leave">On Leave</option>
                    <option value="suspended">Suspended</option>
                    <option value="terminated">Terminated</option>
                  </select>
                </div>
              </div>

              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Hire Date <span class="text-danger">*</span></label>
                  <input type="date" class="sk-input" v-model="form.hire_date" required />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Confirmation Date</label>
                  <input type="date" class="sk-input" v-model="form.confirmation_date" />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Probation End Date</label>
                  <input type="date" class="sk-input" v-model="form.probation_end_date" />
                </div>
              </div>
              <div class="col-md-4">
                <div class="sk-form-group">
                  <label class="sk-label">Contract End Date</label>
                  <input type="date" class="sk-input" v-model="form.contract_end_date" />
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Tax Treatment</label>
                  <select class="sk-select" v-model="form.tax_treatment">
                    <option value="resident">Resident (Standard PAYE)</option>
                    <option value="non_resident">Non-Resident (Flat 25%)</option>
                    <option value="expatriate">Expatriate</option>
                    <option value="casual">Casual Worker (5%)</option>
                  </select>
                </div>
              </div>

              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Work Email</label>
                  <input type="email" class="sk-input" v-model.trim="form.work_email" />
                </div>
              </div>

              <div class="col-12">
                <div class="d-flex gap-4 mt-1 flex-wrap">
                  <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                    <input type="checkbox" v-model="form.is_exempt_ssnit" />
                    <span>Exempt from SSNIT</span>
                  </label>
                  <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                    <input type="checkbox" v-model="form.is_exempt_paye" />
                    <span>Exempt from PAYE</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── STEP 3: Payment / Banking ── -->
      <div v-show="activeStep === 2">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-bank2" style="color:var(--sk-accent)"></i>
            <h5 class="sk-card-title">Payment Information</h5>
          </div>
          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="sk-form-group">
                  <label class="sk-label">Payment Method</label>
                  <select class="sk-select" v-model="form.payment_method">
                    <option value="bank">Bank Transfer</option>
                    <option value="mobile_money">Mobile Money</option>
                    <option value="cash">Cash</option>
                    <option value="cheque">Cheque</option>
                  </select>
                </div>
              </div>

              <template v-if="form.payment_method === 'bank'">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Bank Name</label>
                    <select class="sk-select" v-model="form.bank_name">
                      <option value="">Select bank...</option>
                      <option v-for="b in ghanaBanks" :key="b" :value="b">{{ b }}</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Bank Branch</label>
                    <input type="text" class="sk-input" v-model.trim="form.bank_branch" placeholder="e.g. Accra Main" />
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Account Number <span class="text-danger">*</span></label>
                    <input type="text" class="sk-input" v-model.trim="form.account_number" />
                  </div>
                </div>
                <div class="col-12">
                  <div class="sk-form-group">
                    <label class="sk-label">Account Name (as on bank records)</label>
                    <input type="text" class="sk-input" v-model.trim="form.account_name" />
                  </div>
                </div>
              </template>

              <template v-if="form.payment_method === 'mobile_money'">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Mobile Money Provider</label>
                    <select class="sk-select" v-model="form.mobile_money_provider">
                      <option value="mtn">MTN Mobile Money</option>
                      <option value="vodafone">Telecel Cash</option>
                      <option value="airteltigo">AirtelTigo Money</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Mobile Money Number <span class="text-danger">*</span></label>
                    <input type="tel" class="sk-input" v-model.trim="form.mobile_money_number"
                      placeholder="024XXXXXXX" />
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Navigation ── -->
      <div class="d-flex justify-content-between mt-4">
        <button type="button" class="sk-btn sk-btn-ghost" @click="activeStep--" v-if="activeStep > 0">
          <i class="bi bi-arrow-left"></i> Back
        </button>
        <div v-else></div>

        <button
          v-if="activeStep < steps.length - 1"
          type="button"
          class="sk-btn sk-btn-primary"
          @click="nextStep"
        >
          Next <i class="bi bi-arrow-right"></i>
        </button>
        <button
          v-else
          type="button"
          class="sk-btn sk-btn-primary"
          @click="submitForm"
          :disabled="saving"
        >
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>
          <i v-else class="bi bi-floppy-fill"></i>
          {{ isEditing ? 'Save Changes' : 'Create Employee' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { employeeApi, companyApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route  = useRoute()
const toast  = useToastStore()

const isEditing = computed(() => route.name === 'employee-edit' && !!route.params.id)

// ── Reference data ─────────────────────────────────────────────────────────────
const departments = ref([])
const branches    = ref([])
const jobGrades   = ref([])
const managers    = ref([])
const refLoading  = ref(true)
const refError    = ref('')

// ── Form state ─────────────────────────────────────────────────────────────────
const saving      = ref(false)
const activeStep  = ref(0)
const formErrors  = ref([])

const defaultForm = () => ({
  // Personal
  first_name: '', middle_name: '', last_name: '',
  gender: '', date_of_birth: '', marital_status: 'single',
  national_id: '', ssnit_number: '', tin: '',
  personal_email: '', work_email: '',
  personal_phone: '', address: '', city: '', region: '',
  emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: '',
  // Employment
  employee_id: '', job_title: '',
  department: '', branch: '', job_grade: '', reports_to: '',
  employment_type: 'full_time', status: 'probation',
  hire_date: '', confirmation_date: '', probation_end_date: '', contract_end_date: '',
  tax_treatment: 'resident',
  is_exempt_ssnit: false, is_exempt_paye: false,
  // Payment
  payment_method: 'bank',
  bank_name: '', bank_branch: '', bank_code: '', account_number: '', account_name: '',
  mobile_money_number: '', mobile_money_provider: 'mtn',
})

const form = ref(defaultForm())

// ── Steps ──────────────────────────────────────────────────────────────────────
const steps = [
  { id: 'personal',   label: 'Personal Info'  },
  { id: 'employment', label: 'Employment'      },
  { id: 'banking',    label: 'Payment'         },
]

// ── Static reference lists ─────────────────────────────────────────────────────
const ghanaRegions = [
  'Ahafo', 'Ashanti', 'Bono', 'Bono East', 'Central', 'Eastern',
  'Greater Accra', 'North East', 'Northern', 'Oti', 'Savannah',
  'Upper East', 'Upper West', 'Volta', 'Western', 'Western North',
]

const ghanaBanks = [
  'Absa Bank Ghana', 'Access Bank Ghana', 'Agricultural Development Bank (ADB)',
  'Cal Bank', 'Consolidated Bank Ghana', 'Ecobank Ghana', 'FBN Bank Ghana',
  'Fidelity Bank Ghana', 'First Atlantic Bank', 'First National Bank',
  'GCB Bank', 'Ghana Commercial Bank', 'GT Bank Ghana', 'National Investment Bank (NIB)',
  'OmniBSIC Bank', 'Prudential Bank', 'Republic Bank', 'Société Générale Ghana',
  'Stanbic Bank Ghana', 'Standard Chartered Bank Ghana', 'UBA Ghana',
  'Universal Merchant Bank', 'Zenith Bank Ghana',
]

// ── Validation ─────────────────────────────────────────────────────────────────
function validateStep(step) {
  const errors = []
  if (step === 0) {
    if (!form.value.first_name) errors.push('First name is required')
    if (!form.value.last_name)  errors.push('Last name is required')
    if (!form.value.gender)     errors.push('Gender is required')
    if (!form.value.date_of_birth) errors.push('Date of birth is required')
  }
  if (step === 1) {
    if (!form.value.employee_id)    errors.push('Employee ID is required')
    if (!form.value.job_title)      errors.push('Job title is required')
    if (!form.value.employment_type) errors.push('Employment type is required')
    if (!form.value.hire_date)      errors.push('Hire date is required')
  }
  if (step === 2) {
    if (form.value.payment_method === 'bank' && !form.value.account_number) {
      errors.push('Bank account number is required')
    }
    if (form.value.payment_method === 'mobile_money' && !form.value.mobile_money_number) {
      errors.push('Mobile money number is required')
    }
  }
  return errors
}

function nextStep() {
  const errors = validateStep(activeStep.value)
  if (errors.length) {
    formErrors.value = errors
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  formErrors.value = []
  activeStep.value++
}

// ── Build payload — strip empty strings to null/undefined ──────────────────────
function buildPayload() {
  const data = { ...form.value }

  // Convert empty strings to null for FK fields
  const fkFields = ['department', 'branch', 'job_grade', 'reports_to']
  fkFields.forEach(f => {
    if (!data[f]) data[f] = null
  })

  // Remove read-only / derived fields
  delete data.id
  delete data.company
  delete data.company_name
  delete data.department_name
  delete data.branch_name
  delete data.job_grade_name
  delete data.manager_name
  delete data.full_name
  delete data.years_of_service
  delete data.age
  delete data.created_at
  delete data.updated_at
  delete data.created_by

  return data
}

async function submitForm() {
  const errors = validateStep(activeStep.value)
  if (errors.length) {
    formErrors.value = errors
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  formErrors.value = []
  saving.value = true

  try {
    const payload = buildPayload()
    if (isEditing.value) {
      await employeeApi.update(route.params.id, payload)
      toast.success('Employee updated', `${form.value.first_name}'s record has been saved`)
      router.push(`/employees/${route.params.id}`)
    } else {
      const emp = await employeeApi.create(payload)
      toast.success('Employee created', `${form.value.first_name} ${form.value.last_name} has been added`)
      router.push(`/employees/${emp.id}`)
    }
  } catch (e) {
    toast.error('Save failed', e.message)
    formErrors.value = [e.message]
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } finally {
    saving.value = false
  }
}

// ── Load reference data and existing employee ──────────────────────────────────
onMounted(async () => {
  refLoading.value = true
  refError.value   = ''

  try {
    // Load all reference data in parallel
    const [deptData, branchData, gradeData, empListData] = await Promise.all([
      companyApi.departments(),
      companyApi.branches(),
      companyApi.jobGrades(),
      employeeApi.list({ page_size: 200 }),
    ])

    departments.value = deptData.results  || deptData  || []
    branches.value    = branchData.results || branchData || []
    jobGrades.value   = gradeData.results  || gradeData  || []

    // Managers list: all active employees (for 'reports_to' dropdown)
    const empList     = empListData.results || empListData || []
    managers.value    = empList.map(e => ({
      id: e.id,
      full_name: e.full_name || `${e.first_name} ${e.last_name}`,
      employee_id: e.employee_id,
    }))

    // If editing, load the existing employee record
    if (isEditing.value) {
      const emp = await employeeApi.get(route.params.id)
      // Merge into form — convert FK objects to IDs
      Object.keys(defaultForm()).forEach(key => {
        if (emp[key] !== undefined && emp[key] !== null) {
          form.value[key] = emp[key]
        }
      })
      // Ensure FK fields are IDs (not objects)
      if (emp.department && typeof emp.department === 'object') {
        form.value.department = emp.department.id
      }
      if (emp.branch && typeof emp.branch === 'object') {
        form.value.branch = emp.branch.id
      }
      if (emp.job_grade && typeof emp.job_grade === 'object') {
        form.value.job_grade = emp.job_grade.id
      }
      if (emp.reports_to && typeof emp.reports_to === 'object') {
        form.value.reports_to = emp.reports_to.id
      }
      form.value.id = emp.id
    }

  } catch (e) {
    refError.value = `Failed to load company data: ${e.message}. Make sure your account is linked to a company.`
    console.error('EmployeeFormView mount error:', e)
  } finally {
    refLoading.value = false
  }
})

function fmt(v) {
  return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 0 })
}
</script>

<style scoped>
.step-bar {
  display: flex;
  align-items: center;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.step-item:not(:last-child)::after {
  content: '';
  flex: 1;
  height: 2px;
  background: var(--sk-gray-200);
  margin: 0 8px;
}

.step-item.done::after {
  background: var(--sk-success);
}

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--sk-gray-300);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background: white;
  color: var(--sk-gray-500);
  flex-shrink: 0;
  transition: var(--transition);
}

.step-item.active .step-dot {
  border-color: var(--sk-blue-mid);
  background: var(--sk-blue-mid);
  color: white;
}

.step-item.done .step-dot {
  border-color: var(--sk-success);
  background: var(--sk-success);
  color: white;
}

.step-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--sk-gray-500);
  white-space: nowrap;
}

.step-item.active .step-label { color: var(--sk-blue-mid); font-weight: 600; }
.step-item.done  .step-label  { color: var(--sk-success); }
</style>
