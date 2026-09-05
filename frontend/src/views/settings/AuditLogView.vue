<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Audit Log</h1><div class="page-subtitle">Complete trail of all system actions</div></div>
    </div>
    <div class="sk-card">
      <div class="sk-card-header">
        <div class="d-flex gap-2 flex-wrap">
          <div class="sk-input-group" style="width:220px"><i class="bi bi-search input-icon"></i><input type="text" class="sk-input" v-model="search" placeholder="Search actions..." @input="loadLogs" /></div>
          <select class="sk-select" v-model="actionFilter" @change="loadLogs" style="width:auto">
            <option value="">All Actions</option>
            <option value="login">Login</option><option value="create">Create</option><option value="update">Update</option>
            <option value="delete">Delete</option><option value="payroll_run">Payroll Run</option><option value="export">Export</option>
          </select>
        </div>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead><tr><th>User</th><th>Action</th><th>Resource</th><th>IP</th><th>Time</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="5" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-for="log in logs" :key="log.id">
              <td>
                <div style="font-weight:500;font-size:13px">{{ log.user_name || '–' }}</div>
              </td>
              <td><span class="sk-badge" :class="actionBadge(log.action)">{{ log.action }}</span></td>
              <td style="font-size:12.5px">{{ log.resource_type }} <span v-if="log.resource_id" style="color:var(--sk-gray-400)">{{ log.resource_id.slice(0,8) }}...</span></td>
              <td><code style="font-size:11px">{{ log.ip_address || '–' }}</code></td>
              <td style="font-size:12px;color:var(--sk-gray-500)">{{ formatDateTime(log.timestamp) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="sk-pagination">
        <button class="sk-page-btn" :disabled="page <= 1" @click="page--; loadLogs()"><i class="bi bi-chevron-left"></i></button>
        <span style="font-size:13px;color:var(--sk-gray-500);padding:0 12px">Page {{ page }}</span>
        <button class="sk-page-btn" :disabled="logs.length < 50" @click="page++; loadLogs()"><i class="bi bi-chevron-right"></i></button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const logs = ref([])
const loading = ref(true)
const search = ref('')
const actionFilter = ref('')
const page = ref(1)

async function loadLogs() {
  loading.value = true
  try {
    const data = await userApi.auditLogs({ search: search.value || undefined, action: actionFilter.value || undefined, page: page.value })
    logs.value = data.results || data
  } catch (e) { toast.error('Failed to load logs', e.message) } finally { loading.value = false }
}

function actionBadge(a) {
  return { login: 'badge-approved', logout: 'badge-inactive', create: 'badge-active', update: 'badge-pending', delete: 'badge-rejected', payroll_run: 'badge-processing', payroll_approve: 'badge-paid', export: 'badge-review' }[a] || 'badge-inactive'
}

function formatDateTime(dt) { if (!dt) return '–'; return new Date(dt).toLocaleString('en-GH', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }

onMounted(loadLogs)
</script>
