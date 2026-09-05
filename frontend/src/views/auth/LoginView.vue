<template>
  <div class="login-page">
    <div class="login-left">
      <div class="login-branding">
        <div class="login-logo">S</div>
        <h1>Sikasem</h1>
        <p>Payroll Management System</p>
      </div>
      <div class="login-features">
        <div class="login-feature" v-for="f in features" :key="f.text">
          <i class="bi" :class="f.icon"></i>
          <span>{{ f.text }}</span>
        </div>
      </div>
      <div class="login-badge">
        <i class="bi bi-shield-fill-check"></i>
        Ghana GRA & SSNIT Compliant
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="login-header">
          <h2>Welcome back</h2>
          <p>Sign in to your Sikasem account</p>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="sk-form-group">
            <label class="sk-label">Email Address</label>
            <div class="sk-input-group">
              <i class="bi bi-envelope input-icon"></i>
              <input
                type="email" class="sk-input" v-model="form.email"
                placeholder="you@company.com" required autocomplete="email"
              />
            </div>
          </div>

          <div class="sk-form-group">
            <label class="sk-label">
              Password
              <a href="#" style="float:right;font-size:11px;color:var(--sk-blue-light);font-weight:400">Forgot password?</a>
            </label>
            <div class="sk-input-group">
              <i class="bi bi-lock input-icon"></i>
              <input
                :type="showPass ? 'text' : 'password'"
                class="sk-input" v-model="form.password"
                placeholder="••••••••" required autocomplete="current-password"
                style="padding-right:40px"
              />
              <button type="button" class="pass-toggle" @click="showPass = !showPass">
                <i class="bi" :class="showPass ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
          </div>

          <div v-if="error" class="login-error">
            <i class="bi bi-exclamation-triangle-fill"></i>
            {{ error }}
          </div>

          <button type="submit" class="sk-btn sk-btn-primary w-100 sk-btn-lg" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            <span>{{ loading ? 'Signing in...' : 'Sign In' }}</span>
          </button>
        </form>

        <div class="login-footer">
          <i class="bi bi-lock-fill"></i>
          Secured with 256-bit encryption
        </div>
      </div>

      <div style="text-align:center;margin-top:16px;font-size:11.5px;color:var(--sk-gray-400)">
        Sikasem by Sikaba Systems &copy; {{ new Date().getFullYear() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ email: '', password: '' })
const error = ref('')
const loading = ref(false)
const showPass = ref(false)

const features = [
  { icon: 'bi-calculator-fill', text: 'Automated PAYE & SSNIT Calculations' },
  { icon: 'bi-receipt-cutoff', text: 'Digital Payslip Generation' },
  { icon: 'bi-phone-fill', text: 'Mobile Money Disbursement' },
  { icon: 'bi-stars', text: 'AI-Powered Compliance Advisor' },
  { icon: 'bi-shield-fill-check', text: 'GRA Tax Band Compliance' },
]

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const result = await auth.login(form.value.email, form.value.password)
    if (result.mustChangePassword) {
      router.push('/change-password')
    } else {
      router.push('/')
    }
  } catch (e) {
    error.value = e.message || 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
}

.login-left {
  width: 420px;
  background: var(--sk-dark);
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  gap: 40px;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: '';
  position: absolute;
  top: -80px; right: -80px;
  width: 320px; height: 320px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(58,123,213,.25) 0%, transparent 70%);
}

.login-left::after {
  content: '';
  position: absolute;
  bottom: -60px; left: -60px;
  width: 240px; height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(245,166,35,.15) 0%, transparent 70%);
}

.login-branding {
  position: relative; z-index: 1;
}

.login-logo {
  width: 52px; height: 52px;
  background: linear-gradient(135deg, var(--sk-blue-light), var(--sk-accent));
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: white;
  margin-bottom: 20px;
}

.login-branding h1 {
  font-size: 32px; font-weight: 800; color: white;
  letter-spacing: -1px; margin: 0;
}

.login-branding p {
  font-size: 13.5px; color: var(--sk-gray-500); margin-top: 4px;
}

.login-features {
  display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

.login-feature {
  display: flex; align-items: center; gap: 12px;
  font-size: 13.5px; color: var(--sk-gray-400);
}

.login-feature i { color: var(--sk-accent); font-size: 16px; }

.login-badge {
  margin-top: auto;
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(58,123,213,.15);
  border: 1px solid rgba(58,123,213,.3);
  border-radius: 99px;
  padding: 8px 14px;
  font-size: 12px; color: var(--sk-blue-light);
  font-weight: 500;
  position: relative; z-index: 1;
}

.login-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: var(--sk-gray-50);
}

.login-card {
  background: var(--sk-white);
  border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 36px 36px 28px;
  width: 100%;
  max-width: 420px;
}

.login-header {
  margin-bottom: 28px;
}

.login-header h2 {
  font-size: 24px; font-weight: 800;
  color: var(--sk-gray-900); margin: 0;
  letter-spacing: -.4px;
}

.login-header p {
  font-size: 13.5px; color: var(--sk-gray-500); margin-top: 4px;
}

.pass-toggle {
  position: absolute; right: 11px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none; cursor: pointer;
  color: var(--sk-gray-400); padding: 4px;
}

.login-error {
  background: #FEE2E2; border: 1px solid #FECACA;
  color: var(--sk-danger);
  border-radius: var(--radius-sm);
  padding: 10px 14px; font-size: 13px;
  margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}

.login-footer {
  text-align: center; margin-top: 22px;
  font-size: 11.5px; color: var(--sk-gray-400);
  display: flex; align-items: center; justify-content: center; gap: 6px;
}

@media (max-width: 768px) {
  .login-left { display: none; }
}
</style>
