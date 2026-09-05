// stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, tokenStore } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('sk_user') || 'null'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value && !!tokenStore.access)
  const isEmployee = computed(() => user.value?.role === 'employee')
  const isHR = computed(() => ['hr_manager', 'company_admin', 'super_admin'].includes(user.value?.role))
  const isPayroll = computed(() => ['payroll_officer', 'finance_manager', 'hr_manager', 'company_admin', 'super_admin'].includes(user.value?.role))
  const isAdmin = computed(() => ['company_admin', 'super_admin'].includes(user.value?.role))
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')

  async function login(email, password) {
    loading.value = true
    try {
      const data = await authApi.login(email, password)
      tokenStore.set(data.access, data.refresh)
      user.value = data.user
      localStorage.setItem('sk_user', JSON.stringify(data.user))
      return { mustChangePassword: data.must_change_password }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout(tokenStore.refresh)
    } catch {}
    tokenStore.clear()
    user.value = null
    localStorage.removeItem('sk_user')
  }

  async function fetchMe() {
    try {
      const data = await authApi.me()
      user.value = data
      localStorage.setItem('sk_user', JSON.stringify(data))
      return data
    } catch (e) {
      console.error('fetchMe failed:', e.message)
      // Only clear user if it's an auth error
      if (e.status === 401) {
        user.value = null
        localStorage.removeItem('sk_user')
      }
      return null
    }
  }

  function initials() {
    if (!user.value) return '?'
    return `${user.value.first_name?.[0] || ''}${user.value.last_name?.[0] || ''}`.toUpperCase()
  }

  return { user, loading, isAuthenticated, isEmployee, isHR, isPayroll, isAdmin, isSuperAdmin, login, logout, fetchMe, initials }
})
