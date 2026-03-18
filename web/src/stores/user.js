import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
  const favorites = ref([])

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value.username || '')

  function login(data) {
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('userInfo', JSON.stringify(data.user))
  }

  function logout() {
    token.value = ''
    userInfo.value = {}
    favorites.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function setFavorites(list) {
    favorites.value = list
  }

  function addFavorite(novel) {
    if (!favorites.value.find(f => f.id === novel.id)) {
      favorites.value.push(novel)
    }
  }

  function removeFavorite(novelId) {
    favorites.value = favorites.value.filter(f => f.id !== novelId)
  }

  function isFavorited(novelId) {
    return favorites.value.some(f => f.id === novelId)
  }

  return {
    token, userInfo, favorites,
    isLoggedIn, username,
    login, logout,
    setFavorites, addFavorite, removeFavorite, isFavorited
  }
})
