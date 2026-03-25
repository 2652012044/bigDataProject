import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const searchKeyword = ref('')
  const sideMenuCollapsed = ref(false)

  function setSearchKeyword(keyword) {
    searchKeyword.value = keyword
  }

  function toggleSideMenu() {
    sideMenuCollapsed.value = !sideMenuCollapsed.value
  }

  return {
    searchKeyword,
    sideMenuCollapsed,
    setSearchKeyword,
    toggleSideMenu
  }
})
