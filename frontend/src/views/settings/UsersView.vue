<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">User Management</h1><div class="page-subtitle">Manage system users and access roles</div></div>
      <button class="sk-btn sk-btn-primary" @click="showModal = true"><i class="bi bi-person-plus-fill"></i> Add User</button>
    </div>

    <div class="sk-card">
      <div class="sk-card-header">
        <div class="sk-input-group" style="width:240px">
          <i class="bi bi-search input-icon"></i>
          <input type="text" class="sk-input" v-model="search" placeholder="Search users..." />
        </div>
        <select class="sk-select ms-2" v-model="roleFilter" style="width:auto">
          <option value="">All Roles</option>
          <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
        </select>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead><tr><th>User</th><th>Role</th><th>Joined</th><th>Last Login</th><th>Status</th><th style="text-align:right">Actions</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="6" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-for="u in filteredUsers" :key="u.id">
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="avatar avatar-sm">{{ `${u.first_name?.[0]||''}${u.last_name?.[0]||''}`.toUpperCase() }}</div>
                  <div>
                    <div style="font-weight:500">{{ u.first_name }} {{ u.last_name }}</div>
                    <div style="font-size:11.5px;color:var(--sk-gray-400)">{{ u.email }}</div>
                  </div>
                </div>
              </td>
              <td><span class="sk-badge badge-processing">{{ roleLabel(u.role) }}</span></td>
              <td style="font-size:12.5px">{{ formatDate(u.date_joined) }}</td>
              <td style="font-size:12.5px;color:var(--sk-gray-500)">{{ u.last_login_ip || '–' }}</td>
              <td><span class="sk-badge" :class="u.is_active ? 'badge-active' : 'badge-inactive'">{{ u.is_active ? 'Active' : 'Inactive' }}</span></td>
              <td>
                <div class="d-flex justify-content-end gap-1">
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="editUser(u)"><i class="bi bi-pencil"></i></button>
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="toggleActive(u)" :title="u.is_active ? 'Deactivate' : 'Activate'">
                    <i class="bi" :class="u.is_active ? 'bi-person-x' : 'bi-person-check'"></i>
                  </button>
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="resetPassword(u)" title="Reset password">
                    <i class="bi bi-key"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- User Modal -->
    <div v-if="showModal" class="sk-modal-backdrop" @click.self="closeModal">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">{{ editing ? 'Edit User' : 'Add New User' }}</h5>
          <button class="sk-modal-close" @click="closeModal"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="row g-3">
            <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">First Name</label><input type="text" class="sk-input" v-model="form.first_name" /></div></div>
            <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Last Name</label><input type="text" class="sk-input" v-model="form.last_name" /></div></div>
            <div class="col-12"><div class="sk-form-group"><label class="sk-label">Email</label><input type="email" class="sk-input" v-model="form.email" :disabled="editing" /></div></div>
            <div v-if="!editing" class="col-12"><div class="sk-form-group"><label class="sk-label">Password</label><input type="password" class="sk-input" v-model="form.password" /></div></div>
            <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Role</label>
              <select class="sk-select" v-model="form.role">
                <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div></div>
            <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Phone</label><input type="text" class="sk-input" v-model="form.phone" /></div></div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="closeModal">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="saveUser" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm"></span>
            {{ editing ? 'Update' : 'Create User' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { userApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const users = ref([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editing = ref(null)
const search = ref('')
const roleFilter = ref('')
const form = ref({ first_name: '', last_name: '', email: '', password: '', role: 'employee', phone: '' })

const roles = [
  { value: 'company_admin', label: 'Company Admin' },
  { value: 'hr_manager', label: 'HR Manager' },
  { value: 'payroll_officer', label: 'Payroll Officer' },
  { value: 'finance_manager', label: 'Finance Manager' },
  { value: 'branch_manager', label: 'Branch Manager' },
  { value: 'employee', label: 'Employee' },
]

const filteredUsers = computed(() => {
  return users.value.filter(u => {
    const matchSearch = !search.value || `${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(search.value.toLowerCase())
    const matchRole = !roleFilter.value || u.role === roleFilter.value
    return matchSearch && matchRole
  })
})

function roleLabel(r) { return roles.find(x => x.value === r)?.label || r }
function formatDate(d) { if (!d) return '–'; return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' }) }

function editUser(u) { editing.value = u.id; form.value = { ...u }; showModal.value = true }
function closeModal() { showModal.value = false; editing.value = null; form.value = { first_name: '', last_name: '', email: '', password: '', role: 'employee', phone: '' } }

async function loadUsers() {
  loading.value = true
  try { const d = await userApi.list(); users.value = d.results || d } catch (e) { toast.error('Failed to load users', e.message) } finally { loading.value = false }
}

async function saveUser() {
  saving.value = true
  try {
    if (editing.value) { await userApi.update(editing.value, form.value); toast.success('User updated') }
    else { await userApi.create(form.value); toast.success('User created', `Temporary password set`) }
    closeModal(); loadUsers()
  } catch (e) { toast.error('Save failed', e.message) } finally { saving.value = false }
}

async function toggleActive(u) {
  await userApi.toggleActive(u.id)
  u.is_active = !u.is_active
  toast.success(u.is_active ? 'User activated' : 'User deactivated')
}

async function resetPassword(u) {
  const result = await userApi.resetPassword(u.id)
  toast.info('Password reset', result.message)
}

onMounted(loadUsers)
</script>
