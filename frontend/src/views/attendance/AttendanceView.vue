<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Attendance</h1><div class="page-subtitle">Track and manage employee attendance records</div></div>
      <div class="d-flex gap-2">
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="showImportModal = true" v-if="auth.isHR">
          <i class="bi bi-upload"></i> Import
        </button>
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="loadSummary">
          <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
      </div>
    </div>

    <!-- Month/Year picker -->
    <div class="d-flex align-items-center gap-3 mb-4">
      <button class="sk-btn sk-btn-ghost sk-btn-icon" @click="prevMonth"><i class="bi bi-chevron-left"></i></button>
      <h4 style="margin:0;font-weight:700;font-size:18px;min-width:160px;text-align:center">{{ monthLabel }}</h4>
      <button class="sk-btn sk-btn-ghost sk-btn-icon" @click="nextMonth" :disabled="isCurrentMonth"><i class="bi bi-chevron-right"></i></button>
    </div>

    <!-- Summary stats -->
    <div class="row g-3 mb-4">
      <div class="col-sm-6 col-lg-3" v-for="s in summaryStats" :key="s.label">
        <div class="kpi-card" style="padding:14px 18px">
          <div class="kpi-card-accent" :style="`background:${s.color}`"></div>
          <div style="font-size:22px;font-weight:700">{{ s.value }}</div>
          <div style="font-size:11.5px;color:var(--sk-gray-500);margin-top:2px">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="sk-card">
      <div class="sk-card-header">
        <i class="bi bi-calendar3-week-fill" style="color:var(--sk-blue-mid)"></i>
        <h5 class="sk-card-title">{{ auth.isEmployee ? 'My Attendance Record' : 'Monthly Summary' }}</h5>
        <div class="ms-auto d-flex gap-2" v-if="!auth.isEmployee">
          <div class="sk-input-group" style="width:220px">
            <i class="bi bi-search input-icon"></i>
            <input type="text" class="sk-input" v-model="search" placeholder="Search employee..." />
          </div>
        </div>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table">
          <thead>
            <tr>
              <th>{{ auth.isEmployee ? 'My Details' : 'Employee' }}</th>
              <th>Present</th>
              <th>Absent</th>
              <th>Late</th>
              <th>Leave</th>
              <th>OT Hours</th>
              <th>Attendance %</th>
              <th v-if="auth.isHR">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-else-if="!filteredSummary.length"><td colspan="8"><div class="empty-state"><i class="bi bi-calendar3"></i><h5>No attendance data</h5></div></td></tr>
            <tr v-for="row in filteredSummary" :key="row.employee__id">
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="avatar avatar-sm">{{ initials(row) }}</div>
                  <span style="font-weight:500">{{ row.employee__first_name }} {{ row.employee__last_name }}</span>
                </div>
              </td>
              <td><span class="fw-600 text-success">{{ row.present || 0 }}</span></td>
              <td><span class="fw-600 text-danger">{{ row.absent || 0 }}</span></td>
              <td><span class="fw-600 text-warning">{{ row.late || 0 }}</span></td>
              <td>{{ row.leave || 0 }}</td>
              <td class="text-mono">{{ (row.overtime_total || 0).toFixed(1) }}h</td>
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div style="flex:1">
                    <div class="sk-progress">
                      <div class="sk-progress-bar" :style="`width:${attPct(row)}%;background:${attColor(attPct(row))}`"></div>
                    </div>
                  </div>
                  <span style="font-size:12px;font-weight:600;min-width:36px">{{ attPct(row) }}%</span>
                </div>
              </td>
              <td v-if="auth.isHR">
                <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="viewEmployee(row)">
                  <i class="bi bi-eye"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Import Modal -->
    <div v-if="showImportModal" class="sk-modal-backdrop" @click.self="showImportModal = false">
      <div class="sk-modal sk-modal-md">
        <div class="sk-modal-header">
          <h5 class="sk-modal-title">Import Attendance Data</h5>
          <button class="sk-modal-close" @click="showImportModal = false"><i class="bi bi-x"></i></button>
        </div>
        <div class="sk-modal-body">
          <div class="d-flex align-items-start justify-content-between gap-3 mb-3">
            <p class="mb-0" style="font-size:13.5px;color:var(--sk-gray-600)">Upload a CSV file with columns: <code>employee_id, date, status, clock_in, clock_out</code></p>
            <button class="sk-btn sk-btn-ghost sk-btn-sm text-nowrap" type="button" @click="downloadTemplate">
              <i class="bi bi-download"></i> Download template
            </button>
          </div>
          <div class="sk-form-group">
            <label class="sk-label">CSV File</label>
            <input type="file" class="sk-input" accept=".csv" style="padding:6px 10px" @change="handleFile" />
          </div>
          <div v-if="importPreview.length" class="mt-3">
            <div style="font-size:12.5px;color:var(--sk-gray-600);margin-bottom:8px">Preview (first 5 rows):</div>
            <div style="font-family:var(--font-mono);font-size:11px;background:var(--sk-gray-50);padding:10px;border-radius:8px;overflow-x:auto">
              <div v-for="row in importPreview" :key="row.join('')">{{ row.join(' | ') }}</div>
            </div>
          </div>
        </div>
        <div class="sk-modal-footer">
          <button class="sk-btn sk-btn-ghost" @click="showImportModal = false">Cancel</button>
          <button class="sk-btn sk-btn-primary" @click="doImport" :disabled="importing">
            <span v-if="importing" class="spinner-border spinner-border-sm"></span>
            Import Records
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { attendanceApi } from '@/utils/api'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()
const summary = ref([])
const loading = ref(true)
const search = ref('')
const showImportModal = ref(false)
const importing = ref(false)
const importPreview = ref([])
const importFile = ref(null)

const today = new Date()
const currentMonth = ref(today.getMonth() + 1)
const currentYear = ref(today.getFullYear())

const isCurrentMonth = computed(() => currentMonth.value === today.getMonth() + 1 && currentYear.value === today.getFullYear())
const monthLabel = computed(() => new Date(currentYear.value, currentMonth.value - 1, 1).toLocaleDateString('en-GH', { month: 'long', year: 'numeric' }))

const filteredSummary = computed(() => {
  if (!search.value) return summary.value
  const q = search.value.toLowerCase()
  return summary.value.filter(r => `${r.employee__first_name} ${r.employee__last_name}`.toLowerCase().includes(q))
})

const summaryStats = computed(() => {
  const total = filteredSummary.value.reduce((s, r) => ({ present: s.present + (r.present || 0), absent: s.absent + (r.absent || 0), late: s.late + (r.late || 0), ot: s.ot + (r.overtime_total || 0) }), { present: 0, absent: 0, late: 0, ot: 0 })
  return [
    { label: 'Total Present Days', value: total.present, color: 'var(--sk-success)' },
    { label: 'Total Absent Days', value: total.absent, color: 'var(--sk-danger)' },
    { label: 'Late Arrivals', value: total.late, color: 'var(--sk-warning)' },
    { label: 'Total OT Hours', value: total.ot.toFixed(1) + 'h', color: 'var(--sk-blue-mid)' },
  ]
})

function prevMonth() {
  if (currentMonth.value === 1) { currentMonth.value = 12; currentYear.value-- }
  else currentMonth.value--
  loadSummary()
}

function nextMonth() {
  if (isCurrentMonth.value) return
  if (currentMonth.value === 12) { currentMonth.value = 1; currentYear.value++ }
  else currentMonth.value++
  loadSummary()
}

async function loadSummary() {
  loading.value = true
  try {
    const data = await attendanceApi.monthlySummary({ month: currentMonth.value, year: currentYear.value })
    summary.value = data.results || data
  } catch (e) { toast.error('Failed to load attendance', e.message) } finally { loading.value = false }
}

function attPct(row) {
  const total = (row.present || 0) + (row.absent || 0) + (row.late || 0)
  if (!total) return 0
  return Math.round(((row.present || 0) / total) * 100)
}

function attColor(pct) {
  if (pct >= 90) return 'var(--sk-success)'
  if (pct >= 75) return 'var(--sk-warning)'
  return 'var(--sk-danger)'
}

function initials(row) { return `${row.employee__first_name?.[0] || ''}${row.employee__last_name?.[0] || ''}`.toUpperCase() }
function viewEmployee(row) { router.push(`/employees/${row.employee__id}`) }

function downloadTemplate() {
  const headers = 'employee_id,date,status,clock_in,clock_out'
  const csv = `${headers}\n`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'attendance_import_template.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function handleFile(e) {
  importFile.value = e.target.files[0]
  const reader = new FileReader()
  reader.onload = ev => {
    const lines = ev.target.result.split('\n').slice(0, 6)
    importPreview.value = lines.map(l => l.split(','))
  }
  reader.readAsText(importFile.value)
}

async function doImport() {
  if (!importFile.value) {
    toast.warning('No file', 'Please select a CSV file to import')
    return
  }
  importing.value = true
  try {
    const text = await importFile.value.text()
    const rawLines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
    if (rawLines.length <= 1) {
      throw new Error('CSV file contains no data rows')
    }

    const headers = rawLines[0].split(',').map(h => h.trim().toLowerCase().replace(/['"]/g, ''))
    const records = []

    for (let i = 1; i < rawLines.length; i++) {
      const cols = rawLines[i].split(',').map(c => c.trim().replace(/['"]/g, ''))
      if (!cols.length || (cols.length === 1 && !cols[0])) continue
      const row = {}
      headers.forEach((h, idx) => {
        row[h] = cols[idx] !== undefined ? cols[idx] : ''
      })
      if (row.employee_id && row.date) {
        records.push(row)
      }
    }

    if (!records.length) {
      throw new Error('No valid attendance rows found. Please check columns: employee_id, date, status, clock_in, clock_out')
    }

    const res = await attendanceApi.bulkImport(records)
    if (res.errors && res.errors.length) {
      toast.warning('Partial import', `Imported ${res.imported || 0} records with ${res.errors.length} errors`)
    } else {
      toast.success('Import complete', `Successfully imported ${res.imported || 0} attendance records`)
    }
    showImportModal.value = false
    importFile.value = null
    importPreview.value = []
    await loadSummary()
  } catch (e) {
    toast.error('Import failed', e.message)
  } finally {
    importing.value = false
  }
}

onMounted(loadSummary)
</script>
