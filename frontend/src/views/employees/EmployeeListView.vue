<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Employees</h1>
        <div class="page-subtitle">{{ total }} total employees across all branches</div>
      </div>
      <div class="d-flex gap-2">
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="exportEmployees">
          <i class="bi bi-download"></i> Export
        </button>
        <router-link v-if="auth.isHR" to="/employees/new" class="sk-btn sk-btn-primary sk-btn-sm">
          <i class="bi bi-person-plus-fill"></i> Add Employee
        </router-link>
      </div>
    </div>

    <!-- Filters -->
    <div class="sk-card mb-4">
      <div class="sk-card-body" style="padding:14px 20px">
        <div class="row g-3 align-items-end">
          <div class="col-md-4">
            <div class="sk-input-group">
              <i class="bi bi-search input-icon"></i>
              <input type="text" class="sk-input" v-model="filters.search" placeholder="Search name, ID, email..." @input="debouncedLoad" />
            </div>
          </div>
          <div class="col-md-2">
            <select class="sk-select" v-model="filters.status" @change="loadEmployees">
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="probation">Probation</option>
              <option value="on_leave">On Leave</option>
              <option value="suspended">Suspended</option>
              <option value="terminated">Terminated</option>
            </select>
          </div>
          <div class="col-md-2">
            <select class="sk-select" v-model="filters.employment_type" @change="loadEmployees">
              <option value="">All Types</option>
              <option value="full_time">Full Time</option>
              <option value="part_time">Part Time</option>
              <option value="contract">Contract</option>
              <option value="intern">Intern</option>
            </select>
          </div>
          <div class="col-md-2">
            <select class="sk-select" v-model="filters.department" @change="loadEmployees">
              <option value="">All Departments</option>
              <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <div class="d-flex gap-2">
              <button class="sk-btn" :class="viewMode === 'table' ? 'sk-btn-primary' : 'sk-btn-ghost'" @click="viewMode = 'table'">
                <i class="bi bi-list-ul"></i>
              </button>
              <button class="sk-btn" :class="viewMode === 'grid' ? 'sk-btn-primary' : 'sk-btn-ghost'" @click="viewMode = 'grid'">
                <i class="bi bi-grid-3x3-gap"></i>
              </button>
              <button class="sk-btn sk-btn-ghost" @click="resetFilters">
                <i class="bi bi-x-circle"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table view -->
    <div v-if="viewMode === 'table'" class="sk-card">
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>ID</th>
              <th>Department</th>
              <th>Job Title</th>
              <th>Type</th>
              <th>Status</th>
              <th>Hire Date</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8">
                <div class="d-flex justify-content-center p-4">
                  <div class="spinner-border text-primary spinner-border-sm"></div>
                </div>
              </td>
            </tr>
            <tr v-else-if="employees.length === 0">
              <td colspan="8">
                <div class="empty-state">
                  <i class="bi bi-people"></i>
                  <h5>No employees found</h5>
                  <p>Try adjusting your search filters</p>
                </div>
              </td>
            </tr>
            <tr v-for="emp in employees" :key="emp.id" @click="goToEmployee(emp.id)" style="cursor:pointer">
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="avatar avatar-sm" :style="emp.photo ? '' : ''">
                    <img v-if="emp.photo" :src="emp.photo" :alt="emp.full_name" style="width:100%;height:100%;border-radius:50%;object-fit:cover" />
                    <span v-else>{{ initials(emp) }}</span>
                  </div>
                  <div>
                    <div style="font-weight:600;font-size:13.5px">{{ emp.full_name }}</div>
                    <div style="font-size:11.5px;color:var(--sk-gray-400)">{{ emp.work_email }}</div>
                  </div>
                </div>
              </td>
              <td><code style="font-family:var(--font-mono);font-size:12px;background:var(--sk-gray-100);padding:2px 6px;border-radius:4px">{{ emp.employee_id }}</code></td>
              <td>{{ emp.department_name || '–' }}</td>
              <td style="font-size:13px">{{ emp.job_title }}</td>
              <td>
                <span class="sk-badge badge-active" style="background:var(--sk-gray-100);color:var(--sk-gray-700)">
                  {{ empTypeLabel(emp.employment_type) }}
                </span>
              </td>
              <td>
                <span class="sk-badge" :class="statusBadge(emp.status)">
                  <span class="sk-badge-dot" :class="statusDot(emp.status)"></span>
                  {{ emp.status }}
                </span>
              </td>
              <td>{{ formatDate(emp.hire_date) }}</td>
              <td style="text-align:right">
                <div class="d-flex justify-content-end gap-1">
                  <router-link :to="`/employees/${emp.id}`" class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon" @click.stop>
                    <i class="bi bi-eye"></i>
                  </router-link>
                  <router-link v-if="auth.isHR" :to="`/employees/${emp.id}/edit`" class="sk-btn sk-btn-ghost sk-btn-sm sk-btn-icon" @click.stop>
                    <i class="bi bi-pencil"></i>
                  </router-link>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="sk-pagination">
        <button class="sk-page-btn" :disabled="page <= 1" @click="page--; loadEmployees()">
          <i class="bi bi-chevron-left"></i>
        </button>
        <button
          v-for="p in visiblePages" :key="p"
          class="sk-page-btn" :class="{ active: p === page }"
          @click="page = p; loadEmployees()"
        >{{ p }}</button>
        <button class="sk-page-btn" :disabled="page >= totalPages" @click="page++; loadEmployees()">
          <i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- Grid view -->
    <div v-else class="row g-3">
      <div v-if="loading" v-for="i in 8" :key="i" class="col-sm-6 col-lg-4 col-xl-3">
        <div class="sk-card" style="padding:20px;text-align:center">
          <div class="skeleton" style="width:60px;height:60px;border-radius:50%;margin:0 auto 12px"></div>
          <div class="skeleton" style="width:70%;height:16px;margin:0 auto 8px"></div>
          <div class="skeleton" style="width:50%;height:13px;margin:0 auto"></div>
        </div>
      </div>
      <div v-else v-for="emp in employees" :key="emp.id" class="col-sm-6 col-lg-4 col-xl-3">
        <div class="sk-card emp-card" @click="goToEmployee(emp.id)" style="cursor:pointer;padding:20px;text-align:center">
          <div class="avatar avatar-lg mx-auto mb-3">
            <img v-if="emp.photo" :src="emp.photo" :alt="emp.full_name" style="width:100%;height:100%;border-radius:50%;object-fit:cover" />
            <span v-else>{{ initials(emp) }}</span>
          </div>
          <div style="font-weight:600;font-size:14px">{{ emp.full_name }}</div>
          <div style="font-size:12px;color:var(--sk-gray-500);margin-top:2px">{{ emp.job_title }}</div>
          <div style="font-size:11.5px;color:var(--sk-gray-400);margin-top:4px">{{ emp.department_name || 'No Department' }}</div>
          <div class="mt-3">
            <span class="sk-badge" :class="statusBadge(emp.status)">{{ emp.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { employeeApi, companyApi } from '@/utils/api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const employees = ref([])
const departments = ref([])
const total = ref(0)
const loading = ref(true)
const page = ref(1)
const pageSize = 25
const viewMode = ref('table')
const filters = ref({ search: route.query.search || '', status: '', employment_type: '', department: '' })

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const visiblePages = computed(() => {
  const pages = []
  for (let i = Math.max(1, page.value - 2); i <= Math.min(totalPages.value, page.value + 2); i++) {
    pages.push(i)
  }
  return pages
})

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadEmployees, 400)
}

async function loadEmployees() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      search: filters.value.search || undefined,
      status: filters.value.status || undefined,
      employment_type: filters.value.employment_type || undefined,
      department: filters.value.department || undefined,
    }
    const data = await employeeApi.list(params)
    employees.value = data.results || data
    total.value = data.count || data.length
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = { search: '', status: '', employment_type: '', department: '' }
  page.value = 1
  loadEmployees()
}

function goToEmployee(id) { router.push(`/employees/${id}`) }

function initials(emp) {
  return `${emp.first_name?.[0] || ''}${emp.last_name?.[0] || ''}`.toUpperCase()
}

function formatDate(d) {
  if (!d) return '–'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

function statusBadge(s) {
  const m = { active: 'badge-active', probation: 'badge-processing', on_leave: 'badge-pending', suspended: 'badge-rejected', terminated: 'badge-cancelled' }
  return m[s] || 'badge-inactive'
}

function statusDot(s) {
  const m = { active: 'dot-active', probation: '', on_leave: 'dot-pending', terminated: 'dot-inactive', suspended: '' }
  return m[s] || ''
}

function empTypeLabel(t) {
  const m = { full_time: 'Full Time', part_time: 'Part Time', contract: 'Contract', intern: 'Intern', casual: 'Casual' }
  return m[t] || t
}

async function exportEmployees() {
  // Trigger CSV download
}

onMounted(async () => {
  const [, deps] = await Promise.all([loadEmployees(), companyApi.departments()])
  departments.value = deps.results || deps
})
</script>

<style scoped>
.emp-card { transition: var(--transition); }
.emp-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
</style>
