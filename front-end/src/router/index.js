import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import DashboardView from '../views/DashboardView.vue'
import AcessoNegadoView from '../views/AcessoNegadoView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/home', name: 'home', component: HomeView },
    { path: '/', redirect: '/home' },
    { path: '/acesso-negado', name: 'acesso-negado', component: AcessoNegadoView },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { perfisPermitidos: ['SECRETARIA', 'COORDENACAO', 'ADMIN'] },
    },
  ],
})

router.beforeEach((to, from) => {
  const authStore = useAuthStore()
  const perfisPermitidos = to.meta.perfisPermitidos

  if (!perfisPermitidos) {
    return true
  }

  if (!authStore.token) {
    return { name: 'login' } // não autenticado → vai logar
  }
  const temPermissao = perfisUsuario.some(perfil => perfisPermitidos.includes(perfil))
  if (!temPermissao) {
    return { name: 'acesso-negado' } // autenticado, mas sem permissão → avisa
  }

  return true
})

export default router
