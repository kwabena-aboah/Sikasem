import { createRouter, createWebHistory } from 'vue-router'
import { tokenStore } from '@/utils/api'

const routes = [
  // Auth
  { path: '/login', name: 'login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
  { path: '/change-password', name: 'change-password', component: () => import('@/views/auth/ChangePasswordView.vue'), meta: { public: true } },

  // App shell
  {
    path: '/',
    component: () => import('@/components/layout/AppShell.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },

      // Employees
      { path: 'employees', name: 'employees', component: () => import('@/views/employees/EmployeeListView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'employees/new', name: 'employee-new', component: () => import('@/views/employees/EmployeeFormView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'employees/:id', name: 'employee-detail', component: () => import('@/views/employees/EmployeeDetailView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'employees/:id/edit', name: 'employee-edit', component: () => import('@/views/employees/EmployeeFormView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },

      // Payroll
      { path: 'payroll', redirect: '/payroll/periods' },
      { path: 'payroll/periods', name: 'payroll-periods', component: () => import('@/views/payroll/PayrollPeriodsView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin', 'payroll_officer', 'finance_manager'] } },
      { path: 'payroll/periods/:id', name: 'payroll-period-detail', component: () => import('@/views/payroll/PayrollPeriodDetailView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin', 'payroll_officer', 'finance_manager'] } },
      { path: 'payroll/structures', name: 'salary-structures', component: () => import('@/views/payroll/SalaryStructuresView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'payroll/employee-salaries', name: 'employee-salaries', component: () => import('@/views/payroll/EmployeeSalariesView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'payroll/rules', name: 'payroll-rules', component: () => import('@/views/payroll/PayrollRulesView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },

      // Self-service payslips
      { path: 'payslips', name: 'payslips', component: () => import('@/views/payroll/PayslipsView.vue') },

      // Attendance
      { path: 'attendance', name: 'attendance', component: () => import('@/views/attendance/AttendanceView.vue') },

      // Leaves
      { path: 'leaves', name: 'leaves', component: () => import('@/views/leaves/LeavesView.vue') },
      { path: 'leaves/apply', name: 'leave-apply', component: () => import('@/views/leaves/LeaveApplyView.vue'), meta: { requiresEmployeeProfile: true } },

      // Loans
      { path: 'loans', name: 'loans', component: () => import('@/views/loans/LoansView.vue') },
      { path: 'loans/apply', name: 'loan-apply', component: () => import('@/views/loans/LoanApplyView.vue') },
      { path: 'loans/:id', name: 'loan-detail', component: () => import('@/views/loans/LoanDetailView.vue') },

      // Reports
      { path: 'reports', name: 'reports', component: () => import('@/views/reports/ReportsView.vue') },
      { path: 'reports/tax', name: 'tax-report', component: () => import('@/views/reports/TaxReportView.vue') },
      { path: 'reports/headcount', name: 'headcount-report', component: () => import('@/views/reports/HeadcountView.vue') },

      // AI
      { path: 'ai-advisor', name: 'ai-advisor', component: () => import('@/views/AIAdvisorView.vue') },

      // Settings and master data
      { path: 'settings', name: 'settings', component: () => import('@/views/settings/SettingsView.vue'), meta: { roles: ['company_admin', 'super_admin'] } },
      { path: 'settings/branches', name: 'branches', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/departments', name: 'departments', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/job-grades', name: 'job-grades', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/salary-components', name: 'salary-components', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/leave-types', name: 'leave-types', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/loan-types', name: 'loan-types', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/shifts', name: 'shifts', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/benefits', name: 'benefits', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/holidays', name: 'holidays', component: () => import('@/views/settings/MasterDataView.vue'), meta: { roles: ['hr_manager', 'company_admin', 'super_admin'] } },
      { path: 'settings/users', name: 'settings-users', component: () => import('@/views/settings/UsersView.vue'), meta: { roles: ['company_admin', 'super_admin'] } },
      { path: 'settings/audit', name: 'audit-log', component: () => import('@/views/settings/AuditLogView.vue'), meta: { roles: ['company_admin', 'super_admin'] } },

      // Self-service profile
      { path: 'profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
    ],
  },

  // 404
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to, from, next) => {
  const isPublic = to.meta.public
  const isLoggedIn = !!tokenStore.access

  if (!isPublic && !isLoggedIn) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  if (isPublic && isLoggedIn && to.name === 'login') {
    return next({ name: 'dashboard' })
  }

  if (to.meta.roles && !to.meta.roles.includes(JSON.parse(localStorage.getItem('sk_user') || '{}').role)) {
    return next({ name: 'dashboard' })
  }

  if (to.meta.requiresEmployeeProfile) {
    let user = null
    try { user = JSON.parse(localStorage.getItem('sk_user') || 'null') } catch {}
    if (!user?.employee_profile_id) {
      return next({ name: to.name === 'leave-apply' ? 'leaves' : 'loans' })
    }
  }

  next()
})

export default router
