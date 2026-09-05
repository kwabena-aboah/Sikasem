// stores/ui.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const sidebarOpen  = ref(window.innerWidth >= 1024)
  const pageLoading  = ref(false)

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  return { sidebarOpen, pageLoading, toggleSidebar }
})
