<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Leave Management</h1>
        <div class="page-subtitle">Manage leave applications and balances</div>
      </div>
      <router-link v-if="auth.user?.employee_profile_id" to="/leaves/apply" class="sk-btn sk-btn-primary">
        <i class="bi bi-calendar-plus-fill"></i> Apply for Leave
      </router-link>
    </div>

    <!-- Leave balances -->
    <div class="row g-3 mb-4">
      <div v-for="bal in balances" :key="bal.leave_type" class="col-sm-6 col-lg-3">
        <div class="sk-card" style="padding:18px 20px">
          <div style="font-size:13px;font-weight:600;color:var(--sk-gray-800);margin-bottom:10px">{{ bal.leave_type }}</div>
          <div style="font-size:26px;font-weight:700;color:var(--sk-blue-mid)">{{ bal.available }}</div>
          <div style="font-size:11.5px;color:var(--sk-gray-500);margin-bottom:10px">days available</div>
          <div class="sk-progress mb-1">
            <div class="sk-progress-bar"
              :style="`width:${(bal.taken / bal.entitled) * 100}%;background:${progressColor(bal.taken, bal.entitled)}`">
            </div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--sk-gray-400)">
            <span>{{ bal.taken }} taken</span>
            <span>{{ bal.entitled }} total</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="sk-tabs">
      <button class="sk-tab" :class="{ active: tab === 'mine' }" @click="tab = 'mine'">
        <i class="bi bi-person"></i> My Applications
      </button>
      <button v-if="auth.isHR" class="sk-tab" :class="{ active: tab === 'team' }" @click="tab = 'team'">
        <i class="bi bi-people"></i> All Applications
        <span v-if="pendingCount > 0" class="sidebar-badge ms-1" style="background:var(--sk-warning);color:var(--sk-dark)">{{ pendingCount }}</span>
      </button>
      <button v-if="auth.isHR" class="sk-tab" :class="{ active: tab === 'calendar' }" @click="tab = 'calendar'">
        <i class="bi bi-calendar3"></i> Leave Calendar
      </button>
    </div>

    <!-- Applications Table -->
    <div v-if="tab !== 'calendar'" class="sk-card">
      <div class="sk-card-header">
        <div class="d-flex gap-2 ms-auto">
          <select class="sk-select" v-model="filterStatus" @change="loadApplications" style="width:auto">
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th v-if="tab === 'team'">Employee</th>
              <th>Leave Type</th>
              <th>From</th>
              <th>To</th>
              <th>Days</th>
              <th>Applied</th>
              <th>Status</th>
              <th v-if="auth.isHR && tab === 'team'" style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-else-if="!applications.length"><td colspan="8"><div class="empty-state"><i class="bi bi-calendar-check"></i><h5>No applications found</h5></div></td></tr>
            <tr v-for="app in applications" :key="app.id">
              <td v-if="tab === 'team'">
                <div class="d-flex align-items-center gap-2">
                  <div class="avatar avatar-sm">{{ initials(app.employee_name) }}</div>
                  <div>
                    <div style="font-weight:500">{{ app.employee_name }}</div>
                    <div style="font-size:11.5px;color:var(--sk-gray-400)">{{ app.department }}</div>
                  </div>
                </div>
              </td>
              <td>{{ app.leave_type_name }}</td>
              <td>{{ formatDate(app.start_date) }}</td>
              <td>{{ formatDate(app.end_date) }}</td>
              <td><strong>{{ app.days_requested }}</strong></td>
              <td>{{ formatDate(app.applied_at) }}</td>
              <td><span class="sk-badge" :class="`badge-${app.status}`">{{ app.status }}</span></td>
              <td v-if="auth.isHR && tab === 'team'">
                <div v-if="app.status === 'pending'" class="d-flex justify-content-end gap-1">
                  <button class="sk-btn sk-btn-primary sk-btn-sm" @click="approveLeave(app)">
                    <i class="bi bi-check-lg"></i> Approve
                  </button>
                  <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="openRejectModal(app)">
                    <i class="bi bi-x-lg"></i> Reject
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Calendar view -->
    <div v-if="tab === 'calendar'" class="sk-card">
      <div class="sk-card-body">
        <div class="leave-calendar">
          <div v-for="item in calendarItems" :key="`${item.employee__first_name}${item.start_date}`" class="leave-cal-item">
            <div class="leave-cal-name">{{ item.employee__first_name }} {{ item.employee__last_name }}</div>
            <div class="leave-cal-dates">{{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
            <div class="leave-cal-type sk-badge badge-approved">{{ item.leave_type__name }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="rejectTarget" class="sk-modal-backdrop" @click.self="rejectTarget = null">
      <div class="sk-modal sk-modal-sm">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Reject Leave Application</h5>
          <button class="sk-modal-close" @click="rejectTarget = null"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <p style="font-size:13.5px;color:var(--sk-gray-600)">Rejecting leave for <strong>{{ rejectTarget.employee_name }}</strong>.</p>
          <div class="sk-form-group">
            <label class="sk-label">Reason for Rejection</label>
            <textarea class="sk-textarea" v-model="rejectReason" placeholder="Provide a reason..."></textarea>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="rejectTarget = null">Cancel</button>
          <button class="sk-btn sk-btn-danger" @click="confirmReject">
            <i class="bi bi-x-lg"></i> Reject Leave
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { leaveApi, employeeApi } from '@/utils/api'

const auth = useAuthStore()
const toast = useToastStore()
const tab = ref('mine')
const applications = ref([])
const balances = ref([])
const calendarItems = ref([])
const loading = ref(true)
const filterStatus = ref('')
const rejectTarget = ref(null)
const rejectReason = ref('')

const pendingCount = computed(() => applications.value.filter(a => a.status === 'pending').length)

async function loadApplications() {
  loading.value = true
  try {
    const params = { status: filterStatus.value || undefined }
    if (tab.value === 'mine' && auth.user?.employee_profile_id) {
      params.employee = auth.user.employee_profile_id
    }
    const data = await leaveApi.applications(params)
    applications.value = data.results || data
  } catch (e) {
    toast.error('Failed to load applications', e.message)
  } finally {
    loading.value = false
  }
}

async function loadBalances() {
  try {
    if (auth.user?.employee_profile_id) {
      const data = await employeeApi.leaveBalances(auth.user.employee_profile_id)
      balances.value = data
    }
  } catch {}
}

async function loadCalendar() {
  try {
    const data = await leaveApi.calendar()
    calendarItems.value = data
  } catch {}
}

async function approveLeave(app) {
  try {
    await leaveApi.approve(app.id)
    toast.success('Leave approved', `${app.employee_name}'s leave has been approved`)
    loadApplications()
  } catch (e) {
    toast.error('Failed to approve', e.message)
  }
}

function openRejectModal(app) {
  rejectTarget.value = app
  rejectReason.value = ''
}

async function confirmReject() {
  try {
    await leaveApi.reject(rejectTarget.value.id, rejectReason.value)
    toast.success('Leave rejected')
    rejectTarget.value = null
    loadApplications()
  } catch (e) {
    toast.error('Failed to reject', e.message)
  }
}

function initials(name) {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function formatDate(d) {
  if (!d) return '–'
  return new Date(d).toLocaleDateString('en-GH', { day: 'numeric', month: 'short', year: 'numeric' })
}

function progressColor(taken, entitled) {
  const pct = taken / entitled
  if (pct < 0.5) return 'var(--sk-success)'
  if (pct < 0.8) return 'var(--sk-warning)'
  return 'var(--sk-danger)'
}

watch(tab, (newTab) => {
  if (newTab === 'calendar') loadCalendar()
  else loadApplications()
})

onMounted(() => {
  loadApplications()
  loadBalances()
})
</script>

<style scoped>
.leave-calendar {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;
}

.leave-cal-item {
  background: var(--sk-gray-50); border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-md); padding: 14px 16px;
  border-left: 4px solid var(--sk-blue-mid);
}

.leave-cal-name { font-weight: 600; font-size: 13.5px; margin-bottom: 4px; }
.leave-cal-dates { font-size: 12px; color: var(--sk-gray-500); margin-bottom: 8px; }
</style>
