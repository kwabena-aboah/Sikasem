// stores/toast.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let counter  = 0

  function add(type, title, message = '', duration = 4500) {
    const id = ++counter
    toasts.value.push({ id, type, title, message })
    if (duration > 0) setTimeout(() => remove(id), duration)
    return id
  }

  function remove(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx > -1) toasts.value.splice(idx, 1)
  }

  return {
    toasts,
    success: (title, msg = '') => add('success', title, msg),
    error:   (title, msg = '') => add('error',   title, msg),
    warning: (title, msg = '') => add('warning', title, msg),
    info:    (title, msg = '') => add('info',    title, msg),
    remove,
  }
})
