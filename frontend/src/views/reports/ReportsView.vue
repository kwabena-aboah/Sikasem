<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Reports & Analytics</h1><div class="page-subtitle">Payroll, compliance, and workforce reports</div></div>
      <div class="d-flex gap-2">
        <select class="sk-select" v-model="selectedYear" @change="loadAll" style="width:auto">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <!-- Report nav cards -->
    <div class="row g-3 mb-4">
      <div v-for="r in reportCards" :key="r.name" class="col-sm-6 col-lg-3">
        <router-link :to="r.route" class="report-nav-card">
          <div class="report-nav-icon" :style="`background:${r.bg};color:${r.color}`"><i class="bi" :class="r.icon"></i></div>
          <div style="font-weight:600;font-size:13.5px;color:var(--sk-gray-900)">{{ r.name }}</div>
          <div style="font-size:12px;color:var(--sk-gray-500);margin-top:2px">{{ r.desc }}</div>
        </router-link>
      </div>
    </div>

    <div class="row g-4">
      <!-- Payroll cost chart -->
      <div class="col-lg-8">
        <div class="sk-card">
          <div class="sk-card-header">
            <i class="bi bi-bar-chart-line-fill" style="color:var(--sk-blue-mid)"></i>
            <h5 class="sk-card-title">Monthly Payroll Cost — {{ selectedYear }}</h5>
            <button class="sk-btn sk-btn-ghost sk-btn-sm ms-auto" @click="exportPayrollCsv">
              <i class="bi bi-download"></i> Export
            </button>
          </div>
          <div class="sk-card-body"><canvas ref="payrollChart" style="max-height:280px"></canvas></div>
        </div>
      </div>

      <!-- Tax summary -->
      <div class="col-lg-4">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-receipt" style="color:var(--sk-warning)"></i><h5 class="sk-card-title">Tax Summary {{ selectedYear }}</h5></div>
          <div class="sk-card-body" style="padding-top:4px">
            <div v-if="taxData">
              <div v-for="item in taxSummaryItems" :key="item.label" class="tax-row">
                <span>{{ item.label }}</span>
                <span class="text-mono fw-600" :style="`color:${item.color}`">GHS {{ formatAmt(item.value) }}</span>
              </div>
            </div>
            <div v-else class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></div>
          </div>
        </div>
      </div>

      <!-- Leave utilisation -->
      <div class="col-lg-6">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-calendar-check" style="color:var(--sk-success)"></i><h5 class="sk-card-title">Leave Utilisation {{ selectedYear }}</h5></div>
          <div class="sk-card-body"><canvas ref="leaveChart" style="max-height:220px"></canvas></div>
        </div>
      </div>

      <!-- Headcount -->
      <div class="col-lg-6">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-people-fill" style="color:var(--sk-accent)"></i><h5 class="sk-card-title">Headcount Movement {{ selectedYear }}</h5></div>
          <div class="sk-card-body"><canvas ref="headcountChart" style="max-height:220px"></canvas></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { reportsApi, payrollApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const toast = useToastStore()
const selectedYear = ref(new Date().getFullYear())
const years = computed(() => { const c = new Date().getFullYear(); return [c, c-1, c-2] })
const taxData = ref(null)
const leaveData = ref(null)
const headcountData = ref(null)
const payrollChart = ref(null)
const leaveChart = ref(null)
const headcountChart = ref(null)
let charts = {}

const reportCards = [
  { name: 'Tax Report', desc: 'PAYE & SSNIT compliance', icon: 'bi-receipt', color: 'var(--sk-warning)', bg: '#FEF3C7', route: '/reports/tax' },
  { name: 'Headcount', desc: 'Hires & terminations', icon: 'bi-people-fill', color: 'var(--sk-blue-mid)', bg: '#EEF4FF', route: '/reports/headcount' },
  { name: 'Leave Report', desc: 'Leave utilisation', icon: 'bi-calendar-check', color: 'var(--sk-success)', bg: '#D1FAE5', route: '/reports' },
  { name: 'Payroll Export', desc: 'Download CSV/Excel', icon: 'bi-file-earmark-spreadsheet', color: '#7C3AED', bg: '#EDE9FE', route: '/payroll/periods' },
]

const taxSummaryItems = computed(() => {
  if (!taxData.value) return []
  const t = taxData.value.annual_totals
  return [
    { label: 'Total PAYE', value: t.paye, color: 'var(--sk-danger)' },
    { label: 'SSNIT Employee', value: t.ssnit_employee, color: 'var(--sk-warning)' },
    { label: 'SSNIT Employer', value: t.ssnit_employer, color: 'var(--sk-blue-mid)' },
    { label: 'Tier 2 Employer', value: t.tier2_employer, color: 'var(--sk-blue-light)' },
    { label: 'Total Payroll', value: t.total_gross, color: 'var(--sk-success)' },
  ]
})

async function loadAll() {
  const [tx, lv, hc] = await Promise.all([
    reportsApi.taxReport(selectedYear.value).catch(() => null),
    reportsApi.leaveReport(selectedYear.value).catch(() => null),
    reportsApi.headcountReport(selectedYear.value).catch(() => null),
  ])
  taxData.value = tx
  leaveData.value = lv
  headcountData.value = hc
  await nextTick()
  renderCharts()
}

function renderCharts() {
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

  // Payroll trend
  if (payrollChart.value && taxData.value?.monthly) {
    charts.payroll?.destroy()
    const md = taxData.value.monthly
    charts.payroll = new Chart(payrollChart.value, {
      type: 'bar',
      data: {
        labels: md.map(m => months[m.month - 1]),
        datasets: [
          { label: 'Gross Pay', data: md.map(m => m.gross), backgroundColor: 'rgba(58,123,213,.7)', borderRadius: 5 },
          { label: 'PAYE', data: md.map(m => m.paye), backgroundColor: 'rgba(192,57,43,.6)', borderRadius: 5 },
          { label: 'SSNIT', data: md.map(m => m.ssnit_emp + m.ssnit_empr), backgroundColor: 'rgba(245,166,35,.6)', borderRadius: 5 },
        ]
      },
      options: { responsive: true, scales: { y: { ticks: { callback: v => `GHS ${(v/1000).toFixed(0)}k` } }, x: { grid: { display: false } } } }
    })
  }

  // Leave chart
  if (leaveChart.value && leaveData.value?.by_leave_type) {
    charts.leave?.destroy()
    const ld = leaveData.value.by_leave_type
    charts.leave = new Chart(leaveChart.value, {
      type: 'bar',
      data: {
        labels: ld.map(l => l.leave_type__name),
        datasets: [{ label: 'Days Taken', data: ld.map(l => l.total_days), backgroundColor: ['#3A7BD5','#1E8C5A','#F5A623','#7C3AED','#E74C3C'], borderRadius: 6 }]
      },
      options: { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } } } }
    })
  }

  // Headcount chart
  if (headcountChart.value && headcountData.value?.monthly) {
    charts.headcount?.destroy()
    const hd = headcountData.value.monthly
    charts.headcount = new Chart(headcountChart.value, {
      type: 'line',
      data: {
        labels: hd.map(m => months[m.month - 1]),
        datasets: [
          { label: 'Hires', data: hd.map(m => m.hires), borderColor: 'var(--sk-success)', backgroundColor: 'rgba(30,140,90,.1)', fill: true, tension: 0.3, pointRadius: 4 },
          { label: 'Terminations', data: hd.map(m => m.terminations), borderColor: 'var(--sk-danger)', backgroundColor: 'rgba(192,57,43,.1)', fill: true, tension: 0.3, pointRadius: 4 },
        ]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true }, x: { grid: { display: false } } } }
    })
  }
}

async function exportPayrollCsv() {
  toast.info('Export', 'Please select a specific payroll period to export')
}

function formatAmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }

onMounted(loadAll)
</script>

<style scoped>
.report-nav-card { display: flex; flex-direction: column; gap: 8px; padding: 18px 20px; background: white; border: 1.5px solid var(--sk-gray-200); border-radius: var(--radius-lg); text-decoration: none; transition: var(--transition); }
.report-nav-card:hover { border-color: var(--sk-blue-light); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.report-nav-icon { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; font-size: 18px; }
.tax-row { display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--sk-gray-100); font-size: 13px; }
.tax-row:last-child { border-bottom: none; }
</style>
