<template>
  <div>
    <div class="page-header">
      <div><h1 class="page-title">Tax Report</h1><div class="page-subtitle">Monthly PAYE and SSNIT compliance summary</div></div>
      <div class="d-flex gap-2">
        <select class="sk-select" v-model="year" @change="load" style="width:auto">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="printReport">
          <i class="bi bi-printer"></i> Print
        </button>
      </div>
    </div>

    <!-- Annual summary cards -->
    <div v-if="data" class="row g-3 mb-4">
      <div class="col-sm-6 col-lg-3" v-for="item in annualCards" :key="item.label">
        <div class="kpi-card">
          <div class="kpi-card-accent" :style="`background:${item.color}`"></div>
          <div class="kpi-value" style="font-size:20px">GHS {{ fmtAmt(item.value) }}</div>
          <div class="kpi-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- Monthly breakdown table -->
    <div v-if="loading" class="text-center p-5">
      <div class="spinner-border text-primary"></div>
      <div style="font-size:13px;color:var(--sk-gray-500);margin-top:10px">Loading tax report…</div>
    </div>

    <div v-else-if="!data" class="sk-card empty-state" style="padding:60px">
      <i class="bi bi-receipt"></i>
      <h5>No tax report data</h5>
      <p>There is no tax data available for the selected year.</p>
    </div>

    <div v-else class="sk-card">
      <div class="sk-card-header">
        <i class="bi bi-table" style="color:var(--sk-blue-mid)"></i>
        <h5 class="sk-card-title">Monthly Tax Summary — {{ year }}</h5>
      </div>
      <div class="sk-table-wrapper">
        <table class="sk-table" id="tax-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Employees</th>
              <th>Gross Pay</th>
              <th>PAYE (Employee)</th>
              <th>SSNIT Employee (5.5%)</th>
              <th>SSNIT Employer (10.5%)</th>
              <th>Tier 2 (2.5%)</th>
              <th>Total Tax Due</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="text-center p-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>
            <tr v-else-if="!data?.monthly?.length"><td colspan="8"><div class="empty-state"><i class="bi bi-receipt"></i><h5>No data for {{ year }}</h5></div></td></tr>
            <tr v-for="m in data.monthly" :key="m.month">
              <td style="font-weight:600">{{ monthName(m.month) }}</td>
              <td>{{ m.count }}</td>
              <td class="text-mono">{{ fmtAmt(m.gross) }}</td>
              <td class="text-mono text-danger fw-600">{{ fmtAmt(m.paye) }}</td>
              <td class="text-mono text-warning">{{ fmtAmt(m.ssnit_emp) }}</td>
              <td class="text-mono text-primary">{{ fmtAmt(m.ssnit_empr) }}</td>
              <td class="text-mono" style="color:#7C3AED">{{ fmtAmt(m.tier2) }}</td>
              <td class="text-mono fw-600">{{ fmtAmt(m.paye + m.ssnit_emp + m.ssnit_empr + m.tier2) }}</td>
            </tr>
            <!-- Totals row -->
            <tr v-if="data?.monthly?.length" style="background:var(--sk-gray-50);font-weight:700">
              <td>ANNUAL TOTAL</td>
              <td>–</td>
              <td class="text-mono">{{ fmtAmt(data.annual_totals?.total_gross) }}</td>
              <td class="text-mono text-danger">{{ fmtAmt(data.annual_totals?.paye) }}</td>
              <td class="text-mono text-warning">{{ fmtAmt(data.annual_totals?.ssnit_employee) }}</td>
              <td class="text-mono text-primary">{{ fmtAmt(data.annual_totals?.ssnit_employer) }}</td>
              <td class="text-mono" style="color:#7C3AED">{{ fmtAmt(data.annual_totals?.tier2_employer) }}</td>
              <td class="text-mono" style="font-size:15px">{{ fmtAmt((data.annual_totals?.paye || 0) + (data.annual_totals?.ssnit_employee || 0) + (data.annual_totals?.ssnit_employer || 0) + (data.annual_totals?.tier2_employer || 0)) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- GRA Filing note -->
    <div class="mt-4 p-4" style="background:#FFF8E1;border:1px solid #FFE082;border-radius:12px;font-size:13px;color:#795548">
      <div style="font-weight:700;margin-bottom:6px;display:flex;align-items:center;gap:8px">
        <i class="bi bi-info-circle-fill" style="color:#F57F17"></i>
        GRA Filing Reminder
      </div>
      PAYE must be remitted to the Ghana Revenue Authority by the <strong>15th of the following month</strong>.
      SSNIT contributions must be paid by the <strong>14th of the following month</strong> via SSNIT's online portal.
      Failure to remit attracts a penalty of <strong>3 times the amount plus interest</strong> (Income Tax Act 2015, Section 113).
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { reportsApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const data = ref(null)
const loading = ref(true)
const year = ref(new Date().getFullYear())
const years = computed(() => { const c = year.value; return [c, c-1, c-2] })
const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

const annualCards = computed(() => {
  if (!data.value?.annual_totals) return []
  const t = data.value.annual_totals
  return [
    { label: 'Total PAYE', value: t.paye, color: 'var(--sk-danger)' },
    { label: 'Total SSNIT (Emp)', value: t.ssnit_employee, color: 'var(--sk-warning)' },
    { label: 'Total SSNIT (Empr)', value: t.ssnit_employer, color: 'var(--sk-blue-mid)' },
    { label: 'Total Payroll', value: t.total_gross, color: 'var(--sk-success)' },
  ]
})

async function load() {
  loading.value = true
  try { data.value = await reportsApi.taxReport(year.value) }
  catch (e) { toast.error('Failed to load tax report', e.message) }
  finally { loading.value = false }
}

function monthName(n) { return months[(n - 1)] || n }
function fmtAmt(v) { if (!v && v !== 0) return '0.00'; return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 }) }
function printReport() { window.print() }

onMounted(load)
</script>
