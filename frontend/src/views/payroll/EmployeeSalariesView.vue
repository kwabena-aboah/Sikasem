<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Employee Salaries</h1><div class="page-subtitle">Assign a current salary and structure before processing payroll.</div></div>
      <button class="sk-btn sk-btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Assign Salary</button>
    </div>

    <div class="sk-card">
      <div class="sk-card-header">
        <div class="sk-input-group" style="width:280px"><i class="bi bi-search input-icon"></i><input class="sk-input" v-model="search" placeholder="Search employees..." /></div>
        <span class="ms-auto" style="font-size:12px;color:var(--sk-gray-500)">{{ filteredAssignments.length }} assignments</span>
      </div>
      <div v-if="loading" class="text-center p-5"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="!filteredAssignments.length" class="empty-state" style="padding:60px"><i class="bi bi-person-vcard"></i><h5>No salary assignments</h5><p>Assign a salary to each active employee before running payroll.</p></div>
      <div v-else class="sk-table-wrapper"><table class="sk-table"><thead><tr><th>Employee</th><th>Structure</th><th>Basic Salary</th><th>Effective From</th><th>Status</th><th style="text-align:right">Actions</th></tr></thead>
        <tbody><tr v-for="assignment in filteredAssignments" :key="assignment.id"><td><strong>{{ assignment.employee_name }}</strong><div style="font-size:11px;color:var(--sk-gray-400)">{{ assignment.employee_id_num }}</div></td><td>{{ assignment.structure_name }}</td><td class="text-mono">GHS {{ formatAmount(assignment.basic_salary) }}</td><td>{{ formatDate(assignment.effective_from) }}</td><td><span class="sk-badge" :class="assignment.is_current ? 'badge-active' : 'badge-inactive'">{{ assignment.is_current ? 'Current' : 'Historical' }}</span></td><td style="text-align:right"><button class="sk-btn sk-btn-ghost sk-btn-sm" @click="editAssignment(assignment)"><i class="bi bi-pencil"></i></button></td></tr></tbody>
      </table></div>
    </div>

    <div v-if="showModal" class="sk-modal-backdrop" @click.self="closeModal"><div class="sk-modal sk-modal-md">
      <div class="sk-modal-header"><h5 class="sk-modal-title">{{ editing ? 'Edit' : 'Assign' }} Employee Salary</h5><button class="sk-modal-close" @click="closeModal"><i class="bi bi-x"></i></button></div>
      <div class="sk-modal-body"><div class="row g-3">
        <div class="col-12"><label class="sk-label">Employee</label><select class="sk-select" v-model="form.employee" :disabled="!!editing"><option value="">Select employee...</option><option v-for="employee in employees" :key="employee.id" :value="employee.id">{{ employee.full_name || `${employee.first_name} ${employee.last_name}` }} ({{ employee.employee_id }})</option></select></div>
        <div class="col-12"><label class="sk-label">Salary Structure</label><select class="sk-select" v-model="form.structure"><option value="">Select structure...</option><option v-for="structure in structures" :key="structure.id" :value="structure.id">{{ structure.name }} ({{ structure.code }})</option></select></div>
        <div class="col-md-6"><label class="sk-label">Basic Salary (GHS)</label><input class="sk-input" type="number" min="0" step="0.01" v-model.number="form.basic_salary" /></div>
        <div class="col-md-6"><label class="sk-label">Effective From</label><input class="sk-input" type="date" v-model="form.effective_from" /></div>
        <div class="col-12"><label class="sk-label">Notes</label><textarea class="sk-textarea" v-model="form.notes"></textarea></div>
      </div></div>
      <div class="sk-modal-footer"><button class="sk-btn sk-btn-ghost" @click="closeModal">Cancel</button><button class="sk-btn sk-btn-primary" @click="save" :disabled="saving"><span v-if="saving" class="spinner-border spinner-border-sm"></span> Save Assignment</button></div>
    </div></div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { employeeApi, payrollApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const employees = ref([])
const structures = ref([])
const assignments = ref([])
const loading = ref(true)
const saving = ref(false)
const search = ref('')
const showModal = ref(false)
const editing = ref(null)
const form = ref({ employee: '', structure: '', basic_salary: 0, effective_from: '', notes: '' })

const filteredAssignments = computed(() => assignments.value.filter(item => {
  const text = `${item.employee_name || ''} ${item.employee_id_num || ''}`.toLowerCase()
  return text.includes(search.value.toLowerCase())
}))

function resetForm() {
  form.value = { employee: '', structure: '', basic_salary: 0, effective_from: new Date().toISOString().slice(0, 10), notes: '' }
}
function openCreate() { editing.value = null; resetForm(); showModal.value = true }
function editAssignment(item) { editing.value = item.id; form.value = { employee: item.employee, structure: item.structure, basic_salary: Number(item.basic_salary), effective_from: item.effective_from, notes: item.notes || '' }; showModal.value = true }
function closeModal() { showModal.value = false; editing.value = null }
function formatAmount(value) { return Number(value || 0).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' }) : '—' }

async function load() {
  loading.value = true
  try {
    const [employeeData, structureData, assignmentData] = await Promise.all([employeeApi.list({ page_size: 500 }), payrollApi.structures(), payrollApi.employeeSalaries()])
    employees.value = employeeData.results || employeeData || []
    structures.value = structureData.results || structureData || []
    assignments.value = assignmentData.results || assignmentData || []
  } catch (error) { toast.error('Failed to load salary data', error.message) }
  finally { loading.value = false }
}

async function save() {
  if (!form.value.employee || !form.value.structure || !form.value.basic_salary || !form.value.effective_from) {
    toast.warning('Validation', 'Employee, structure, basic salary, and effective date are required.')
    return
  }
  saving.value = true
  try {
    if (editing.value) await payrollApi.updateEmployeeSalary(editing.value, form.value)
    else await payrollApi.createEmployeeSalary(form.value)
    toast.success(editing.value ? 'Salary updated' : 'Salary assigned', 'This employee will now be included in payroll.')
    closeModal(); await load()
  } catch (error) { toast.error('Save failed', error.message) }
  finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.sk-label { display:block; margin-bottom:6px; }
</style>
