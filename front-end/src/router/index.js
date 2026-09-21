import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import DashboardView from '../views/DashboardView.vue'
import AcessoNegadoView from '../views/AcessoNegadoView.vue'
import { useAuthStore } from '../stores/auth'
import ConfiguracoesView from '../views/ConfiguracoesView.vue'
import SemestresView from '../views/SemestresView.vue'
import SuspensoesView from '../views/SuspensoesView.vue'

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
    {
      path: '/configuracoes',
      name: 'configuracoes',
      component: ConfiguracoesView,
      meta: { perfisPermitidos: ['SECRETARIA', 'COORDENACAO', 'ADMIN'] },
    },
    {
      path: '/semestres',
      name: 'semestres',
      component: SemestresView,
      meta: { perfisPermitidos: ['SECRETARIA', 'COORDENACAO', 'ADMIN'] },
    },
    {
      path: '/suspensoes',
      name: 'suspensoes',
      component: SuspensoesView,
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

  // ✅ ADICIONADO: Resgata a lista de perfis do usuário logado na store
  const perfisUsuario = authStore.perfis || authStore.usuario?.perfis || []

  const temPermissao = perfisUsuario.some((perfil) => perfisPermitidos.includes(perfil))
  if (!temPermissao) {
    return { name: 'acesso-negado' } // autenticado, mas sem permissão → avisa
  }

  return true
})

export default router
