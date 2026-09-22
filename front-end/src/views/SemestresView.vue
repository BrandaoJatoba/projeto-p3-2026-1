<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const codigoSemestre = ref('')
const dataInicioReal = ref('')
const dataFimReal = ref('')
const diasLetivos = ref('')
const mensagem = ref('')
const semestres = ref([])
const editandoSemestreId = ref(null)

const suspensoes = ref([])
const semestreSelecionado = ref(null)

const authStore = useAuthStore()

function selecionarSemestre(semestre) {
  semestreSelecionado.value = semestre
}

const suspensoesDoSemestreSelecionado = computed(() => {
  if (!semestreSelecionado.value) return []
  return suspensoes.value.filter((s) => s.id_semestre === semestreSelecionado.value.id_semestre)
})

const diasLetivosCalculados = computed(() => {
  if (!semestreSelecionado.value) return 0
  const diasSuspensos = suspensoesDoSemestreSelecionado.value.reduce(
    (soma, s) => soma + (s.dias_suspensos || 0),
    0,
  )
  return semestreSelecionado.value.dias_letivos - diasSuspensos
})

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
    ? `http://localhost:8000/configuracoes/semestres/${editandoSemestreId.value}`
    : 'http://localhost:8000/configuracoes/semestres'
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

onMounted(() => {
  buscarSemestres()
  buscarSuspensoes()
})
</script>

<template>
  <DefaultLayout>
    <h1>Semestres Letivos</h1>

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

      <button type="submit">
        {{ editandoSemestreId ? 'Salvar edição' : 'Cadastrar semestre' }}
      </button>
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
        <tr
          v-for="semestre in semestres"
          :key="semestre.id_semestre"
          :class="{ linhaSelecionada: semestreSelecionado?.id_semestre === semestre.id_semestre }"
          @click="selecionarSemestre(semestre)"
          style="cursor: pointer"
        >
          <td>{{ semestre.codigo_semestre }}</td>
          <td>{{ semestre.data_inicio_real }}</td>
          <td>{{ semestre.data_fim_real }}</td>
          <td>{{ semestre.dias_letivos }}</td>
          <td><button type="button" @click.stop="editarSemestre(semestre)">Editar</button></td>
        </tr>
      </tbody>
    </table>

    <div v-if="semestreSelecionado">
      <h3>Detalhes do semestre {{ semestreSelecionado.codigo_semestre }}</h3>
      <p>Dias letivos calculados (descontando suspensões): {{ diasLetivosCalculados }}</p>

      <table>
        <thead>
          <tr>
            <th>Motivo</th>
            <th>Início</th>
            <th>Fim</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="suspensao in suspensoesDoSemestreSelecionado" :key="suspensao.id_suspensao">
            <td>{{ suspensao.motivo }}</td>
            <td>{{ suspensao.data_inicio_suspensao }}</td>
            <td>{{ suspensao.data_fim_suspensao }}</td>
          </tr>
        </tbody>
      </table>
    </div>
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

.linhaSelecionada {
  background-color: #e0f0ff;
}

th,
td {
  border: 1px solid #ccc;
  padding: 8px 12px;
  text-align: left;
}
</style>
