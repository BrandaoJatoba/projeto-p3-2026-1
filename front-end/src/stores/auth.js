import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const usuarioSalvo = localStorage.getItem('usuario')

  const usuario = ref(usuarioSalvo ? JSON.parse(usuarioSalvo) : null)
  const token = ref(localStorage.getItem('token'))

  function login(dadosLogin) {
    token.value = dadosLogin.access_token
    usuario.value = dadosLogin.usuario
    localStorage.setItem('token', dadosLogin.access_token)
    localStorage.setItem('usuario', JSON.stringify(dadosLogin.usuario))
  }

  return { usuario, token, login }
})
