<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Salary Structures</h1>
        <div class="page-subtitle">Configure pay components and salary structures</div>
      </div>
      <div class="d-flex gap-2">
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="openNewComponent">
          <i class="bi bi-plus-lg"></i> Add Component
        </button>
        <button class="sk-btn sk-btn-primary sk-btn-sm" @click="openNewStructure">
          <i class="bi bi-diagram-3-fill"></i> New Structure
        </button>
      </div>
    </div>

    <div class="row g-4">
      <!-- Pay Components -->
      <div class="col-lg-5">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-puzzle-fill" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Pay Components</h5>
            <span style="font-size:12px;color:var(--sk-gray-400);margin-left:auto">
              {{ components.length }} total
            </span>
          </div>
          <div v-if="loading" class="text-center p-4">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!components.length" class="empty-state" style="padding:30px">
            <i class="bi bi-puzzle"></i>
            <h5>No components yet</h5>
            <p>Add pay components like Basic Salary, Housing Allowance, etc.</p>
            <button class="sk-btn sk-btn-primary sk-btn-sm mt-2" @click="openNewComponent">
              Add First Component
            </button>
          </div>
          <div v-else class="sk-table-wrapper">
            <table class="sk-table">
              <thead>
                <tr>
                  <th>Name / Code</th>
                  <th>Type</th>
                  <th style="text-align:center">Taxable</th>
                  <th style="text-align:center">SSNIT</th>
                  <th style="text-align:right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in components" :key="c.id">
                  <td>
                    <div style="font-weight:600;font-size:13px">{{ c.name }}</div>
                    <code style="font-size:10.5px;background:var(--sk-gray-100);padding:1px 5px;border-radius:3px">
                      {{ c.code }}
                    </code>
                  </td>
                  <td>
                    <span class="sk-badge"
                      :class="c.component_type === 'earning' ? 'badge-active' : c.component_type === 'deduction' ? 'badge-rejected' : 'badge-pending'"
                      style="font-size:10px">
                      {{ c.component_type }}
                    </span>
                  </td>
                  <td style="text-align:center">
                    <i class="bi" style="font-size:15px"
                      :class="c.is_taxable ? 'bi-check-circle-fill text-success' : 'bi-x-circle text-danger'"></i>
                  </td>
                  <td style="text-align:center">
                    <i class="bi" style="font-size:15px"
                      :class="c.is_pensionable ? 'bi-check-circle-fill text-success' : 'bi-x-circle text-danger'"></i>
                  </td>
                  <td style="text-align:right">
                    <div class="d-flex justify-content-end gap-1">
                      <button class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon" @click="editComponent(c)">
                        <i class="bi bi-pencil"></i>
                      </button>
                      <button class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon"
                        style="color:var(--sk-danger)" @click="toggleComponent(c)">
                        <i class="bi" :class="c.is_active ? 'bi-eye-slash' : 'bi-eye'"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Salary Structures -->
      <div class="col-lg-7">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-diagram-3-fill" style="color:var(--sk-accent)"></i>
            <h5 class="sk-card-title">Salary Structures</h5>
          </div>
          <div v-if="loading" class="text-center p-4">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!structures.length" class="empty-state" style="padding:40px">
            <i class="bi bi-diagram-3"></i>
            <h5>No structures yet</h5>
            <p>Create a salary structure to group pay components for employees</p>
            <button class="sk-btn sk-btn-primary sk-btn-sm mt-2" @click="openNewStructure">
              Create First Structure
            </button>
          </div>
          <div v-else class="sk-card-body" style="padding-top:4px">
            <div v-for="s in structures" :key="s.id" class="structure-card">
              <div class="d-flex align-items-center justify-content-between">
                <div>
                  <div style="font-weight:700;font-size:14px">{{ s.name }}</div>
                  <div class="d-flex gap-2 mt-1">
                    <code style="font-size:10.5px;background:var(--sk-gray-100);padding:1px 5px;border-radius:3px">
                      {{ s.code }}
                    </code>
                    <span v-if="s.is_default" class="sk-badge badge-active" style="font-size:10px">Default</span>
                    <span class="sk-badge badge-inactive" style="font-size:10px">
                      {{ s.components_count }} components
                    </span>
                  </div>
                </div>
                <div class="d-flex gap-1 align-items-center">
                  <button class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon" @click="editStructure(s)">
                    <i class="bi bi-pencil"></i>
                  </button>
                </div>
              </div>
              <p v-if="s.description"
                style="font-size:12.5px;color:var(--sk-gray-500);margin:8px 0 0">
                {{ s.description }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Component Modal ── -->
    <div v-if="showComponentModal" class="sk-modal-backdrop" @click.self="closeComponentModal">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">{{ editingComp ? 'Edit' : 'Add' }} Pay Component</h5>
          <button class="sk-modal-close" @click="closeComponentModal"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="row g-3">
            <div class="col-md-8">
              <div class="sk-form-group">
                <label class="sk-label">Component Name <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="compForm.name"
                  placeholder="e.g. Basic Salary, Housing Allowance" required />
              </div>
            </div>
            <div class="col-md-4">
              <div class="sk-form-group">
                <label class="sk-label">Code <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="compForm.code"
                  placeholder="e.g. BASIC" :disabled="!!editingComp"
                  style="text-transform:uppercase"
                  @input="compForm.code = compForm.code.toUpperCase()" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Component Type <span class="text-danger">*</span></label>
                <select class="sk-select" v-model="compForm.component_type">
                  <option value="earning">Earning (adds to gross)</option>
                  <option value="deduction">Deduction (reduces net pay)</option>
                  <option value="employer_contribution">Employer Contribution</option>
                </select>
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Calculation Method</label>
                <select class="sk-select" v-model="compForm.calculation_method">
                  <option value="fixed">Fixed Amount</option>
                  <option value="pct_basic">Percentage of Basic Salary</option>
                  <option value="pct_gross">Percentage of Gross Pay</option>
                </select>
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">
                  Default Value
                  <span style="font-weight:400;font-size:11px;color:var(--sk-gray-400)">
                    ({{ compForm.calculation_method === 'fixed' ? 'GHS amount' : 'decimal e.g. 0.25 = 25%' }})
                  </span>
                </label>
                <input type="number" class="sk-input" v-model.number="compForm.default_value"
                  step="0.01" min="0" />
              </div>
            </div>
            <div class="col-md-6">
              <div class="sk-form-group">
                <label class="sk-label">Sort Order</label>
                <input type="number" class="sk-input" v-model.number="compForm.sort_order" min="0" />
              </div>
            </div>
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Description</label>
                <textarea class="sk-textarea" v-model="compForm.description"
                  style="min-height:60px"
                  placeholder="Optional: describe when this component applies…"></textarea>
              </div>
            </div>
            <div class="col-12">
              <div class="d-flex gap-4 flex-wrap">
                <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                  <input type="checkbox" v-model="compForm.is_taxable" />
                  <span><strong>Taxable</strong> — included in PAYE calculation</span>
                </label>
                <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                  <input type="checkbox" v-model="compForm.is_pensionable" />
                  <span><strong>Pensionable</strong> — included in SSNIT base</span>
                </label>
                <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                  <input type="checkbox" v-model="compForm.display_on_payslip" />
                  <span>Show on payslip</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="closeComponentModal">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="saveComponent" :disabled="savingComp">
            <span v-if="savingComp" class="spinner-border spinner-border-sm"></span>
            {{ editingComp ? 'Save Changes' : 'Add Component' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Structure Modal ── -->
    <div v-if="showStructureModal" class="sk-modal-backdrop" @click.self="closeStructureModal">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">{{ editingStructure ? 'Edit' : 'New' }} Salary Structure</h5>
          <button class="sk-modal-close" @click="closeStructureModal"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="row g-3">
            <div class="col-md-8">
              <div class="sk-form-group">
                <label class="sk-label">Structure Name <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="structForm.name"
                  placeholder="e.g. Standard Monthly, Executive Package" />
              </div>
            </div>
            <div class="col-md-4">
              <div class="sk-form-group">
                <label class="sk-label">Code <span class="text-danger">*</span></label>
                <input type="text" class="sk-input" v-model="structForm.code"
                  :disabled="!!editingStructure"
                  placeholder="e.g. STD"
                  @input="structForm.code = structForm.code.toUpperCase()"
                  style="text-transform:uppercase" />
              </div>
            </div>
            <div class="col-12">
              <div class="sk-form-group">
                <label class="sk-label">Description</label>
                <textarea class="sk-textarea" v-model="structForm.description"
                  style="min-height:70px"
                  placeholder="Describe this salary structure…"></textarea>
              </div>
            </div>
            <div class="col-12">
              <div class="d-flex gap-3">
                <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                  <input type="checkbox" v-model="structForm.is_default" />
                  <span>Set as default structure</span>
                </label>
                <label class="d-flex align-items-center gap-2" style="cursor:pointer;font-size:13.5px">
                  <input type="checkbox" v-model="structForm.is_active" />
                  <span>Active</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="closeStructureModal">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="saveStructure" :disabled="savingStruct">
            <span v-if="savingStruct" class="spinner-border spinner-border-sm"></span>
            {{ editingStructure ? 'Save Changes' : 'Create Structure' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { payrollApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const components = ref([])
const structures  = ref([])
const loading     = ref(true)

// ── Component modal state ──────────────────────────────────────────────────────
const showComponentModal = ref(false)
const editingComp        = ref(null)   // null = new, id string = editing
const savingComp         = ref(false)

const defaultCompForm = () => ({
  name: '', code: '', component_type: 'earning',
  calculation_method: 'fixed', default_value: 0,
  is_taxable: true, is_pensionable: true,
  display_on_payslip: true, is_active: true,
  description: '', sort_order: 0,
})
const compForm = ref(defaultCompForm())

// ── Structure modal state ──────────────────────────────────────────────────────
const showStructureModal = ref(false)
const editingStructure   = ref(null)
const savingStruct       = ref(false)

const defaultStructForm = () => ({
  name: '', code: '', description: '',
  is_default: false, is_active: true,
})
const structForm = ref(defaultStructForm())

// ── Component actions ──────────────────────────────────────────────────────────
function openNewComponent() {
  editingComp.value = null
  compForm.value    = defaultCompForm()
  showComponentModal.value = true
}

function editComponent(c) {
  editingComp.value = c.id
  compForm.value    = {
    name:               c.name,
    code:               c.code,
    component_type:     c.component_type,
    calculation_method: c.calculation_method,
    default_value:      parseFloat(c.default_value || 0),
    is_taxable:         c.is_taxable,
    is_pensionable:     c.is_pensionable,
    display_on_payslip: c.display_on_payslip,
    is_active:          c.is_active,
    description:        c.description || '',
    sort_order:         c.sort_order  || 0,
  }
  showComponentModal.value = true
}

function closeComponentModal() {
  showComponentModal.value = false
  editingComp.value        = null
  compForm.value           = defaultCompForm()
}

async function saveComponent() {
  if (!compForm.value.name || !compForm.value.code) {
    toast.warning('Validation', 'Name and Code are required.')
    return
  }

  savingComp.value = true
  try {
    // NOTE: 'company' is read_only on the serializer — backend sets it from request.user
    const payload = { ...compForm.value }

    if (editingComp.value) {
      await payrollApi.updateComponent(editingComp.value, payload)
      toast.success('Component updated')
    } else {
      await payrollApi.createComponent(payload)
      toast.success('Component added')
    }
    closeComponentModal()
    await loadData()
  } catch (e) {
    toast.error('Save failed', e.message)
  } finally {
    savingComp.value = false
  }
}

async function toggleComponent(c) {
  try {
    await payrollApi.updateComponent(c.id, { is_active: !c.is_active })
    c.is_active = !c.is_active
    toast.info(c.is_active ? 'Component activated' : 'Component deactivated')
  } catch (e) {
    toast.error('Update failed', e.message)
  }
}

// ── Structure actions ──────────────────────────────────────────────────────────
function openNewStructure() {
  editingStructure.value   = null
  structForm.value         = defaultStructForm()
  showStructureModal.value = true
}

function editStructure(s) {
  editingStructure.value = s.id
  structForm.value       = {
    name:        s.name,
    code:        s.code,
    description: s.description || '',
    is_default:  s.is_default,
    is_active:   s.is_active,
  }
  showStructureModal.value = true
}

function closeStructureModal() {
  showStructureModal.value = false
  editingStructure.value   = null
  structForm.value         = defaultStructForm()
}

async function saveStructure() {
  if (!structForm.value.name || !structForm.value.code) {
    toast.warning('Validation', 'Name and Code are required.')
    return
  }

  savingStruct.value = true
  try {
    // NOTE: 'company' is read_only on the serializer — backend sets it from request.user
    const payload = { ...structForm.value }

    if (editingStructure.value) {
      await payrollApi.updateStructure(editingStructure.value, payload)
      toast.success('Structure updated')
    } else {
      await payrollApi.createStructure(payload)
      toast.success('Structure created')
    }
    closeStructureModal()
    await loadData()
  } catch (e) {
    toast.error('Save failed', e.message)
  } finally {
    savingStruct.value = false
  }
}

// ── Load ───────────────────────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const [compsData, structsData] = await Promise.all([
      payrollApi.components(),
      payrollApi.structures(),
    ])
    components.value = compsData.results  || compsData  || []
    structures.value = structsData.results || structsData || []
  } catch (e) {
    toast.error('Failed to load data', e.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.structure-card {
  background: var(--sk-gray-50);
  border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin-bottom: 10px;
  transition: var(--transition);
}
.structure-card:hover {
  border-color: var(--sk-blue-light);
  background: white;
  box-shadow: var(--shadow-sm);
}
</style>
