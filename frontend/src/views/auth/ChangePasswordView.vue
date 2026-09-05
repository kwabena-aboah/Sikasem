<template>
  <div class="login-page">
    <div class="login-right" style="width:100%">
      <div class="login-card" style="max-width:460px">
        <div class="login-header">
          <div style="width:48px;height:48px;background:linear-gradient(135deg,var(--sk-blue-light),var(--sk-accent));border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:16px">
            <i class="bi bi-shield-lock-fill" style="color:white;font-size:22px"></i>
          </div>
          <h2>Change Password</h2>
          <p>{{ isForced ? 'You must set a new password before continuing.' : 'Update your account password.' }}</p>
        </div>

        <div v-if="isForced" class="mb-4" style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:8px;padding:12px 14px;font-size:13px;color:#92400E;display:flex;gap:10px;align-items:center">
          <i class="bi bi-exclamation-triangle-fill"></i>
          Your password was reset by an administrator. Please choose a new password.
        </div>

        <form @submit.prevent="submit">
          <div v-if="!isForced" class="sk-form-group">
            <label class="sk-label">Current Password</label>
            <div class="sk-input-group">
              <i class="bi bi-lock input-icon"></i>
              <input :type="show.old ? 'text' : 'password'" class="sk-input" v-model="form.old_password" required style="padding-right:40px" />
              <button type="button" class="pass-toggle" @click="show.old = !show.old">
                <i class="bi" :class="show.old ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
          </div>

          <div class="sk-form-group">
            <label class="sk-label">New Password</label>
            <div class="sk-input-group">
              <i class="bi bi-key input-icon"></i>
              <input :type="show.new ? 'text' : 'password'" class="sk-input" v-model="form.new_password" required minlength="8" style="padding-right:40px" />
              <button type="button" class="pass-toggle" @click="show.new = !show.new">
                <i class="bi" :class="show.new ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
            <!-- Strength indicator -->
            <div class="mt-2">
              <div class="sk-progress" style="height:4px">
                <div class="sk-progress-bar" :style="`width:${strength.pct}%;background:${strength.color}`"></div>
              </div>
              <div style="font-size:11px;margin-top:4px" :style="`color:${strength.color}`">{{ strength.label }}</div>
            </div>
          </div>

          <div class="sk-form-group">
            <label class="sk-label">Confirm New Password</label>
            <div class="sk-input-group">
              <i class="bi bi-key-fill input-icon"></i>
              <input :type="show.confirm ? 'text' : 'password'" class="sk-input" v-model="form.confirm_password" required style="padding-right:40px" :class="{ 'border-danger': form.confirm_password && form.confirm_password !== form.new_password }" />
              <button type="button" class="pass-toggle" @click="show.confirm = !show.confirm">
                <i class="bi" :class="show.confirm ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
            <div v-if="form.confirm_password && form.confirm_password !== form.new_password" style="font-size:12px;color:var(--sk-danger);margin-top:4px">
              Passwords do not match
            </div>
          </div>

          <div v-if="error" class="login-error mb-3">
            <i class="bi bi-exclamation-triangle-fill"></i>{{ error }}
          </div>

          <button type="submit" class="sk-btn sk-btn-primary w-100 sk-btn-lg" :disabled="loading || form.new_password !== form.confirm_password">
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            Update Password
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const toast = useToastStore()

const isForced = computed(() => route.query.forced === '1')
const form = ref({ old_password: '', new_password: '', confirm_password: '' })
const show = ref({ old: false, new: false, confirm: false })
const loading = ref(false)
const error = ref('')

const strength = computed(() => {
  const p = form.value.new_password
  if (!p) return { pct: 0, color: 'var(--sk-gray-300)', label: '' }
  let score = 0
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  const levels = [
    { pct: 20, color: 'var(--sk-danger)', label: 'Very weak' },
    { pct: 40, color: 'var(--sk-warning)', label: 'Weak' },
    { pct: 60, color: '#D4851A', label: 'Fair' },
    { pct: 80, color: 'var(--sk-blue-light)', label: 'Strong' },
    { pct: 100, color: 'var(--sk-success)', label: 'Very strong' },
  ]
  return levels[score - 1] || levels[0]
})

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await authApi.changePassword(form.value)
    toast.success('Password updated', 'You can now use your new password')
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; background: var(--sk-gray-50); }
.login-right { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 24px; flex: 1; }
.login-card { background: white; border: 1px solid var(--sk-gray-200); border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); padding: 36px; width: 100%; }
.login-header h2 { font-size: 22px; font-weight: 800; color: var(--sk-gray-900); margin: 0; }
.login-header p { font-size: 13.5px; color: var(--sk-gray-500); margin-top: 4px; }
.login-error { background: #FEE2E2; border: 1px solid #FECACA; color: var(--sk-danger); border-radius: 8px; padding: 10px 14px; font-size: 13px; display: flex; align-items: center; gap: 8px; }
.pass-toggle { position: absolute; right: 11px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; color: var(--sk-gray-400); padding: 4px; }
.border-danger { border-color: var(--sk-danger) !important; }
</style>
