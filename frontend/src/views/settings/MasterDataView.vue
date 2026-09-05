<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ config.title }}</h1>
        <div class="page-subtitle">{{ config.subtitle }}</div>
      </div>
      <button class="sk-btn sk-btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Add {{ config.singular }}
      </button>
    </div>

    <div class="sk-card">
      <div class="sk-card-header">
        <div class="sk-input-group" style="width:280px">
          <i class="bi bi-search input-icon"></i>
          <input class="sk-input" v-model="search" :placeholder="`Search ${config.title.toLowerCase()}...`" />
        </div>
        <span class="ms-auto" style="font-size:12px;color:var(--sk-gray-500)">{{ filteredRows.length }} records</span>
      </div>
      <div v-if="loading" class="text-center p-5"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="!filteredRows.length" class="empty-state" style="padding:60px">
        <i class="bi bi-database"></i><h5>No {{ config.title.toLowerCase() }} found</h5>
        <p>Create the first record to make it available across the system.</p>
      </div>
      <div v-else class="sk-table-wrapper">
        <table class="sk-table"><thead><tr>
          <th v-for="field in config.columns" :key="field.key">{{ field.label }}</th>
          <th>Status</th><th style="text-align:right">Actions</th>
        </tr></thead><tbody>
          <tr v-for="row in filteredRows" :key="row.id">
            <td v-for="field in config.columns" :key="field.key">{{ displayValue(row, field) }}</td>
            <td><span class="sk-badge" :class="row.is_active === false ? 'badge-inactive' : 'badge-active'">
              {{ row.is_active === false ? 'Inactive' : 'Active' }}
            </span></td>
            <td><div class="d-flex justify-content-end gap-1">
              <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="openEdit(row)"><i class="bi bi-pencil"></i></button>
              <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="remove(row)" title="Delete"><i class="bi bi-trash text-danger"></i></button>
            </div></td>
          </tr>
        </tbody></table>
      </div>
    </div>

    <div v-if="showModal" class="sk-modal-backdrop" @click.self="closeModal">
      <div class="sk-modal sk-modal-lg">
        <div class="sk-modal-header"><h5 class="sk-modal-title">{{ editing ? 'Edit' : 'Add' }} {{ config.singular }}</h5>
          <button class="sk-modal-close" @click="closeModal"><i class="bi bi-x"></i></button></div>
        <div class="sk-modal-body"><div class="row g-3">
          <div v-for="field in config.fields" :key="field.key" :class="field.full ? 'col-12' : 'col-md-6'">
            <div class="sk-form-group">
              <label class="sk-label">{{ field.label }}</label>
              <select v-if="field.type === 'select'" class="sk-select" v-model="form[field.key]">
                <option value="">Select {{ field.label.toLowerCase() }}...</option>
                <option v-for="option in optionsFor(field)" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <textarea v-else-if="field.type === 'textarea'" class="sk-textarea" v-model="form[field.key]"></textarea>
              <label v-else-if="field.type === 'checkbox'" class="d-flex align-items-center gap-2" style="margin-top:8px">
                <input type="checkbox" v-model="form[field.key]" /> {{ field.label }}
              </label>
              <input v-else class="sk-input" :type="field.type || 'text'" v-model="form[field.key]" :step="field.type === 'number' ? '0.01' : undefined" />
            </div>
          </div>
        </div></div>
        <div class="sk-modal-footer"><button class="sk-btn sk-btn-ghost" @click="closeModal">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="save" :disabled="saving"><span v-if="saving" class="spinner-border spinner-border-sm"></span> Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, companyApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const toast = useToastStore()
const rows = ref([]); const search = ref(''); const loading = ref(true)
const saving = ref(false); const showModal = ref(false); const editing = ref(null)
const form = ref({}); const branches = ref([]); const departments = ref([])

const configs = {
  branches: { title: 'Branches', singular: 'Branch', subtitle: 'Manage company locations and branch codes.', endpoint: '/companies/branches/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'city', label: 'City' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'address', label: 'Address', full: true, type: 'textarea' }, { key: 'city', label: 'City' }, { key: 'region', label: 'Region' }, { key: 'phone', label: 'Phone' }, { key: 'email', label: 'Email', type: 'email' }, { key: 'is_headquarters', label: 'Headquarters', type: 'checkbox' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  departments: { title: 'Departments', singular: 'Department', subtitle: 'Organise employees into departments and cost centres.', endpoint: '/companies/departments/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'branch_name', label: 'Branch' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'branch', label: 'Branch', type: 'select', source: 'branches' }, { key: 'cost_center', label: 'Cost Centre' }, { key: 'description', label: 'Description', full: true, type: 'textarea' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  'job-grades': { title: 'Job Grades', singular: 'Job Grade', subtitle: 'Manage job levels and salary bands.', endpoint: '/companies/job-grades/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'min_salary', label: 'Minimum Salary' }, { key: 'max_salary', label: 'Maximum Salary' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'min_salary', label: 'Minimum Salary', type: 'number' }, { key: 'max_salary', label: 'Maximum Salary', type: 'number' }, { key: 'description', label: 'Description', full: true, type: 'textarea' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  'salary-components': { title: 'Salary Components', singular: 'Salary Component', subtitle: 'Configure earnings, deductions, and employer contributions.', endpoint: '/payroll/components/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'component_type', label: 'Type' }, { key: 'calculation_method', label: 'Calculation' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'component_type', label: 'Type', type: 'select', options: [{ value: 'earning', label: 'Earning' }, { value: 'deduction', label: 'Deduction' }, { value: 'employer_contribution', label: 'Employer Contribution' }] }, { key: 'calculation_method', label: 'Calculation Method', type: 'select', options: [{ value: 'fixed', label: 'Fixed Amount' }, { value: 'pct_basic', label: 'Percentage of Basic' }, { value: 'pct_gross', label: 'Percentage of Gross' }, { value: 'formula', label: 'Custom Formula' }] }, { key: 'default_value', label: 'Default Value', type: 'number' }, { key: 'is_taxable', label: 'Taxable', type: 'checkbox' }, { key: 'is_pensionable', label: 'Pensionable', type: 'checkbox' }, { key: 'is_statutory', label: 'Statutory', type: 'checkbox' }, { key: 'display_on_payslip', label: 'Show on Payslip', type: 'checkbox' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  'leave-types': { title: 'Leave Types', singular: 'Leave Type', subtitle: 'Define leave policies available to employees.', endpoint: '/leaves/types/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'days_per_year', label: 'Days / Year' }, { key: 'is_paid', label: 'Paid' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'days_per_year', label: 'Days per Year', type: 'number' }, { key: 'accrual_type', label: 'Accrual', type: 'select', options: [{ value: 'monthly', label: 'Monthly' }, { value: 'annual', label: 'Annual' }, { value: 'manual', label: 'Manual' }] }, { key: 'is_paid', label: 'Paid', type: 'checkbox' }, { key: 'carry_forward', label: 'Carry Forward', type: 'checkbox' }, { key: 'max_days_per_request', label: 'Max Days per Request', type: 'number' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  'loan-types': { title: 'Loan Types', singular: 'Loan Type', subtitle: 'Configure employee loan and advance products.', endpoint: '/loans/types/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'max_amount', label: 'Max Amount' }, { key: 'max_months', label: 'Max Months' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'max_amount', label: 'Maximum Amount', type: 'number' }, { key: 'max_months', label: 'Maximum Months', type: 'number' }, { key: 'interest_rate', label: 'Interest Rate', type: 'number' }, { key: 'interest_type', label: 'Interest Type', type: 'select', options: [{ value: 'flat', label: 'Flat Rate' }, { value: 'reducing', label: 'Reducing Balance' }, { value: 'none', label: 'Interest-Free' }] }, { key: 'requires_guarantor', label: 'Requires Guarantor', type: 'checkbox' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  shifts: { title: 'Shifts', singular: 'Shift', subtitle: 'Set working hours and overtime rules.', endpoint: '/attendance/shifts/', columns: [{ key: 'name', label: 'Name' }, { key: 'start_time', label: 'Start' }, { key: 'end_time', label: 'End' }, { key: 'grace_period_minutes', label: 'Grace (min)' }], fields: [{ key: 'name', label: 'Name' }, { key: 'start_time', label: 'Start Time', type: 'time' }, { key: 'end_time', label: 'End Time', type: 'time' }, { key: 'break_minutes', label: 'Break Minutes', type: 'number' }, { key: 'overtime_threshold_hours', label: 'Overtime Threshold', type: 'number' }, { key: 'grace_period_minutes', label: 'Grace Period (Minutes)', type: 'number' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
  benefits: { title: 'Benefits', singular: 'Benefit', subtitle: 'Manage non-cash employee benefits.', endpoint: '/leaves/benefits/', columns: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'monetary_value', label: 'Value' }, { key: 'is_taxable', label: 'Taxable' }], fields: [{ key: 'name', label: 'Name' }, { key: 'code', label: 'Code' }, { key: 'description', label: 'Description', full: true, type: 'textarea' }, { key: 'monetary_value', label: 'Monetary Value', type: 'number' }, { key: 'is_taxable', label: 'Taxable', type: 'checkbox' }, { key: 'is_active', label: 'Active', type: 'checkbox' }] },
}

configs.holidays = { title: 'Public Holidays', singular: 'Public Holiday', subtitle: 'Manage company and national holidays.', endpoint: '/attendance/holidays/', columns: [{ key: 'name', label: 'Name' }, { key: 'date', label: 'Date' }, { key: 'country', label: 'Country' }, { key: 'is_national', label: 'National' }], fields: [{ key: 'name', label: 'Name' }, { key: 'date', label: 'Date', type: 'date' }, { key: 'country', label: 'Country' }, { key: 'is_national', label: 'National Holiday', type: 'checkbox' }] }

const config = computed(() => configs[route.name] || configs.branches)
const filteredRows = computed(() => rows.value.filter(row => JSON.stringify(row).toLowerCase().includes(search.value.toLowerCase())))

function blankForm() {
  return Object.fromEntries(
    config.value.fields.map(field => [
      field.key,
      field.type === 'checkbox' ? false : field.type === 'select' ? null : '',
    ])
  )
}

function normaliseRow(row) {
  const result = { ...row }
  config.value.fields.forEach(field => {
    if (result[field.key] === undefined) {
      result[field.key] = field.type === 'checkbox' ? false : field.type === 'select' ? null : ''
    }
    // Keep null as null — do not convert to '' — so FK select fields bind correctly
  })
  return result
}

function optionsFor(field) {
  if (field.options) return field.options
  if (field.source === 'branches') return branches.value.map(item => ({ value: item.id, label: item.name }))
  if (field.source === 'departments') return departments.value.map(item => ({ value: item.id, label: item.name }))
  return []
}

function displayValue(row, field) {
  const val = row[field.key]
  if (field.type === 'checkbox' || typeof val === 'boolean') return val ? 'Yes' : 'No'
  if (field.key === 'branch_name') return val || 'All branches'
  if (val === null || val === undefined || val === '') return '—'
  // Resolve select option labels for display
  if (field.type === 'select' && field.options) {
    const opt = field.options.find(o => o.value === val)
    return opt ? opt.label : val
  }
  return val
}

async function load() {
  loading.value = true
  try {
    const data = await api.get(config.value.endpoint)
    rows.value = (data.results || data || []).map(normaliseRow)
    if (config.value.title === 'Departments') departments.value = rows.value
    if (config.value.title === 'Branches') branches.value = rows.value
  } catch (error) {
    toast.error('Could not load records', error.message)
  } finally { loading.value = false }
}

function openCreate() { editing.value = null; form.value = blankForm(); showModal.value = true }
function openEdit(row) { editing.value = row.id; form.value = { ...row }; showModal.value = true }
function closeModal() { showModal.value = false; editing.value = null }

async function save() {
  // Validate required fields (name is always required)
  const requiredFields = config.value.fields.filter(f => f.required !== false && ['name', 'code'].includes(f.key))
  for (const f of requiredFields) {
    if (!form.value[f.key] || String(form.value[f.key]).trim() === '') {
      toast.error('Validation error', `${f.label} is required`)
      return
    }
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    delete payload.id; delete payload.company; delete payload.branch_name; delete payload.head_name; delete payload.employee_count
    // Convert empty strings to null so FK and optional fields don't cause UUID/type errors
    Object.keys(payload).forEach(k => {
      if (payload[k] === '') payload[k] = null
    })
    if (editing.value) await api.patch(`${config.value.endpoint}${editing.value}/`, payload)
    else await api.post(config.value.endpoint, payload)
    toast.success(editing.value ? 'Record updated' : 'Record created')
    closeModal(); await load()
  } catch (error) { toast.error('Save failed', error.message) }
  finally { saving.value = false }
}

async function remove(row) {
  if (!confirm(`Delete "${row.name}"? This cannot be undone.`)) return
  try {
    await api.delete(`${config.value.endpoint}${row.id}/`)
    toast.success('Record deleted'); await load()
  } catch (error) { toast.error('Delete failed', error.message) }
}

watch(() => route.name, () => { search.value = ''; load() })
onMounted(async () => {
  try {
    const [branchData, departmentData] = await Promise.all([companyApi.branches(), companyApi.departments()])
    branches.value = branchData.results || branchData || []
    departments.value = departmentData.results || departmentData || []
  } catch { /* reference data is optional */ }
  await load()
})
</script>
