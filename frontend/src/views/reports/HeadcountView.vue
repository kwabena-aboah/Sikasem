<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Headcount Report</h1><div class="page-subtitle">Workforce movement — hires and terminations</div></div>
      <select class="sk-select" v-model="year" @change="load" style="width:auto">
        <option v-for="y in [new Date().getFullYear(), new Date().getFullYear()-1]" :key="y" :value="y">{{ y }}</option>
      </select>
    </div>

    <div class="row g-4">
      <div class="col-lg-8">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-people-fill" style="color:var(--sk-blue-mid)"></i><h5 class="sk-card-title">Monthly Headcount Movement</h5></div>
          <div class="sk-card-body"><canvas ref="chartEl" style="max-height:300px"></canvas></div>
        </div>
      </div>
      <div class="col-lg-4">
        <div class="sk-card">
          <div class="sk-card-header"><i class="bi bi-bar-chart-line" style="color:var(--sk-accent)"></i><h5 class="sk-card-title">Annual Summary</h5></div>
          <div class="sk-card-body" v-if="data">
            <div class="info-row"><span class="info-label">Total Hires</span><strong class="text-success">{{ totalHires }}</strong></div>
            <div class="info-row"><span class="info-label">Total Terminations</span><strong class="text-danger">{{ totalTerminations }}</strong></div>
            <div class="info-row"><span class="info-label">Net Change</span><strong :class="netChange >= 0 ? 'text-success' : 'text-danger'">{{ netChange >= 0 ? '+' : '' }}{{ netChange }}</strong></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { reportsApi } from '@/utils/api'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const data = ref(null)
const year = ref(new Date().getFullYear())
const chartEl = ref(null)
let chart = null

const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const totalHires = computed(() => data.value?.monthly?.reduce((s, m) => s + m.hires, 0) || 0)
const totalTerminations = computed(() => data.value?.monthly?.reduce((s, m) => s + m.terminations, 0) || 0)
const netChange = computed(() => totalHires.value - totalTerminations.value)

async function load() {
  try {
    data.value = await reportsApi.headcountReport(year.value)
    await nextTick()
    renderChart()
  } catch {}
}

function renderChart() {
  if (!chartEl.value || !data.value?.monthly) return
  chart?.destroy()
  const md = data.value.monthly
  chart = new Chart(chartEl.value, {
    type: 'bar',
    data: {
      labels: md.map(m => months[m.month - 1]),
      datasets: [
        { label: 'Hires', data: md.map(m => m.hires), backgroundColor: 'rgba(30,140,90,.7)', borderRadius: 6 },
        { label: 'Terminations', data: md.map(m => m.terminations), backgroundColor: 'rgba(192,57,43,.7)', borderRadius: 6 },
      ]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } }, x: { grid: { display: false } } } }
  })
}

onMounted(load)
</script>

<style scoped>
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--sk-gray-100); font-size: 13.5px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--sk-gray-600); }
</style>
