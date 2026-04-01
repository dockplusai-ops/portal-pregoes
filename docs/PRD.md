# PRD — Portal de Pregões v1.0
**Produto:** Portal de Pregões Públicos  
**Responsável:** Gustavo Karsten / Dockplus AI  
**Data:** 2026-04-01  
**Status:** Draft para revisão  

---

## 1. Visão Geral

### 1.1 Problema
Empresas que participam de licitações públicas perdem oportunidades porque:
- As informações dos pregões estão espalhadas em dezenas de portais (PNCP, ComprasNet, BEC, etc.)
- Não há uma ferramenta que centralize, filtre e organize os pregões relevantes por segmento
- O processo de análise técnica e preparação de proposta é manual, demorado e propenso a erros
- Não há rastreabilidade do pipeline de oportunidades (quais pregões foram avaliados, cotados, enviados)

### 1.2 Solução
Um portal SaaS que:
1. **Agrega** automaticamente todos os pregões do PNCP em tempo real
2. **Filtra** por qualquer combinação de critérios (UF, segmento, valor, prazo, órgão)
3. **Gerencia** o pipeline de oportunidades: da consulta à proposta enviada
4. **Facilita** a análise técnica e geração de proposta com dados estruturados

### 1.3 Público-alvo
- Empresas que vendem para o governo (qualquer segmento)
- Consultores e despachantes de licitação
- Departamentos de compras públicas

---

## 2. Objetivos de Negócio

| Objetivo | Métrica de Sucesso |
|---|---|
| Reduzir tempo de prospecção | < 5 min para identificar oportunidades relevantes |
| Aumentar taxa de participação | Empresas fecham 2x mais pregões |
| Centralizar pipeline | 100% das oportunidades registradas no portal |
| Agilizar proposta | Proposta gerada em < 30 min com dados do edital |

---

## 3. Escopo v1.0

### IN SCOPE
- Autenticação (email/senha + verificação por email)
- Dashboard com KPIs e pregões urgentes
- Consulta avançada com todos os filtros disponíveis
- Detalhamento completo de cada pregão
- Envio para análise (pipeline de oportunidades)
- Análise técnica do pregão
- Estimativa de custo / custo real
- Criação e gestão de proposta
- Envio da proposta (PDF + registro)

### OUT OF SCOPE v1.0
- Integração direta com portais para envio eletrônico de proposta
- Módulo multi-tenant / multi-empresa
- App mobile
- IA para análise automática de editais
- Integração com ERP

---

## 4. Funcionalidades — Detalhamento

---

### 4.1 Autenticação e Usuários

#### 4.1.1 Cadastro
- Nome completo
- Email corporativo
- Senha (mín. 8 chars, 1 maiúscula, 1 número, 1 especial)
- CNPJ da empresa (opcional no cadastro, obrigatório para enviar proposta)
- Razão social
- Segmento de atuação (multi-select: TI, Saúde, Engenharia, Alimentação, Serviços, etc.)
- UF de preferência (multi-select)

#### 4.1.2 Verificação de email
- Ao cadastrar: email com link de verificação (token JWT, expiração 24h)
- Link redireciona para `/verificar-email?token=xxx`
- Conta fica com status `pending` até verificação
- Re-envio de verificação disponível na tela de login

#### 4.1.3 Login
- Email + senha
- "Lembrar por 30 dias" (refresh token)
- Esqueci minha senha: email com link de reset (token JWT, expiração 1h)
- Bloqueio após 5 tentativas inválidas (desbloqueio automático em 15 min)

#### 4.1.4 Perfil do usuário
- Editar dados pessoais
- Alterar senha
- Configurar segmentos e UFs de interesse (usado para realce nos resultados)
- Notificações: receber email quando novo pregão bater nos filtros salvos

---

### 4.2 Dashboard

**Layout:** sidebar fixa + área principal com cards e tabela

#### 4.2.1 KPIs (cards no topo)
| Card | Dado |
|---|---|
| Pregões abertos hoje | Qty com encerramento >= hoje |
| Encerrando em 48h | Qty urgentes |
| Total no banco | Qty total de contratações |
| Em análise | Qty de oportunidades na pipeline |
| Propostas enviadas | Qty de propostas status "enviada" |
| Valor total em pipeline | Soma dos valores estimados em análise |

#### 4.2.2 Urgentes — tabela
- Pregões com `data_encerramento_proposta` nos próximos 3 dias
- Colunas: Nº PNCP | Objeto (truncado) | UF | Órgão | Valor estimado | Encerra em (countdown) | Ações
- Botão rápido "Ver detalhes" e "Enviar para análise"

#### 4.2.3 Recentes — tabela
- Últimos 10 pregões publicados no PNCP (ordenado por `data_publicacao_pncp` DESC)
- Mesmas colunas

#### 4.2.4 Minha pipeline — mini-funil
- Colunas do funil: `Em análise` → `Cotação` → `Proposta` → `Enviado` → `Ganho/Perdido`
- Qty e valor em cada etapa
- Link "Ver pipeline completa"

---

### 4.3 Consulta de Pregões

#### 4.3.1 Filtros disponíveis

**Filtros básicos (sempre visíveis):**
- Busca por texto — pesquisa no `objeto_compra` (full-text trigram)
- UF — multi-select (todos os estados + "Todos")
- Município — text com autocomplete (populado a partir dos dados)
- Situação — multi-select: Divulgada | Suspensa | Revogada | Anulada | Homologada
- Encerramento — range de datas: "Abertura de" até "Abertura até" + "Encerramento de" até "Encerramento até"

**Filtros avançados (collapsível):**
- Modalidade — multi-select (Pregão Eletrônico, Concorrência, Chamamento Público, etc.)
- Modo de disputa — Aberto | Fechado | Aberto e Fechado
- Valor estimado — range (mín/máx em R$)
- Esfera — Federal | Estadual | Municipal
- Poder — Executivo | Legislativo | Judiciário | Ministério Público | Outros
- CNPJ do órgão — busca direta por CNPJ
- Razão social do órgão — texto livre
- SRP (Sistema de Registro de Preços) — Sim | Não | Todos
- Orçamento sigiloso — Sim | Não | Todos
- Número PNCP — busca direta
- Número do processo

**Filtros salvos:**
- Botão "Salvar filtro atual" com nome
- Lista de filtros salvos no sidebar
- Notificação por email: checkbox por filtro salvo ("Notificar quando houver novidades")

#### 4.3.2 Resultados

**Controles de resultado:**
- Total encontrado (ex: "1.247 pregões")
- Ordenação: Mais recentes | Encerramento mais próximo | Maior valor | Menor valor
- Visualização: Tabela | Cards
- Seleção múltipla de registros (checkbox)
- Paginação: 20 / 50 / 100 por página

**Colunas da tabela:**
| # | Campo | Descrição |
|---|---|---|
| - | Checkbox | Seleção |
| 1 | Nº PNCP | `numero_controle_pncp` |
| 2 | Nº Processo | `numero_compra` |
| 3 | Objeto | `objeto_compra` (120 chars + tooltip) |
| 4 | Órgão | `orgao_razao_social` |
| 5 | UF | `unidade_uf_sigla` |
| 6 | Município | `unidade_municipio_nome` |
| 7 | Valor estimado | formatado em R$ |
| 8 | Abertura | `data_abertura_proposta` |
| 9 | Encerramento | `data_encerramento_proposta` + badge urgente |
| 10 | Situação | badge colorido |
| 11 | Ações | Ver detalhes \| Enviar para análise |

**Indicadores visuais:**
- Badge vermelho: encerra em < 24h
- Badge laranja: encerra em < 72h
- Badge cinza: situação diferente de "Divulgada"
- Destaque (borda azul): objeto bate nos segmentos de interesse do usuário

**Ação em lote (seleção múltipla):**
- "Enviar X selecionados para análise" — cria registros em massa na pipeline

---

### 4.4 Detalhes do Pregão

Rota: `/pregao/:numeroPNCP`

#### 4.4.1 Cabeçalho
- Número PNCP (copiável)
- Número do processo
- Modalidade + Modo de disputa
- Status badge
- Countdown (dias/horas até encerramento, se ativo)
- Botões: "Enviar para análise" | "Ver edital" (link externo) | "Copiar link"

#### 4.4.2 Seção: Objeto e Valores
- Objeto completo (sem truncamento)
- Informação complementar (se houver)
- Valor total estimado (destacado)
- Valor total homologado (se disponível)
- Orçamento sigiloso? Sim/Não
- SRP (Sistema de Registro de Preços)? Sim/Não

#### 4.4.3 Seção: Datas
- Publicação no PNCP
- Data de inclusão
- Abertura de propostas
- Encerramento de propostas
- Última atualização

#### 4.4.4 Seção: Órgão Responsável
- CNPJ (formatado, copiável)
- Razão social
- Esfera (Federal/Estadual/Municipal)
- Poder
- Unidade: código, nome, município, UF, código IBGE
- Órgão sub-rogado (se houver)

#### 4.4.5 Seção: Amparo Legal
- Código
- Nome
- Descrição completa

#### 4.4.6 Seção: Itens do Pregão
Tabela com todos os itens:
- Nº item | Descrição | Material/Serviço | Qtd | Unidade | Valor unit. estimado | Valor total | NCM/NBS | Critério de julgamento | Situação | Benefício ME/EPP

#### 4.4.7 Seção: Links
- Link para o sistema de origem
- Link para o processo eletrônico
- (ambos abrem em nova aba)

#### 4.4.8 Seção: Histórico no Portal (se já estiver em análise)
- Timeline: quando foi adicionado à pipeline, mudanças de status, criação de propostas

---

### 4.5 Pipeline de Oportunidades

#### 4.5.1 "Enviar para Análise"
Ao clicar em "Enviar para análise" (seja na listagem, no detalhe, ou em lote):

1. Modal de confirmação com:
   - Resumo do pregão (objeto + valor + encerramento)
   - Campo "Observações iniciais" (textarea opcional)
   - Campo "Responsável" (dropdown de usuários da conta, default = usuário logado)
   - Campo "Prioridade" — Alta | Média | Baixa
   - Botão "Confirmar"

2. Ao confirmar:
   - Registro criado em `oportunidades` com status `em_analise`
   - Se já existir, toast de aviso: "Este pregão já está na sua pipeline (status: X)"
   - Redireciona para a tela de detalhes da oportunidade

#### 4.5.2 Lista de Oportunidades (Pipeline)
Rota: `/pipeline`

- Visualização Kanban (colunas por status) OU tabela (toggle)
- Status do funil: `Em análise` → `Em cotação` → `Proposta criada` → `Proposta enviada` → `Ganho` | `Perdido` | `Desistência`
- Filtros: status | responsável | prioridade | data de encerramento | valor
- Busca por objeto/PNCP
- Ordenação: urgência | valor | data de criação

**Colunas Kanban:**
Cada card mostra: Objeto (truncado) | Órgão | UF | Valor | Prazo | Prioridade badge | Responsável avatar

---

### 4.6 Análise Técnica

Rota: `/oportunidade/:id/analise`

#### 4.6.1 Dados do pregão (read-only)
- Todos os dados do detalhamento (seção 4.4) em modo de leitura
- Itens em tabela editável (para anotações)

#### 4.6.2 Análise Técnica (formulário estruturado)
**Viabilidade:**
- Temos capacidade técnica? — Sim | Parcial | Não
- Temos registro/habilitação necessária? — Sim | Não | Verificar
- Existe concorrência alta? — Sim | Provável | Baixa
- Requer visita técnica? — Sim | Não
- Observações técnicas — textarea livre

**Riscos:**
- Checklist de riscos (multi-select): Prazo apertado | Valor abaixo do mercado | Exigências técnicas difíceis | Localização desfavorável | Histórico de cancelamento do órgão | Outros
- Nível de risco geral: 1–5 (slider)
- Notas sobre riscos — textarea

**Documentos necessários:**
- Checklist dinâmico de documentos habituais de habilitação
- Campo "Já temos?" por documento (toggle Sim/Não/Verificar)
- Campo para adicionar documentos específicos do edital

**Parecer final:**
- Decisão: `Participar` | `Não participar` | `Aguardar`
- Justificativa — textarea obrigatória
- Botão "Salvar análise" → status da oportunidade atualiza para `Em cotação`

---

### 4.7 Custo e Precificação

Rota: `/oportunidade/:id/custo`

#### 4.7.1 Estimativa de custo
Para cada item do pregão:
- Descrição do item (read-only do pregão)
- Qtd licitada (read-only do pregão)
- **Custo unitário** — input numérico (nosso custo real)
- **Margem (%)** — input percentual
- **Preço proposta unitário** — calculado (custo / (1 - margem)) ou editável
- **Total proposta** — calculado
- **Valor de referência PNCP** — valor estimado da API (comparação)
- **Variação vs. referência (%)** — calculada

**Totais:**
- Custo total
- Valor total da proposta
- Margem total
- Variação vs. valor estimado PNCP

**Frete / BDI / Impostos:**
- Campos opcionais para adicionar ao custo total
- BDI (%) — input
- Imposto sobre proposta (%) — input
- Frete (R$) — input
- Custo adicional (R$) — input livre com descrição

**Notas de custo** — textarea livre

Botão "Salvar cotação" → status atualiza para `Proposta criada`

---

### 4.8 Proposta

Rota: `/oportunidade/:id/proposta`

#### 4.8.1 Criação de proposta
**Dados do proponente (pré-preenchido do perfil):**
- Razão social
- CNPJ
- Endereço completo
- Responsável legal
- Telefone
- Email
- Validade da proposta (dias) — padrão 60 dias

**Dados do pregão (pré-preenchido):**
- Número PNCP / Número do processo
- Órgão licitante
- Objeto

**Itens da proposta (pré-preenchido do módulo de custo):**
- Tabela editável com todos os itens
- Edição de preço unitário permitida
- Recalculate automático dos totais

**Condições comerciais:**
- Prazo de entrega/execução — texto ou dias
- Local de entrega/execução — texto
- Forma de pagamento — texto
- Garantias oferecidas — textarea
- Observações gerais — textarea

#### 4.8.2 Preview e geração de PDF
- Preview da proposta formatada (A4, identidade visual)
- Botão "Gerar PDF" — gera PDF para download
- Botão "Salvar rascunho"
- Botão "Marcar como enviada"

#### 4.8.3 Envio
Ao clicar "Marcar como enviada":
1. Modal: "Confirmar envio da proposta?"
   - Campo "Canal de envio" — Portal PNCP | Email | Plataforma do órgão | Presencial
   - Campo "Data/hora de envio" (default: agora)
   - Campo "Protocolo/nº de comprovante" (opcional)
   - Upload de comprovante (PDF/imagem, opcional)
2. Status da oportunidade → `Proposta enviada`
3. Data de envio registrada

#### 4.8.4 Resultado
Após envio, campos disponíveis:
- Resultado: `Ganho` | `Perdido` | `Deserto` | `Cancelado`
- Posição no ranking (se perdido)
- Valor vencedor (se perdido)
- Motivo de desclassificação (se houver)
- Observações pós-resultado

---

### 4.9 Notificações e Alertas

- Email diário: "X novos pregões batem nos seus filtros salvos"
- Email: Pregão em análise encerra em 48h
- Email: Pregão em análise encerra em 24h
- Email de boas-vindas (verificação)
- Email de reset de senha
- Toast/notificações in-app para ações do sistema

---

## 5. Regras de Negócio

1. Um pregão só pode ser adicionado à pipeline **uma vez** (verificar por `numero_controle_pncp` + `user_id`)
2. Proposta só pode ser gerada se análise técnica foi concluída com decisão `Participar`
3. Proposta marcada como "enviada" não pode ser editada (apenas notas de resultado)
4. Usuário não verificado por email não acessa funcionalidades além do perfil
5. Dados de custo são privados por usuário/empresa — nunca visíveis para outros
6. O pregão original em `contratacoes` é sempre read-only (atualizado apenas pelo sync)
7. Ao marcar resultado como `Ganho`, campo "Valor contratado" fica obrigatório

---

## 6. Stack Tecnológica (recomendada)

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 15 (App Router) + Tailwind CSS + shadcn/ui |
| Backend | Next.js API Routes ou FastAPI separado |
| Banco | PostgreSQL 17 (existente no Dokploy) |
| ORM | Prisma (se Next.js) ou SQLAlchemy (se FastAPI) |
| Auth | NextAuth.js v5 com JWT + email verification |
| Email | Resend ou SMTP próprio (mail.dockplusai.com) |
| PDF | @react-pdf/renderer ou Puppeteer |
| Deploy | Dokploy (existente) |

---

## 7. Não-funcionais

- **Performance:** listagem de pregões < 500ms (índices já criados no banco)
- **Segurança:** HTTPS obrigatório, senhas com bcrypt (cost 12), JWT com expiração
- **Responsividade:** funcional em mobile (especialmente consulta e detalhes)
- **Auditoria:** toda ação do usuário na pipeline registrada em log
- **Disponibilidade:** 99.5% (Dokploy + Swarm)

---

## 8. Acceptance Criteria por módulo

### Auth
- [ ] Usuário cadastra conta, recebe email de verificação, verifica, faz login
- [ ] Login inválido 5x bloqueia por 15 min
- [ ] Reset de senha por email funciona com token expirando em 1h
- [ ] Refresh token mantém sessão por 30 dias

### Dashboard
- [ ] KPIs carregam em < 1s com dados reais do banco
- [ ] Tabela de urgentes mostra apenas pregões com encerramento > agora

### Consulta
- [ ] Busca por texto retorna resultados relevantes por trigram
- [ ] Combinação de filtros retorna intersecção correta
- [ ] Filtro salvo pode ser carregado e aplica todos os critérios
- [ ] Seleção múltipla envia todos os registros para análise em uma ação

### Pipeline
- [ ] Mesmo pregão não pode ser adicionado duas vezes
- [ ] Status avança corretamente ao longo do funil
- [ ] Kanban reflete o estado real dos registros

### Proposta
- [ ] PDF gerado contém todos os campos corretamente preenchidos
- [ ] Proposta enviada não pode ser editada
- [ ] Resultado registrado atualiza pipeline corretamente
