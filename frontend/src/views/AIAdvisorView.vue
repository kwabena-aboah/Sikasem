<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-stars me-2" style="color:var(--sk-accent)"></i>
          AI Payroll Advisor
        </h1>
        <div class="page-subtitle">Ask Ama — your Ghana payroll compliance expert</div>
      </div>
      <div class="d-flex gap-2">
        <button class="sk-btn sk-btn-ghost sk-btn-sm" @click="loadForecast">
          <i class="bi bi-graph-up-arrow"></i> Cost Forecast
        </button>
      </div>
    </div>

    <div class="row g-4">
      <!-- Chat Panel -->
      <div class="col-lg-8">
        <div class="sk-card ai-chat-card">
          <!-- AI header -->
          <div class="ai-chat-header">
            <div class="ai-avatar">
              <i class="bi bi-stars"></i>
            </div>
            <div>
              <div style="font-weight:700;font-size:15px;color:white">Ama</div>
              <div style="font-size:12px;opacity:.7">Ghana Payroll Compliance AI</div>
            </div>
            <div class="ai-status ms-auto">
              <span class="sk-badge-dot dot-active"></span>
              Online
            </div>
          </div>

          <!-- Messages -->
          <div class="ai-messages" ref="messagesEl">
            <!-- Welcome message -->
            <div class="ai-msg ai-msg-bot">
              <div class="ai-msg-bubble">
                <p style="margin:0 0 8px">👋 Hello! I'm <strong>Ama</strong>, your AI payroll compliance advisor for Ghana.</p>
                <p style="margin:0 0 8px">I can help you with:</p>
                <div class="ai-capabilities">
                  <span v-for="cap in capabilities" :key="cap" @click="askQuestion(cap)" class="ai-cap-chip">
                    {{ cap }}
                  </span>
                </div>
              </div>
            </div>

            <div v-for="msg in messages" :key="msg.id" class="ai-msg" :class="msg.role === 'user' ? 'ai-msg-user' : 'ai-msg-bot'">
              <div class="ai-msg-bubble">
                <div v-if="msg.loading" class="ai-typing">
                  <span></span><span></span><span></span>
                </div>
                <div v-else style="white-space:pre-wrap;line-height:1.65">{{ msg.content }}</div>
              </div>
              <div class="ai-msg-time">{{ msg.time }}</div>
            </div>
          </div>

          <!-- Input -->
          <div class="ai-input-area">
            <div class="ai-input-row">
              <textarea
                ref="inputEl"
                class="ai-input"
                v-model="inputText"
                placeholder="Ask about PAYE, SSNIT, overtime rules, termination pay..."
                @keydown.enter.exact.prevent="sendMessage"
                @keydown.enter.shift.exact="inputText += '\n'"
                rows="1"
              ></textarea>
              <button class="ai-send-btn" @click="sendMessage" :disabled="!inputText.trim() || sending">
                <span v-if="sending" class="spinner-border spinner-border-sm"></span>
                <i v-else class="bi bi-send-fill"></i>
              </button>
            </div>
            <div class="ai-input-hint">
              <i class="bi bi-info-circle me-1"></i>
              Press Enter to send, Shift+Enter for new line. Answers reference Ghana law and GRA regulations.
            </div>
          </div>
        </div>
      </div>

      <!-- Right panel -->
      <div class="col-lg-4">
        <!-- Quick questions -->
        <div class="sk-card mb-4">
          <div class="sk-card-header">
            <i class="bi bi-question-circle" style="color:var(--sk-accent)"></i>
            <h5 class="sk-card-title">Quick Questions</h5>
          </div>
          <div class="sk-card-body" style="padding-top:8px">
            <button
              v-for="q in quickQuestions" :key="q"
              class="quick-q-btn"
              @click="askQuestion(q)"
            >
              <i class="bi bi-chat-dots me-2" style="color:var(--sk-blue-light)"></i>
              {{ q }}
            </button>
          </div>
        </div>

        <!-- Forecast card -->
        <div class="sk-card" v-if="forecast">
          <div class="sk-card-header">
            <i class="bi bi-graph-up" style="color:var(--sk-success)"></i>
            <h5 class="sk-card-title">3-Month Forecast</h5>
          </div>
          <div class="sk-card-body">
            <div v-if="forecast.ai_narrative" class="mb-3"
              style="font-size:12.5px;color:var(--sk-gray-600);background:var(--sk-gray-50);border-radius:8px;padding:12px;line-height:1.6;border-left:3px solid var(--sk-blue-light)">
              {{ forecast.ai_narrative }}
            </div>
            <div v-for="f in forecast.forecasts" :key="f.month_offset" class="forecast-row">
              <span>Month +{{ f.month_offset }}</span>
              <span class="text-mono fw-600">GHS {{ formatAmt(f.projected_gross) }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="forecastLoading" class="sk-card">
          <div class="sk-card-body text-center p-4">
            <div class="spinner-border text-primary spinner-border-sm mb-2"></div>
            <div style="font-size:12px;color:var(--sk-gray-500)">Generating forecast...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { payrollApi } from '@/utils/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const messagesEl = ref(null)
const inputEl = ref(null)
const forecast = ref(null)
const forecastLoading = ref(false)
let msgId = 0

const capabilities = [
  'PAYE calculation',
  'SSNIT contributions',
  'Overtime rules',
  'Termination pay',
  'Leave entitlements',
  'Tax reliefs',
]

const quickQuestions = [
  'What is the current PAYE tax rate for Ghana?',
  'How is SSNIT Tier 2 calculated?',
  'What are the rules for overtime pay under the Labour Act?',
  'When is an employee entitled to gratuity?',
  'How many days of annual leave is an employee entitled to?',
  'What is the tax treatment for non-resident employees?',
  'How should maternity leave be treated in payroll?',
  'What are the SSNIT contribution rates for 2024?',
]

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  inputText.value = ''
  messages.value.push({ id: ++msgId, role: 'user', content: text, time: now() })

  const botMsg = { id: ++msgId, role: 'bot', content: '', loading: true, time: now() }
  messages.value.push(botMsg)
  await scrollDown()

  sending.value = true
  try {
    const result = await payrollApi.askCompliance(text)
    botMsg.content = result.answer
    botMsg.loading = false
  } catch (e) {
    botMsg.content = 'Sorry, I could not process your question. Please check your connection and try again.'
    botMsg.loading = false
    toast.error('AI Advisor error', e.message)
  } finally {
    sending.value = false
    await scrollDown()
  }
}

function askQuestion(q) {
  inputText.value = q
  nextTick(() => sendMessage())
}

async function loadForecast() {
  forecastLoading.value = true
  try {
    forecast.value = await payrollApi.forecast(3)
  } catch (e) {
    toast.error('Forecast failed', e.message)
  } finally {
    forecastLoading.value = false
  }
}

async function scrollDown() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function now() {
  return new Date().toLocaleTimeString('en-GH', { hour: '2-digit', minute: '2-digit' })
}

function formatAmt(v) {
  if (!v) return '0.00'
  return Number(v).toLocaleString('en-GH', { minimumFractionDigits: 2 })
}

onMounted(loadForecast)
</script>

<style scoped>
.ai-chat-card {
  display: flex; flex-direction: column;
  height: 680px; overflow: hidden;
}

.ai-chat-header {
  display: flex; align-items: center; gap: 12px;
  padding: 18px 22px;
  background: linear-gradient(135deg, var(--sk-dark), var(--sk-blue));
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.ai-avatar {
  width: 42px; height: 42px;
  background: linear-gradient(135deg, var(--sk-blue-light), var(--sk-accent));
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: white;
}

.ai-status {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: rgba(255,255,255,.7);
}

.ai-messages {
  flex: 1; overflow-y: auto;
  padding: 20px;
  display: flex; flex-direction: column; gap: 14px;
  background: var(--sk-gray-50);
}

.ai-msg { display: flex; flex-direction: column; max-width: 85%; }
.ai-msg-user { align-self: flex-end; align-items: flex-end; }
.ai-msg-bot { align-self: flex-start; }

.ai-msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 13.5px; line-height: 1.55;
}

.ai-msg-user .ai-msg-bubble {
  background: var(--sk-blue-mid);
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.ai-msg-bot .ai-msg-bubble {
  background: var(--sk-white);
  border: 1px solid var(--sk-gray-200);
  box-shadow: var(--shadow-sm);
  border-radius: 16px 16px 16px 4px;
}

.ai-msg-time {
  font-size: 10.5px; color: var(--sk-gray-400); margin-top: 4px;
}

.ai-capabilities {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
}

.ai-cap-chip {
  padding: 4px 10px;
  background: var(--sk-gray-100);
  border: 1px solid var(--sk-gray-200);
  border-radius: 99px;
  font-size: 11.5px; color: var(--sk-gray-700);
  cursor: pointer; transition: var(--transition);
}

.ai-cap-chip:hover { background: var(--sk-blue-mid); color: white; border-color: var(--sk-blue-mid); }

.ai-typing {
  display: flex; gap: 4px; align-items: center; padding: 4px 0;
}
.ai-typing span {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--sk-gray-400);
  animation: typing .8s infinite alternate;
}
.ai-typing span:nth-child(2) { animation-delay: .2s; }
.ai-typing span:nth-child(3) { animation-delay: .4s; }
@keyframes typing { to { opacity: .2; transform: translateY(-2px); } }

.ai-input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--sk-gray-200);
  background: var(--sk-white);
}

.ai-input-row { display: flex; gap: 10px; align-items: flex-end; }

.ai-input {
  flex: 1; resize: none;
  border: 1.5px solid var(--sk-gray-200); border-radius: 12px;
  padding: 10px 14px;
  font-family: var(--font-body); font-size: 13.5px;
  line-height: 1.5; outline: none;
  transition: var(--transition);
  max-height: 120px; overflow-y: auto;
}
.ai-input:focus { border-color: var(--sk-blue-light); box-shadow: 0 0 0 3px rgba(58,123,213,.1); }

.ai-send-btn {
  width: 42px; height: 42px; border-radius: 12px; flex-shrink: 0;
  background: var(--sk-blue-mid); color: white; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; transition: var(--transition);
}
.ai-send-btn:hover:not(:disabled) { background: var(--sk-blue); transform: scale(1.05); }
.ai-send-btn:disabled { opacity: .5; cursor: not-allowed; }

.ai-input-hint { font-size: 11px; color: var(--sk-gray-400); margin-top: 6px; }

.quick-q-btn {
  display: block; width: 100%; text-align: left;
  padding: 9px 12px; margin-bottom: 4px;
  background: none; border: 1px solid var(--sk-gray-200);
  border-radius: var(--radius-sm);
  font-size: 12.5px; color: var(--sk-gray-700);
  cursor: pointer; transition: var(--transition);
}
.quick-q-btn:hover { background: var(--sk-gray-50); border-color: var(--sk-blue-light); color: var(--sk-blue-mid); }

.forecast-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--sk-gray-100);
  font-size: 13px;
}
.forecast-row:last-child { border-bottom: none; }
</style>
