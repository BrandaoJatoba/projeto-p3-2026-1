# Sistema de Acompanhamento Acadêmico — PPGI
Repositório oficial do projeto desenvolvido para a disciplina de Programação 3 (P3) do Instituto de Computação.

# 👥 Integrantes do Grupo
João Jatobá

Elis Siqueira

Gabriella Salvadora

# 📚 Sobre a Disciplina
A disciplina de Programação 3 tem como objetivo apresentar os conceitos introdutórios do funcionamento da web e da programação/desenvolvimento de sistemas para a web, abrangendo tanto o ecossistema front-end quanto o back-end (client-side e server-side).

# 🎯 Contexto do Projeto
Cliente: Secretaria do Programa de Pós-Graduação em Informática (PPGI).

Problema Identificado: O acompanhamento dos estudantes matriculados na pós-graduação, incluindo o controle de prazos limite e requisitos pendentes necessários para a diplomação e formação.

Fase Atual: Levantamento de requisitos (após a realização da entrevista inicial com o cliente).

# 📋 Primeiros Passos (Checklist Inicial)
Atualmente, o projeto encontra-se na fase inicial, com o repositório configurado e a entrevista inicial concluída. Os próximos passos planejados são:

[x] Consolidar o Documento de Requisitos: Redigir a especificação detalhada com base na entrevista inicial com a secretaria do PPGI.

[x] Definir Requisitos Funcionais e Não Funcionais: Mapear o que o sistema deve fazer (ex: cadastro de alunos, painel de prazos) e suas restrições.

[x] Escolha da Stack Tecnológica: Selecionar as tecnologias de front-end, back-end e banco de dados que serão utilizadas ao longo da disciplina.

[ ] Elaborar Protótipos de Tela (Wireframes): Desenhar esboços iniciais da interface para validação do fluxo de uso com a secretaria.

[ ] Estruturação Inicial do Repositório: Organizar as pastas para separar o código client-side e server-side.

# 🚀 Frontend — Como rodar o projeto localmente

## Stack utilizada
- Vue 3
- Vite
- Vue Router
- Pinia
- Tailwind CSS (v4)
- ESLint + Prettier

## Pré-requisitos (instale antes de tudo)

**Node.js (versão LTS)**
1. Baixe em [nodejs.org](https://nodejs.org) — selecione "LTS".
2. Abra um terminal e confirme que funcionou:
```bash
node -v
npm -v
```
Se aparecer um número de versão em cada comando, está pronto.

## Passo a passo

1. Abra um terminal na pasta onde você quer guardar o projeto e clone o repositório:
```bash
git clone https://github.com/BrandaoJatoba/projeto-p3-2026-1.git
```

2. No VSCode, vá em **File → Open Folder** e selecione a pasta `projeto-p3-2026-1` que acabou de ser criada.

3. Abra um terminal dentro dessa pasta e entre na pasta do frontend:
```bash
cd front-end
```

4. Instale as dependências:
```bash
npm install
```

5. Rode o servidor de desenvolvimento:
```bash
npm run dev
```

6. O terminal vai mostrar um link parecido com `http://localhost:5173/` — copie e cole no navegador (ou clique nele direto no terminal). Se a página abrir, está tudo funcionando.

> **Deixe esse terminal aberto** enquanto estiver trabalhando — é ele que mantém o site rodando. Fechar ou apertar `Ctrl+C` nele desliga o servidor.

## ⚠️ Problemas comuns

**Erro `ERESOLVE unable to resolve dependency tree` no `npm install`**
Conflito conhecido entre pacotes do projeto. Rode em vez disso:
```bash
npm install --legacy-peer-deps
```

**`node` ou `git` não é reconhecido como comando**
Feche completamente o VSCode (ou o terminal) e abra de novo — às vezes o terminal precisa "reiniciar" pra reconhecer que um programa novo foi instalado no sistema.
