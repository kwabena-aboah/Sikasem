<template>
  <router-view />

  <!-- Global Toast Container -->
  <div class="sk-toast-container">
    <transition-group name="toast">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="sk-toast"
        :class="`sk-toast-${toast.type}`"
      >
        <i class="sk-toast-icon" :class="toastIcon(toast.type)"></i>
        <div>
          <div class="sk-toast-title">{{ toast.title }}</div>
          <div v-if="toast.message" class="sk-toast-msg">{{ toast.message }}</div>
        </div>
        <button
          class="ms-auto sk-modal-close"
          @click="toastStore.remove(toast.id)"
        >
          <i class="bi bi-x"></i>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

function toastIcon(type) {
  const icons = {
    success: 'bi bi-check-circle-fill text-success',
    error: 'bi bi-x-circle-fill text-danger',
    warning: 'bi bi-exclamation-triangle-fill text-warning',
    info: 'bi bi-info-circle-fill text-info',
  }
  return icons[type] || 'bi bi-bell-fill'
}
</script>

<style>
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to { opacity: 0; transform: translateX(40px); }
</style>
