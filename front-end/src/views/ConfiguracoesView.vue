<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const codigoSemestre = ref('')
const dataInicioReal = ref('')
const dataFimReal = ref('')
const diasLetivos = ref('')
const mensagem = ref('')
const semestres = ref([])
const editandoSemestreId = ref(null)

const idSemestreSuspensao = ref('')
const motivoSuspensao = ref('')
const dataInicioSuspensao = ref('')
const dataFimSuspensao = ref('')
const mensagemSuspensao = ref('')
const suspensoes = ref([])
const editandoSuspensaoId = ref(null)

const authStore = useAuthStore()

async function cadastrarSemestre() {
  mensagem.value = ''

  const dadosSemestre = {
    codigo_semestre: codigoSemestre.value,
    data_inicio_real: dataInicioReal.value,
    data_fim_real: dataFimReal.value,
    dias_letivos: Number(diasLetivos.value),
  }

  const editando = editandoSemestreId.value !== null
  const url = editando
    ? `http://localhost:8000/api/configuracoes/semestres/${editandoSemestreId.value}`
    : 'http://localhost:8000/api/configuracoes/semestres'
  const metodo = editando ? 'PUT' : 'POST'

  try {
    const resposta = await fetch(url, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(dadosSemestre),
    })

    if (!resposta.ok) {
      mensagem.value = 'Erro ao salvar semestre. Confira os dados.'
      return
    }

    mensagem.value = editando
      ? 'Semestre atualizado com sucesso!'
      : 'Semestre cadastrado com sucesso!'
    cancelarEdicaoSemestre()
    buscarSemestres()
  } catch (erroDeConexao) {
    mensagem.value = 'Não foi possível conectar ao servidor.'
  }
}

function editarSemestre(semestre) {
  editandoSemestreId.value = semestre.id_semestre
  codigoSemestre.value = semestre.codigo_semestre
  dataInicioReal.value = semestre.data_inicio_real
  dataFimReal.value = semestre.data_fim_real
  diasLetivos.value = semestre.dias_letivos
}

function cancelarEdicaoSemestre() {
  editandoSemestreId.value = null
  codigoSemestre.value = ''
  dataInicioReal.value = ''
  dataFimReal.value = ''
  diasLetivos.value = ''
}

async function buscarSemestres() {
  try {
    const resposta = await fetch('http://localhost:8000/api/configuracoes/semestres', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })
    const dados = await resposta.json()
    semestres.value = dados
  } catch (erro) {
    console.log('Erro ao buscar semestres')
  }
}

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
    ? `http://localhost:8000/api/configuracoes/suspensoes/${editandoSuspensaoId.value}`
    : 'http://localhost:8000/api/configuracoes/suspensoes'
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
    const resposta = await fetch('http://localhost:8000/api/configuracoes/suspensoes', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })
    const dados = await resposta.json()
    suspensoes.value = dados
  } catch (erro) {
    console.log('Erro ao buscar suspensões')
  }
}

async function deletarSuspensao(id) {
  const confirmar = confirm('Tem certeza que deseja excluir essa suspensão?')
  if (!confirmar) return

  try {
    const resposta = await fetch(`http://localhost:8000/api/configuracoes/suspensoes/${id}`, {
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
  <h1>Configurações</h1>

  <h2>Cadastrar Semestre Letivo</h2>
  <form @submit.prevent="cadastrarSemestre">
    <div>
      <label>Código do semestre (ex: 2026.1)</label>
      <input type="text" v-model="codigoSemestre" required />
    </div>

    <div>
      <label>Data de início</label>
      <input type="date" v-model="dataInicioReal" required />
    </div>

    <div>
      <label>Data de fim</label>
      <input type="date" v-model="dataFimReal" required />
    </div>

    <div>
      <label>Dias letivos</label>
      <input type="number" v-model="diasLetivos" required />
    </div>

    <button type="submit">{{ editandoSemestreId ? 'Salvar edição' : 'Cadastrar semestre' }}</button>
    <button type="button" v-if="editandoSemestreId" @click="cancelarEdicaoSemestre">
      Cancelar edição
    </button>
  </form>
  <p v-if="mensagem">{{ mensagem }}</p>
  <h2>Semestres Cadastrados</h2>
  <table>
    <thead>
      <tr>
        <th>Código</th>
        <th>Início</th>
        <th>Fim</th>
        <th>Dias letivos</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="semestre in semestres" :key="semestre.id_semestre">
        <td>{{ semestre.codigo_semestre }}</td>
        <td>{{ semestre.data_inicio_real }}</td>
        <td>{{ semestre.data_fim_real }}</td>
        <td>{{ semestre.dias_letivos }}</td>
        <td><button type="button" @click="editarSemestre(semestre)">Editar</button></td>
      </tr>
    </tbody>
  </table>

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
