import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const usuario = ref(null)
  const token = ref(localStorage.getItem('token'))

  function login(dadosLogin) {
    token.value = dadosLogin.access_token
    usuario.value = dadosLogin.usuario
    localStorage.setItem('token', dadosLogin.access_token)
  }

  return { usuario, token, login }
})
