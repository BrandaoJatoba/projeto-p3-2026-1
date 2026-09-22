<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const idSemestreSuspensao = ref('')
const motivoSuspensao = ref('')
const dataInicioSuspensao = ref('')
const dataFimSuspensao = ref('')
const mensagemSuspensao = ref('')
const suspensoes = ref([])
const editandoSuspensaoId = ref(null)

const semestres = ref([])

const authStore = useAuthStore()

async function cadastrarSuspensao() {
  mensagemSuspensao.value = ''

  const dadosSuspensao = {
    id_semestre: idSemestreSuspensao.value,
    motivo: motivoSuspensao.value,
    data_inicio_suspensao: dataInicioSuspensao.value,
    data_fim_suspensao: dataFimSuspensao.value || null,
  }

  const editando = editandoSuspensaoId.value !== null
  const url = editando
    ? `http://localhost:8000/configuracoes/suspensoes/${editandoSuspensaoId.value}`
    : 'http://localhost:8000/configuracoes/suspensoes'
  const metodo = editando ? 'PUT' : 'POST'

  try {
    const resposta = await fetch(url, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(dadosSuspensao),
    })

    if (!resposta.ok) {
      mensagemSuspensao.value = 'Erro ao salvar suspensão. Confira os dados.'
      return
    }

    mensagemSuspensao.value = editando
      ? 'Suspensão atualizada com sucesso!'
      : 'Suspensão cadastrada com sucesso!'
    cancelarEdicaoSuspensao()
    buscarSuspensoes()
  } catch (erroDeConexao) {
    mensagemSuspensao.value = 'Não foi possível conectar ao servidor.'
  }
}

function editarSuspensao(suspensao) {
  editandoSuspensaoId.value = suspensao.id_suspensao
  idSemestreSuspensao.value = suspensao.id_semestre
  motivoSuspensao.value = suspensao.motivo
  dataInicioSuspensao.value = suspensao.data_inicio_suspensao
  dataFimSuspensao.value = suspensao.data_fim_suspensao
}

function cancelarEdicaoSuspensao() {
  editandoSuspensaoId.value = null
  idSemestreSuspensao.value = ''
  motivoSuspensao.value = ''
  dataInicioSuspensao.value = ''
  dataFimSuspensao.value = ''
}

async function buscarSuspensoes() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/suspensoes', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      console.log('Rota de suspensões ainda não existe ou deu erro')
      return
    }

    const dados = await resposta.json()
    suspensoes.value = dados
  } catch (erro) {
    console.log('Erro ao buscar suspensões')
  }
}

async function buscarSemestres() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/semestres', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      console.log('Rota de semestres ainda não existe ou deu erro')
      return
    }

    const dados = await resposta.json()
    semestres.value = dados
  } catch (erro) {
    console.log('Erro ao buscar semestres')
  }
}

async function deletarSuspensao(id) {
  const confirmar = confirm('Tem certeza que deseja excluir essa suspensão?')
  if (!confirmar) return

  try {
    const resposta = await fetch(`http://localhost:8000/configuracoes/suspensoes/${id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      mensagemSuspensao.value = 'Erro ao excluir suspensão.'
      return
    }

    buscarSuspensoes()
  } catch (erro) {
    mensagemSuspensao.value = 'Não foi possível conectar ao servidor.'
  }
}

onMounted(() => {
  buscarSemestres()
  buscarSuspensoes()
})
</script>

<template>
  <DefaultLayout>
    <h1>Suspensões de Calendário</h1>

    <h2>Cadastrar Suspensão de Calendário</h2>
    <form @submit.prevent="cadastrarSuspensao">
      <div>
        <label>Semestre</label>
        <select v-model="idSemestreSuspensao" required>
          <option value="" disabled>Selecione um semestre</option>
          <option
            v-for="semestre in semestres"
            :key="semestre.id_semestre"
            :value="semestre.id_semestre"
          >
            {{ semestre.codigo_semestre }}
          </option>
        </select>
      </div>

      <div>
        <label>Motivo (ex: Greve Docente)</label>
        <input type="text" v-model="motivoSuspensao" required />
      </div>

      <div>
        <label>Data de início</label>
        <input type="date" v-model="dataInicioSuspensao" required />
      </div>

      <div>
        <label>Data de fim (deixe em branco se ainda não terminou)</label>
        <input type="date" v-model="dataFimSuspensao" />
      </div>

      <button type="submit">
        {{ editandoSuspensaoId ? 'Salvar edição' : 'Cadastrar suspensão' }}
      </button>
      <button type="button" v-if="editandoSuspensaoId" @click="cancelarEdicaoSuspensao">
        Cancelar edição
      </button>
    </form>
    <p v-if="mensagemSuspensao">{{ mensagemSuspensao }}</p>

    <h2>Suspensões Cadastradas</h2>
    <table>
      <thead>
        <tr>
          <th>Semestre</th>
          <th>Motivo</th>
          <th>Início</th>
          <th>Fim</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="suspensao in suspensoes" :key="suspensao.id_suspensao">
          <td>{{ suspensao.id_semestre }}</td>
          <td>{{ suspensao.motivo }}</td>
          <td>{{ suspensao.data_inicio_suspensao }}</td>
          <td>{{ suspensao.data_fim_suspensao }}</td>
          <td>
            <button type="button" @click="editarSuspensao(suspensao)">Editar</button>
            <button type="button" @click="deletarSuspensao(suspensao.id_suspensao)">Excluir</button>
          </td>
        </tr>
      </tbody>
    </table>
  </DefaultLayout>
</template>

<style scoped>
div {
  margin-bottom: 12px;
}

table {
  border-collapse: collapse;
  margin-top: 12px;
}

th,
td {
  border: 1px solid #ccc;
  padding: 8px 12px;
  text-align: left;
}
</style>
