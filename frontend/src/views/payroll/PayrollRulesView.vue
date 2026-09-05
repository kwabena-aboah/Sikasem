<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Payroll Rules Engine</h1>
        <div class="page-subtitle">Configure conditional payroll logic — bonuses, deductions, and custom treatments</div>
      </div>
      <button class="sk-btn sk-btn-primary" @click="openNewRule">
        <i class="bi bi-plus-lg"></i> New Rule
      </button>
    </div>

    <!-- Explainer banner -->
    <div class="mb-4 p-4" style="background:linear-gradient(135deg,var(--sk-dark),var(--sk-blue));border-radius:14px;color:white">
      <div class="d-flex align-items-start gap-3">
        <i class="bi bi-gear-wide-connected" style="font-size:26px;color:var(--sk-accent);flex-shrink:0;margin-top:2px"></i>
        <div>
          <div style="font-weight:700;font-size:15px;margin-bottom:6px">Custom Rules Engine</div>
          <div style="font-size:13px;opacity:.8;line-height:1.65">
            Rules automatically modify pay components based on employee attributes — applied in priority order after standard payroll calculation.
            Example: <em>Add GHS 500 bonus if department = Engineering</em>, or <em>Multiply transport by 1.5 for Managers</em>.
          </div>
        </div>
      </div>
    </div>

    <!-- Rules table -->
    <div class="sk-card">
      <div v-if="loading" class="text-center p-5">
        <div class="spinner-border text-primary"></div>
      </div>
      <div v-else-if="!rules.length" class="empty-state" style="padding:60px">
        <i class="bi bi-gear-wide-connected"></i>
        <h5>No rules configured</h5>
        <p>Create a custom rule to automate conditional pay logic for your employees</p>
        <button class="sk-btn sk-btn-primary sk-btn-sm mt-3" @click="openNewRule">Create First Rule</button>
      </div>
      <div v-else class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th>Rule Name</th>
              <th>Trigger</th>
              <th>Component</th>
              <th>Action</th>
              <th>Priority</th>
              <th>Valid Period</th>
              <th>Active</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in rules" :key="rule.id">
              <td>
                <div style="font-weight:600">{{ rule.name }}</div>
                <div v-if="rule.description" style="font-size:11.5px;color:var(--sk-gray-400)">{{ rule.description }}</div>
              </td>
              <td>
                <span class="sk-badge badge-processing" style="font-size:10.5px">
                  {{ triggerLabel(rule.trigger_type) }}
                </span>
              </td>
              <td style="font-size:13px;font-weight:500">{{ rule.component_name }}</td>
              <td>
                <code style="font-family:var(--font-mono);font-size:11.5px;background:var(--sk-gray-100);padding:3px 7px;border-radius:4px">
                  {{ actionLabel(rule) }}
                </code>
              </td>
              <td>
                <span class="sk-badge badge-inactive">{{ rule.priority }}</span>
              </td>
              <td style="font-size:12px;color:var(--sk-gray-500)">
                {{ rule.valid_from ? formatDate(rule.valid_from) : '—' }}
                {{ rule.valid_to ? ' → ' + formatDate(rule.valid_to) : rule.valid_from ? ' → ongoing' : 'Always' }}
              </td>
              <td>
                <label class="toggle-switch">
                  <input type="checkbox" :checked="rule.is_active" @change="toggleRule(rule)" />
                  <span class="toggle-slider"></span>
                </label>
              </td>
              <td>
                <div class="d-flex justify-content-end gap-1">
                  <button class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon" @click="editRule(rule)">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon"
                    style="color:var(--sk-danger)" @click="deleteRule(rule)">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Rule Modal ── -->
    <div v-if="showModal" class="sk-modal-backdrop" @click.self="closeModal">
      <div class="sk-modal sk-modal-lg">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">{{ editing ? 'Edit Rule' : 'Create Payroll Rule' }}</h5>
          <button class="sk-modal-close" @click="closeModal"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="row g-3">
            <!-- Name -->
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Rule Name <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="form.name"
                  placeholder="e.g. Engineering Department Performance Bonus" />
              </div>
            </div>
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Description <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span></label>
                <textarea class="sk-textarea" v-model="form.description"
                  style="min-height:60px"
                  placeholder="Describe when and why this rule applies…"></textarea>
              </div>
            </div>

            <!-- Trigger -->
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Trigger Condition <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="form.trigger_type">
                  <option value="always">Always Apply (all employees)</option>
                  <option value="dept">If Department</option>
                  <option value="grade">If Job Grade</option>
                  <option value="emp_type">If Employment Type</option>
                  <option value="tax">If Tax Treatment</option>
                  <option value="tenure">If Years of Service</option>
                  <option value="salary">If Salary Range</option>
                </select>
              </div>
            </div>

            <!-- Target component -->
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Target Component <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="form.component">
                  <option value="">Select component…</option>
                  <option v-for="c in components" :key="c.id" :value="c.id">
                    {{ c.name }} ({{ c.code }})
                  </option>
                </select>
              </div>
            </div>

            <!-- Trigger-specific parameters -->
            <div v-if="form.trigger_type === 'dept'" class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Select Departments</label>
                <div class="dept-checkbox-grid">
                  <label v-for="d in departments" :key="d.id"
                    class="dept-checkbox-item"
                    :class="{ active: isDeptSelected(d.id) }">
                    <input type="checkbox"
                      :value="d.id"
                      :checked="isDeptSelected(d.id)"
                      @change="toggleDept(d.id)" />
                    {{ d.name }}
                  </label>
                </div>
              </div>
            </div>

            <div v-if="form.trigger_type === 'grade'" class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Select Job Grades</label>
                <div class="dept-checkbox-grid">
                  <label v-for="g in jobGrades" :key="g.id"
                    class="dept-checkbox-item"
                    :class="{ active: isGradeSelected(g.id) }">
                    <input type="checkbox"
                      :value="g.id"
                      :checked="isGradeSelected(g.id)"
                      @change="toggleGrade(g.id)" />
                    {{ g.name }}
                  </label>
                </div>
              </div>
            </div>

            <div v-if="form.trigger_type === 'emp_type'" class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Employment Types</label>
                <div class="dept-checkbox-grid">
                  <label v-for="t in empTypes" :key="t.value"
                    class="dept-checkbox-item"
                    :class="{ active: isEmpTypeSelected(t.value) }">
                    <input type="checkbox"
                      :value="t.value"
                      :checked="isEmpTypeSelected(t.value)"
                      @change="toggleEmpType(t.value)" />
                    {{ t.label }}
                  </label>
                </div>
              </div>
            </div>

            <div v-if="form.trigger_type === 'tenure'" class="col-12">
              <div class="row g-3">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Min Years of Service</label>
                    <input type="number" class="sk-input"
                      v-model.number="form.trigger_condition.min_years" min="0" step="0.5" />
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Max Years of Service</label>
                    <input type="number" class="sk-input"
                      v-model.number="form.trigger_condition.max_years" min="0" step="0.5" />
                  </div>
                </div>
              </div>
            </div>

            <div v-if="form.trigger_type === 'salary'" class="col-12">
              <div class="row g-3">
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Min Basic Salary (GHS)</label>
                    <input type="number" class="sk-input"
                      v-model.number="form.trigger_condition.min_salary" min="0" />
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="sk-form-group">
                    <label class="sk-label">Max Basic Salary (GHS)</label>
                    <input type="number" class="sk-input"
                      v-model.number="form.trigger_condition.max_salary" min="0" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Action -->
            <div class="col-md-4">
              <div class="sk-form-group">
                <label class="sk-label">Action Type <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="form.action_type">
                  <option value="add">Add Fixed Amount</option>
                  <option value="set">Set to Fixed Amount</option>
                  <option value="multiply">Multiply by Factor</option>
                  <option value="formula">Custom Formula</option>
                </select>
              </div>
            </div>

            <div class="col-md-4">
              <div class="sk-form-group">
                <label class="sk-label">
                  {{ form.action_type === 'multiply' ? 'Multiplier' : 'Value (GHS)' }}
                  <span class="text-danger">*</span>
                </label>
                <input type="number" class="sk-input"
                  v-model.number="form.action_value" step="0.01"
                  :placeholder="form.action_type === 'multiply' ? 'e.g. 1.1 = +10%' : 'e.g. 500'" />
                <div v-if="form.action_type === 'multiply'"
                  style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                  e.g. 1.5 = multiply by 1.5 (50% increase)
                </div>
              </div>
            </div>

            <div class="col-md-4">
              <div class="sk-form-group">
                <label class="sk-label">Priority</label>
                <input type="number" class="sk-input"
                  v-model.number="form.priority" min="0" max="100" />
                <div style="font-size:11px;color:var(--sk-gray-400);margin-top:3px">
                  Higher priority runs later (can override earlier rules)
                </div>
              </div>
            </div>

            <div v-if="form.action_type === 'formula'" class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Formula Expression</label>
                <input type="text" class="sk-input"
                  v-model="form.action_formula"
                  placeholder="e.g. basic * 0.1 + years * 50"
                  style="font-family:var(--font-mono)" />
                <div style="font-size:11.5px;color:var(--sk-gray-500);margin-top:4px">
                  Available variables: <code>basic</code> (basic salary), <code>gross</code> (total gross),
                  <code>value</code> (current component value), <code>years</code> (years of service)
                </div>
              </div>
            </div>

            <!-- Valid dates -->
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Valid From <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span></label>
                <input type="date" class="sk-input" v-model="form.valid_from" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Valid To <span style="font-weight:400;color:var(--sk-gray-400)">(optional)</span></label>
                <input type="date" class="sk-input" v-model="form.valid_to" />
              </div>
            </div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="closeModal">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="saveRule" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm"></span>
            {{ editing ? 'Save Changes' : 'Create Rule' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { payrollApi, companyApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const rules       = ref([])
const components  = ref([])
const departments = ref([])
const jobGrades   = ref([])
const loading     = ref(true)
const showModal   = ref(false)
const saving      = ref(false)
const editing     = ref(null)  // null = new, string = existing rule id

const empTypes = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'contract',  label: 'Contract' },
  { value: 'intern',    label: 'Intern' },
  { value: 'casual',    label: 'Casual' },
]

// ── Form helpers ───────────────────────────────────────────────────────────────
const defaultForm = () => ({
  name:              '',
  description:       '',
  trigger_type:      'always',
  trigger_condition: {},
  component:         '',
  action_type:       'add',
  action_value:      0,
  action_formula:    '',
  priority:          0,
  valid_from:        '',
  valid_to:          '',
  is_active:         true,
})

const form = ref(defaultForm())

// Trigger condition helpers
function isDeptSelected(id)       { return (form.value.trigger_condition.department_ids || []).includes(id) }
function isGradeSelected(id)      { return (form.value.trigger_condition.grade_ids || []).includes(id) }
function isEmpTypeSelected(val)   { return (form.value.trigger_condition.types || []).includes(val) }

function toggleDept(id) {
  const ids = form.value.trigger_condition.department_ids || []
  form.value.trigger_condition.department_ids = ids.includes(id)
    ? ids.filter(x => x !== id)
    : [...ids, id]
}
function toggleGrade(id) {
  const ids = form.value.trigger_condition.grade_ids || []
  form.value.trigger_condition.grade_ids = ids.includes(id)
    ? ids.filter(x => x !== id)
    : [...ids, id]
}
function toggleEmpType(val) {
  const vals = form.value.trigger_condition.types || []
  form.value.trigger_condition.types = vals.includes(val)
    ? vals.filter(x => x !== val)
    : [...vals, val]
}

// ── Modal actions ──────────────────────────────────────────────────────────────
function openNewRule() {
  editing.value  = null
  form.value     = defaultForm()
  showModal.value = true
}

function editRule(rule) {
  editing.value = rule.id
  form.value = {
    name:              rule.name,
    description:       rule.description || '',
    trigger_type:      rule.trigger_type,
    trigger_condition: { ...rule.trigger_condition },
    // component is returned as a UUID string from DRF (PK field)
    component:         rule.component,
    action_type:       rule.action_type,
    action_value:      parseFloat(rule.action_value || 0),
    action_formula:    rule.action_formula || '',
    priority:          rule.priority || 0,
    valid_from:        rule.valid_from  || '',
    valid_to:          rule.valid_to    || '',
    is_active:         rule.is_active,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value   = null
  form.value      = defaultForm()
}

async function saveRule() {
  if (!form.value.name.trim()) {
    toast.warning('Validation', 'Rule name is required.')
    return
  }
  if (!form.value.component) {
    toast.warning('Validation', 'Please select a target component.')
    return
  }

  saving.value = true
  try {
    // company and created_by are read_only on serializer — set server-side
    const payload = {
      name:              form.value.name,
      description:       form.value.description,
      trigger_type:      form.value.trigger_type,
      trigger_condition: form.value.trigger_condition,
      component:         form.value.component,
      action_type:       form.value.action_type,
      action_value:      form.value.action_value,
      action_formula:    form.value.action_formula,
      priority:          form.value.priority,
      valid_from:        form.value.valid_from  || null,
      valid_to:          form.value.valid_to    || null,
      is_active:         form.value.is_active,
    }

    if (editing.value) {
      await payrollApi.updateRule(editing.value, payload)
      toast.success('Rule updated')
    } else {
      await payrollApi.createRule(payload)
      toast.success('Rule created')
    }
    closeModal()
    await loadRules()
  } catch (e) {
    toast.error('Save failed', e.message)
  } finally {
    saving.value = false
  }
}

async function deleteRule(rule) {
  if (!confirm(`Delete rule "${rule.name}"? This cannot be undone.`)) return
  try {
    await payrollApi.deleteRule(rule.id)
    toast.success('Rule deleted')
    await loadRules()
  } catch (e) {
    toast.error('Delete failed', e.message)
  }
}

async function toggleRule(rule) {
  try {
    await payrollApi.updateRule(rule.id, { is_active: !rule.is_active })
    rule.is_active = !rule.is_active
    toast.info(rule.is_active ? 'Rule activated' : 'Rule deactivated')
  } catch (e) {
    toast.error('Update failed', e.message)
  }
}

// ── Display helpers ────────────────────────────────────────────────────────────
function triggerLabel(t) {
  return {
    always:   'Always',
    dept:     'Department',
    grade:    'Job Grade',
    emp_type: 'Emp Type',
    tax:      'Tax Treatment',
    tenure:   'Tenure',
    salary:   'Salary Range',
  }[t] || t
}

function actionLabel(rule) {
  const v = parseFloat(rule.action_value || 0)
  return {
    add:      `+ GHS ${v.toFixed(2)}`,
    set:      `= GHS ${v.toFixed(2)}`,
    multiply: `× ${v}`,
    formula:  rule.action_formula || 'formula',
  }[rule.action_type] || rule.action_type
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

// ── Load data ──────────────────────────────────────────────────────────────────
async function loadRules() {
  try {
    const data  = await payrollApi.rules()
    rules.value = data.results || data || []
  } catch (e) {
    toast.error('Failed to load rules', e.message)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [rulesData, compsData, deptsData, gradesData] = await Promise.all([
      payrollApi.rules(),
      payrollApi.components(),
      companyApi.departments(),
      companyApi.jobGrades(),
    ])
    rules.value       = rulesData.results  || rulesData  || []
    components.value  = compsData.results  || compsData  || []
    departments.value = deptsData.results  || deptsData  || []
    jobGrades.value   = gradesData.results || gradesData || []
  } catch (e) {
    toast.error('Failed to load data', e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dept-checkbox-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0;
}

.dept-checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1.5px solid var(--sk-gray-200);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  transition: var(--transition);
  user-select: none;
}

.dept-checkbox-item:hover { border-color: var(--sk-blue-light); background: #f7faff; }
.dept-checkbox-item.active { border-color: var(--sk-blue-mid); background: #EEF4FF; color: var(--sk-blue-mid); font-weight: 500; }

.dept-checkbox-item input[type="checkbox"] { display: none; }

.toggle-switch {
  position: relative; display: inline-block;
  width: 40px; height: 22px;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background: var(--sk-gray-300); border-radius: 22px; transition: .3s;
}
.toggle-slider::before {
  position: absolute; content: '';
  height: 16px; width: 16px;
  left: 3px; bottom: 3px;
  background: white; border-radius: 50%; transition: .3s;
}
input:checked + .toggle-slider { background: var(--sk-success); }
input:checked + .toggle-slider::before { transform: translateX(18px); }
</style>
