<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">My Profile</h1><div class="page-subtitle">View and update your personal information</div></div>
      <button class="sk-btn sk-btn-primary" @click="save" :disabled="saving">
        <span v-if="saving" class="spinner-border spinner-border-sm"></span>
        <i v-else class="bi bi-floppy-fill"></i> Save Changes
      </button>
    </div>

    <div class="row g-4">
      <div class="col-lg-4">
        <div class="sk-card text-center" style="padding:32px 24px">
          <div class="avatar avatar-lg mx-auto mb-3" style="width:80px;height:80px;font-size:28px">{{ initials }}</div>
          <h4 style="font-size:18px;font-weight:700;margin-bottom:4px">{{ form.first_name }} {{ form.last_name }}</h4>
          <div style="font-size:13px;color:var(--sk-gray-500)">{{ roleLabel }}</div>
          <div v-if="auth.user?.company_name" style="font-size:12.5px;color:var(--sk-gray-400);margin-top:4px">{{ auth.user.company_name }}</div>
          <div class="mt-4 d-flex flex-column gap-2">
            <router-link to="/change-password" class="sk-btn sk-btn-ghost w-100">
              <i class="bi bi-key"></i> Change Password
            </router-link>
          </div>
        </div>
      </div>

      <div class="col-lg-8">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-person-fill" style="color:var(--sk-blue-mid)"></i><h5 class="sk-card-title">Personal Information</h5></div>
          <div class="sk-card-body">
            <div class="row g-3">
              <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">First Name</label><input type="text" class="sk-input" v-model="form.first_name" /></div></div>
              <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Last Name</label><input type="text" class="sk-input" v-model="form.last_name" /></div></div>
              <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Email</label><input type="email" class="sk-input" v-model="form.email" disabled style="background:var(--sk-gray-50)" /></div></div>
              <div class="col-md-6"><div class="sk-form-group"><label class="sk-label">Phone</label><input type="tel" class="sk-input" v-model="form.phone" /></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { userApi, authApi } from '@/utils/api'

const auth = useAuthStore()
const toast = useToastStore()
const saving = ref(false)
const form = ref({ first_name: '', last_name: '', email: '', phone: '' })

const initials = computed(() => `${form.value.first_name?.[0]||''}${form.value.last_name?.[0]||''}`.toUpperCase())
const roleLabel = computed(() => {
  const map = { super_admin: 'Super Admin', company_admin: 'Company Admin', hr_manager: 'HR Manager', payroll_officer: 'Payroll Officer', finance_manager: 'Finance Manager', employee: 'Employee' }
  return map[auth.user?.role] || auth.user?.role || ''
})

async function save() {
  saving.value = true
  try {
    await userApi.update(auth.user.id, { first_name: form.value.first_name, last_name: form.value.last_name, phone: form.value.phone })
    await auth.fetchMe()
    toast.success('Profile updated')
  } catch (e) { toast.error('Update failed', e.message) } finally { saving.value = false }
}

onMounted(() => {
  if (auth.user) form.value = { ...auth.user }
})
</script>
