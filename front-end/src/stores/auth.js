import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const usuarioSalvo = localStorage.getItem('usuario')

  const usuario = ref(usuarioSalvo ? JSON.parse(usuarioSalvo) : null)
  // 1. Alterado de 'token' para 'access_token' para bater com o Layout
  const token = ref(localStorage.getItem('access_token')) 

  function login(dadosLogin) {
    token.value = dadosLogin.access_token
    usuario.value = dadosLogin.usuario
    
    // A LINHA DO CRASH FOI REMOVIDA DAQUI
    
    // 2. Padronizado para access_token
    localStorage.setItem('access_token', dadosLogin.access_token)
    localStorage.setItem('usuario', JSON.stringify(dadosLogin.usuario))
    localStorage.setItem('refresh_token', dadosLogin.refresh_token)
  }

  // 3. (Opcional, mas recomendado) Uma função para ajudar no logout
  function clear() {
    token.value = null
    usuario.value = null
  }

  return { usuario, token, login, clear }
})