<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="app-sidebar" :class="{ open: ui.sidebarOpen }">
      <div class="sidebar-logo">
        <router-link to="/" class="sidebar-brand">
          <div class="sidebar-brand-icon">S</div>
          <div class="sidebar-brand-name">
            <span>Sikasem</span>
            <span>by Sikaba Systems</span>
          </div>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="sidebar-link" :class="{ active: $route.name === 'dashboard' }">
          <i class="bi bi-grid-1x2-fill"></i> Dashboard
        </router-link>

        <div class="sidebar-section">People</div>

        <router-link v-if="auth.isHR" to="/employees" class="sidebar-link" :class="{ active: $route.path.startsWith('/employees') }">
          <i class="bi bi-people-fill"></i> Employees
        </router-link>

        <router-link to="/attendance" class="sidebar-link" :class="{ active: $route.path.startsWith('/attendance') }">
          <i class="bi bi-calendar3-week-fill"></i> Attendance
        </router-link>

        <router-link to="/leaves" class="sidebar-link" :class="{ active: $route.path.startsWith('/leaves') }">
          <i class="bi bi-calendar-check-fill"></i> Leave Management
          <span v-if="pendingLeaves > 0" class="sidebar-badge">{{ pendingLeaves }}</span>
        </router-link>

        <div class="sidebar-section">Payroll</div>

        <router-link v-if="auth.isPayroll" to="/payroll/periods" class="sidebar-link" :class="{ active: $route.path.startsWith('/payroll') }">
          <i class="bi bi-cash-stack"></i> Payroll Runs
        </router-link>

        <router-link to="/payslips" class="sidebar-link" :class="{ active: $route.name === 'payslips' }">
          <i class="bi bi-receipt-cutoff"></i> Payslips
        </router-link>

        <router-link v-if="auth.isHR" to="/payroll/structures" class="sidebar-link"
          :class="{ active: $route.name === 'salary-structures' }">
          <i class="bi bi-diagram-3-fill"></i> Salary Structures
        </router-link>

        <router-link v-if="auth.isHR" to="/payroll/employee-salaries" class="sidebar-link"
          :class="{ active: $route.name === 'employee-salaries' }">
          <i class="bi bi-person-vcard"></i> Employee Salaries
        </router-link>

        <router-link v-if="auth.isHR" to="/payroll/rules" class="sidebar-link"
          :class="{ active: $route.name === 'payroll-rules' }">
          <i class="bi bi-gear-wide-connected"></i> Rules Engine
        </router-link>

        <div class="sidebar-section">Finance</div>

        <router-link to="/loans" class="sidebar-link" :class="{ active: $route.path.startsWith('/loans') }">
          <i class="bi bi-bank2"></i> Loans & Advances
        </router-link>

        <router-link v-if="auth.isHR" to="/reports" class="sidebar-link"
          :class="{ active: $route.path.startsWith('/reports') }">
          <i class="bi bi-bar-chart-line-fill"></i> Reports & Analytics
        </router-link>

        <div class="sidebar-section">Intelligence</div>

        <router-link to="/ai-advisor" class="sidebar-link" :class="{ active: $route.name === 'ai-advisor' }">
          <i class="bi bi-stars"></i> AI Advisor
          <span class="sidebar-badge" style="background:var(--sk-blue-light);color:white">AI</span>
        </router-link>

        <template v-if="auth.isAdmin || auth.isHR">
          <div class="sidebar-section">Admin &amp; HR Setup</div>

          <router-link v-if="auth.isAdmin" to="/settings" class="sidebar-link" :class="{ active: $route.name === 'settings' }">
            <i class="bi bi-sliders"></i> Settings
          </router-link>
          <router-link v-if="auth.isAdmin" to="/settings/users" class="sidebar-link" :class="{ active: $route.name === 'settings-users' }">
            <i class="bi bi-person-gear"></i> User Management
          </router-link>

          <router-link v-for="item in masterDataLinks" :key="item.name" :to="item.to" class="sidebar-link" :class="{ active: $route.name === item.name }">
            <i class="bi" :class="item.icon"></i> {{ item.label }}
          </router-link>

          <router-link v-if="auth.isAdmin" to="/settings/audit" class="sidebar-link" :class="{ active: $route.name === 'audit-log' }">
            <i class="bi bi-shield-check"></i> Audit Log
          </router-link>
        </template>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/profile" class="sidebar-user" style="text-decoration:none">
          <div class="sidebar-user-avatar">{{ auth.initials() }}</div>
          <div class="sidebar-user-info">
            <div class="sidebar-user-name">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</div>
            <div class="sidebar-user-role">{{ roleLabel }}</div>
          </div>
          <i class="bi bi-chevron-right" style="color:var(--sk-gray-600);font-size:11px;margin-left:auto"></i>
        </router-link>
      </div>
    </aside>

    <!-- Main area -->
    <div class="app-main">
      <!-- Topbar -->
      <header class="app-topbar">
        <button class="sk-btn sk-btn-ghost sk-btn-icon" @click="ui.toggleSidebar()">
          <i class="bi bi-list" style="font-size:18px"></i>
        </button>

        <div class="sk-input-group flex-grow-1" style="max-width:360px">
          <i class="bi bi-search input-icon"></i>
          <input
            type="text" class="sk-input" v-model="searchQ"
            placeholder="Search employees, payslips..."
            @keydown.enter="doSearch"
          />
        </div>

        <div class="ms-auto d-flex align-items-center gap-3">
          <!-- Company pill -->
          <div class="d-none d-md-flex align-items-center gap-2"
            style="background:var(--sk-gray-100);padding:5px 12px;border-radius:99px">
            <i class="bi bi-building" style="color:var(--sk-gray-500);font-size:12px"></i>
            <span style="font-size:12px;font-weight:500;color:var(--sk-gray-700)">
              {{ auth.user?.company_name || 'Sikasem' }}
            </span>
          </div>

          <!-- Notifications -->
          <div class="position-relative" ref="notifRef">
            <button class="sk-btn sk-btn-ghost sk-btn-icon position-relative"
              @click="showNotifs = !showNotifs">
              <i class="bi bi-bell" style="font-size:17px"></i>
              <span v-if="unreadCount > 0"
                style="position:absolute;top:2px;right:2px;width:16px;height:16px;
                       background:var(--sk-danger);color:white;font-size:9px;font-weight:700;
                       border-radius:50%;display:flex;align-items:center;justify-content:center">
                {{ unreadCount > 9 ? '9+' : unreadCount }}
              </span>
            </button>

            <!-- Dropdown -->
            <div v-if="showNotifs"
              class="notif-dropdown sk-card"
              style="position:absolute;right:0;top:calc(100% + 8px);width:320px;z-index:200;max-height:400px;overflow-y:auto">
              <div class="sk-card-header">
                <span class="sk-card-title" style="font-size:14px">Notifications</span>
                <button class="sk-btn sk-btn-ghost sk-btn-sm ms-auto" @click="markAllRead">
                  Mark all read
                </button>
              </div>
              <div v-if="notifications.length === 0" class="empty-state" style="padding:24px 16px">
                <i class="bi bi-bell-slash" style="font-size:28px;opacity:.3;display:block;margin-bottom:8px"></i>
                <div style="font-size:13px;color:var(--sk-gray-500)">No notifications</div>
              </div>
              <div
                v-for="n in notifications" :key="n.id"
                class="notif-item" :class="{ unread: !n.is_read }"
                @click="markRead(n)"
              >
                <i class="bi" :class="notifIcon(n.notif_type)" style="font-size:15px;margin-top:2px"></i>
                <div>
                  <div style="font-size:13px;font-weight:500">{{ n.title }}</div>
                  <div style="font-size:11.5px;color:var(--sk-gray-500)">{{ n.message }}</div>
                  <div style="font-size:10.5px;color:var(--sk-gray-400);margin-top:3px">
                    {{ formatDate(n.created_at) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Logout -->
          <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="handleLogout">
            <i class="bi bi-box-arrow-right"></i>
            <span class="d-none d-md-inline">Logout</span>
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>

  <!-- Mobile backdrop -->
  <div
    v-if="ui.sidebarOpen && isMobile"
    style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:99"
    @click="ui.sidebarOpen = false"
  ></div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useUIStore }    from '@/stores/ui'
import { notifApi, leaveApi } from '@/utils/api'

const auth   = useAuthStore()
const toast  = useToastStore()
const ui     = useUIStore()
const router = useRouter()

const searchQ       = ref('')
const showNotifs    = ref(false)
const notifications = ref([])
const unreadCount   = ref(0)
const pendingLeaves = ref(0)
const notifRef      = ref(null)
const isMobile      = ref(window.innerWidth < 1024)

const masterDataLinks = [
  { name: 'branches', to: '/settings/branches', label: 'Branches', icon: 'bi-diagram-2' },
  { name: 'departments', to: '/settings/departments', label: 'Departments', icon: 'bi-diagram-3' },
  { name: 'job-grades', to: '/settings/job-grades', label: 'Job Grades', icon: 'bi-bar-chart-steps' },
  { name: 'salary-components', to: '/settings/salary-components', label: 'Salary Components', icon: 'bi-cash-coin' },
  { name: 'leave-types', to: '/settings/leave-types', label: 'Leave Types', icon: 'bi-calendar-check' },
  { name: 'loan-types', to: '/settings/loan-types', label: 'Loan Types', icon: 'bi-bank' },
  { name: 'shifts', to: '/settings/shifts', label: 'Shifts', icon: 'bi-clock' },
  { name: 'benefits', to: '/settings/benefits', label: 'Benefits', icon: 'bi-gift' },
  { name: 'holidays', to: '/settings/holidays', label: 'Public Holidays', icon: 'bi-calendar-event' },
]

const roleLabel = computed(() => {
  const map = {
    super_admin:     'Super Admin',
    company_admin:   'Company Admin',
    hr_manager:      'HR Manager',
    payroll_officer: 'Payroll Officer',
    finance_manager: 'Finance Manager',
    branch_manager:  'Branch Manager',
    employee:        'Employee',
  }
  return map[auth.user?.role] || auth.user?.role || ''
})

async function loadNotifs() {
  try {
    const [notifData, countData] = await Promise.all([
      notifApi.list(),
      notifApi.unreadCount(),
    ])
    notifications.value = notifData.results || notifData
    unreadCount.value   = countData.count   || 0
  } catch { /* silent */ }
}

async function loadPendingLeaves() {
  if (!auth.isHR) return
  try {
    const data = await leaveApi.applications({ status: 'pending' })
    const list = data.results || data
    pendingLeaves.value = Array.isArray(list) ? list.length : 0
  } catch { /* silent */ }
}

async function markAllRead() {
  try {
    await notifApi.markAllRead()
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
  } catch { /* silent */ }
}

async function markRead(n) {
  if (!n.is_read) {
    try {
      await notifApi.markRead(n.id)
      n.is_read    = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch { /* silent */ }
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

function doSearch() {
  const q = searchQ.value.trim()
  if (q) {
    router.push({ name: 'employees', query: { search: q } })
    searchQ.value = ''
  }
}

function notifIcon(type) {
  const icons = {
    payslip: 'bi-receipt-cutoff text-primary',
    leave:   'bi-calendar-check text-success',
    loan:    'bi-bank2 text-warning',
    payroll: 'bi-cash-stack text-info',
    alert:   'bi-exclamation-triangle text-danger',
    system:  'bi-bell text-secondary',
  }
  return icons[type] || 'bi-bell'
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('en-GH', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

// Close notif dropdown when clicking outside
function handleOutsideClick(e) {
  if (notifRef.value && !notifRef.value.contains(e.target)) {
    showNotifs.value = false
  }
}

function handleResize() {
  isMobile.value = window.innerWidth < 1024
  if (!isMobile.value) ui.sidebarOpen = true
}

let notifInterval = null

onMounted(() => {
  loadNotifs()
  loadPendingLeaves()
  document.addEventListener('click', handleOutsideClick)
  window.addEventListener('resize', handleResize)
  window.addEventListener('notification-updated', loadNotifs)
  notifInterval = setInterval(loadNotifs, 60_000)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('notification-updated', loadNotifs)
  clearInterval(notifInterval)
})
</script>

<style scoped>
.notif-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 11px 16px;
  border-bottom: 1px solid var(--sk-gray-100);
  cursor: pointer;
  transition: var(--transition);
  font-size: 12.5px;
}
.notif-item:hover { background: var(--sk-gray-50); }
.notif-item.unread { background: #EEF4FF; }

.page-enter-active,
.page-leave-active { transition: opacity .15s ease, transform .15s ease; }
.page-enter-from   { opacity: 0; transform: translateY(8px); }
.page-leave-to     { opacity: 0; transform: translateY(-8px); }
</style>
