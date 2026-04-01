# SDD — Portal de Pregões v1.0
**Software Design Document**  
**Projeto:** Portal de Pregões Públicos  
**Baseado em:** PRD v1.0  
**Data:** 2026-04-01  
**Status:** Draft para revisão  

---

## 1. Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE                              │
│         Next.js 15 App Router (SSR + Client Components)     │
│         Tailwind CSS + shadcn/ui + Lucide Icons             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│                    API LAYER                                │
│              Next.js API Routes (/api/*)                    │
│    NextAuth.js v5 (auth) + Middleware (proteção de rotas)   │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
┌──────────▼────────────┐   ┌───────────▼──────────────────┐
│   PostgreSQL 17       │   │     Resend / SMTP             │
│   82.25.86.197:5460   │   │   (emails transacionais)      │
│   db: pregoes         │   └──────────────────────────────┘
│   (Dokploy Swarm)     │
└───────────────────────┘
           │
┌──────────▼────────────┐
│   Worker de Sync      │
│   Python 3.12         │
│   (rodando no Swarm)  │
│   15 min / batch 200  │
└───────────────────────┘
```

---

## 2. Estrutura do Projeto (Next.js)

```
portal-pregoes-app/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── cadastro/
│   │   │   └── page.tsx
│   │   ├── verificar-email/
│   │   │   └── page.tsx
│   │   └── reset-senha/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx              ← sidebar + header autenticados
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── pregoes/
│   │   │   ├── page.tsx            ← listagem/consulta
│   │   │   └── [numeroPNCP]/
│   │   │       └── page.tsx        ← detalhe
│   │   ├── pipeline/
│   │   │   ├── page.tsx            ← kanban/tabela
│   │   │   └── [id]/
│   │   │       ├── page.tsx        ← detalhe da oportunidade
│   │   │       ├── analise/
│   │   │       │   └── page.tsx
│   │   │       ├── custo/
│   │   │       │   └── page.tsx
│   │   │       └── proposta/
│   │   │           └── page.tsx
│   │   └── perfil/
│   │       └── page.tsx
│   └── api/
│       ├── auth/[...nextauth]/
│       │   └── route.ts
│       ├── pregoes/
│       │   ├── route.ts            ← GET listagem com filtros
│       │   └── [numeroPNCP]/
│       │       ├── route.ts        ← GET detalhes
│       │       └── itens/
│       │           └── route.ts
│       ├── oportunidades/
│       │   ├── route.ts            ← GET lista + POST criar
│       │   └── [id]/
│       │       ├── route.ts        ← GET + PUT + DELETE
│       │       ├── analise/
│       │       │   └── route.ts
│       │       ├── custo/
│       │       │   └── route.ts
│       │       └── proposta/
│       │           ├── route.ts
│       │           └── pdf/
│       │               └── route.ts
│       ├── usuarios/
│       │   ├── route.ts
│       │   └── [id]/
│       │       └── route.ts
│       └── email/
│           ├── verificar/
│           │   └── route.ts
│           └── reset/
│               └── route.ts
├── components/
│   ├── ui/                         ← shadcn/ui (Button, Input, Dialog...)
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── PageWrapper.tsx
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── CadastroForm.tsx
│   │   └── ResetSenhaForm.tsx
│   ├── dashboard/
│   │   ├── KPICard.tsx
│   │   ├── TabelaUrgentes.tsx
│   │   ├── TabelaRecentes.tsx
│   │   └── MiniKanban.tsx
│   ├── pregoes/
│   │   ├── FiltrosConsulta.tsx
│   │   ├── TabelaPregoes.tsx
│   │   ├── CardPregao.tsx
│   │   ├── DetalhePregao.tsx
│   │   ├── TabelaItens.tsx
│   │   └── ModalEnviarAnalise.tsx
│   ├── pipeline/
│   │   ├── KanbanBoard.tsx
│   │   ├── KanbanCard.tsx
│   │   ├── TabelaOportunidades.tsx
│   │   └── FiltrosPipeline.tsx
│   ├── oportunidade/
│   │   ├── CabecalhoOportunidade.tsx
│   │   ├── FormAnalise.tsx
│   │   ├── FormCusto.tsx
│   │   ├── TabelaCusto.tsx
│   │   ├── FormProposta.tsx
│   │   ├── PreviewProposta.tsx
│   │   └── ModalResultado.tsx
│   └── shared/
│       ├── BadgeSituacao.tsx
│       ├── BadgeUrgencia.tsx
│       ├── CountdownTimer.tsx
│       ├── FiltroBadge.tsx
│       └── EmptyState.tsx
├── lib/
│   ├── db.ts                       ← cliente Prisma
│   ├── auth.ts                     ← config NextAuth
│   ├── email.ts                    ← wrapper Resend/SMTP
│   ├── pdf.ts                      ← geração de PDF
│   ├── tokens.ts                   ← geração/verificação JWT tokens
│   └── utils.ts                    ← formatadores, helpers
├── hooks/
│   ├── usePregoes.ts
│   ├── useOportunidade.ts
│   ├── useFiltros.ts
│   └── usePipeline.ts
├── types/
│   ├── pregao.ts
│   ├── oportunidade.ts
│   ├── usuario.ts
│   └── api.ts
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── middleware.ts                   ← proteção de rotas auth
├── next.config.ts
└── .env.local
```

---

## 3. Schema do Banco de Dados

### 3.1 Tabelas existentes (sync PNCP — read-only pelo app)

```sql
-- Já existente — não alterar
-- contratacoes (todos os campos da API PNCP)
-- itens (itens de cada pregão)
-- sync_log
-- sync_cursor
```

### 3.2 Novas tabelas (gerenciadas pelo app)

```sql
-- ============================================================
-- USUÁRIOS
-- ============================================================
CREATE TABLE usuarios (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    senha_hash          TEXT NOT NULL,
    email_verificado    BOOLEAN DEFAULT FALSE,
    email_verificado_em TIMESTAMPTZ,
    cnpj_empresa        TEXT,
    razao_social        TEXT,
    segmentos           TEXT[],          -- ex: ['TI', 'Saúde']
    ufs_interesse       TEXT[],          -- ex: ['PR', 'SC', 'SP']
    status              TEXT DEFAULT 'pending',  -- pending | active | blocked
    tentativas_login    INTEGER DEFAULT 0,
    bloqueado_ate       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TOKENS (email verification + reset senha)
-- ============================================================
CREATE TABLE tokens_email (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    tipo        TEXT NOT NULL,           -- 'verificacao' | 'reset_senha'
    usado       BOOLEAN DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FILTROS SALVOS
-- ============================================================
CREATE TABLE filtros_salvos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id      UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nome            TEXT NOT NULL,
    criterios       JSONB NOT NULL,     -- todos os filtros em JSON
    notificar       BOOLEAN DEFAULT FALSE,
    ultimo_check    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- OPORTUNIDADES (pipeline)
-- ============================================================
CREATE TABLE oportunidades (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id              UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    numero_controle_pncp    TEXT REFERENCES contratacoes(numero_controle_pncp),
    status                  TEXT NOT NULL DEFAULT 'em_analise',
    -- em_analise | em_cotacao | proposta_criada | proposta_enviada
    -- ganho | perdido | desistencia | cancelado
    prioridade              TEXT DEFAULT 'media',  -- alta | media | baixa
    responsavel_id          UUID REFERENCES usuarios(id),
    observacoes_iniciais    TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(usuario_id, numero_controle_pncp)
);

-- ============================================================
-- ANÁLISE TÉCNICA
-- ============================================================
CREATE TABLE analises_tecnicas (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oportunidade_id             UUID UNIQUE REFERENCES oportunidades(id) ON DELETE CASCADE,
    capacidade_tecnica          TEXT,   -- 'sim' | 'parcial' | 'nao'
    tem_habilitacao             TEXT,   -- 'sim' | 'nao' | 'verificar'
    concorrencia_alta           TEXT,   -- 'sim' | 'provavel' | 'baixa'
    requer_visita               BOOLEAN DEFAULT FALSE,
    observacoes_tecnicas        TEXT,
    riscos                      TEXT[], -- array de riscos selecionados
    nivel_risco                 INTEGER CHECK (nivel_risco BETWEEN 1 AND 5),
    notas_riscos                TEXT,
    documentos                  JSONB,  -- [{nome, obrigatorio, temos}]
    parecer                     TEXT,   -- 'participar' | 'nao_participar' | 'aguardar'
    justificativa_parecer       TEXT NOT NULL DEFAULT '',
    finalizado                  BOOLEAN DEFAULT FALSE,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- COTAÇÃO / CUSTO
-- ============================================================
CREATE TABLE cotacoes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oportunidade_id UUID UNIQUE REFERENCES oportunidades(id) ON DELETE CASCADE,
    itens           JSONB NOT NULL DEFAULT '[]',
    -- [{numero_item, descricao, qtd, custo_unitario, margem_pct,
    --   preco_proposta_unit, valor_total_proposta, valor_referencia_pncp}]
    bdi_pct         NUMERIC(5,2) DEFAULT 0,
    imposto_pct     NUMERIC(5,2) DEFAULT 0,
    frete_rs        NUMERIC(18,2) DEFAULT 0,
    custo_adicional_rs  NUMERIC(18,2) DEFAULT 0,
    desc_adicional  TEXT,
    total_custo     NUMERIC(18,2),
    total_proposta  NUMERIC(18,2),
    margem_total    NUMERIC(5,2),
    notas           TEXT,
    finalizado      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PROPOSTAS
-- ============================================================
CREATE TABLE propostas (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oportunidade_id         UUID REFERENCES oportunidades(id) ON DELETE CASCADE,
    versao                  INTEGER DEFAULT 1,
    -- Proponente
    razao_social            TEXT NOT NULL,
    cnpj                    TEXT NOT NULL,
    endereco                TEXT,
    responsavel_legal       TEXT,
    telefone                TEXT,
    email_contato           TEXT,
    validade_dias           INTEGER DEFAULT 60,
    -- Condições
    prazo_entrega           TEXT,
    local_entrega           TEXT,
    forma_pagamento         TEXT,
    garantias               TEXT,
    observacoes             TEXT,
    -- Itens (snapshot no momento da geração)
    itens                   JSONB NOT NULL DEFAULT '[]',
    total_proposta          NUMERIC(18,2),
    -- Controle
    status                  TEXT DEFAULT 'rascunho',
    -- rascunho | enviada | ganho | perdido | deserto | cancelado
    canal_envio             TEXT,
    data_envio              TIMESTAMPTZ,
    protocolo_envio         TEXT,
    comprovante_url         TEXT,
    -- Resultado
    resultado               TEXT,
    posicao_ranking         INTEGER,
    valor_vencedor          NUMERIC(18,2),
    motivo_desclassificacao TEXT,
    observacoes_resultado   TEXT,
    -- Arquivo
    pdf_url                 TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LOG DE AÇÕES (auditoria)
-- ============================================================
CREATE TABLE auditoria (
    id              BIGSERIAL PRIMARY KEY,
    usuario_id      UUID REFERENCES usuarios(id),
    entidade        TEXT NOT NULL,   -- 'oportunidade' | 'proposta' | 'analise'
    entidade_id     TEXT NOT NULL,
    acao            TEXT NOT NULL,   -- 'criar' | 'atualizar' | 'excluir' | 'enviar'
    dados_antes     JSONB,
    dados_depois    JSONB,
    ip              TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES ADICIONAIS
-- ============================================================
CREATE INDEX idx_oportunidades_usuario ON oportunidades(usuario_id);
CREATE INDEX idx_oportunidades_status ON oportunidades(status);
CREATE INDEX idx_oportunidades_pncp ON oportunidades(numero_controle_pncp);
CREATE INDEX idx_propostas_oportunidade ON propostas(oportunidade_id);
CREATE INDEX idx_auditoria_entidade ON auditoria(entidade, entidade_id);
CREATE INDEX idx_tokens_email ON tokens_email(token) WHERE usado = FALSE;
```

---

## 4. Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Usuario {
  id                UUID     @id @default(uuid())
  nome              String
  email             String   @unique
  senhaHash         String   @map("senha_hash")
  emailVerificado   Boolean  @default(false) @map("email_verificado")
  emailVerificadoEm DateTime? @map("email_verificado_em")
  cnpjEmpresa       String?  @map("cnpj_empresa")
  razaoSocial       String?  @map("razao_social")
  segmentos         String[]
  ufsInteresse      String[] @map("ufs_interesse")
  status            String   @default("pending")
  tentativasLogin   Int      @default(0) @map("tentativas_login")
  bloqueadoAte      DateTime? @map("bloqueado_ate")
  createdAt         DateTime @default(now()) @map("created_at")
  updatedAt         DateTime @updatedAt @map("updated_at")

  tokens           TokenEmail[]
  filtrosSalvos    FiltroSalvo[]
  oportunidades    Oportunidade[]  @relation("Dono")
  responsavel      Oportunidade[]  @relation("Responsavel")

  @@map("usuarios")
}

model TokenEmail {
  id         UUID     @id @default(uuid())
  usuarioId  UUID     @map("usuario_id")
  token      String   @unique
  tipo       String
  usado      Boolean  @default(false)
  expiresAt  DateTime @map("expires_at")
  createdAt  DateTime @default(now()) @map("created_at")

  usuario    Usuario  @relation(fields: [usuarioId], references: [id], onDelete: Cascade)

  @@map("tokens_email")
}

model FiltroSalvo {
  id          UUID     @id @default(uuid())
  usuarioId   UUID     @map("usuario_id")
  nome        String
  criterios   Json
  notificar   Boolean  @default(false)
  ultimoCheck DateTime? @map("ultimo_check")
  createdAt   DateTime @default(now()) @map("created_at")

  usuario     Usuario  @relation(fields: [usuarioId], references: [id], onDelete: Cascade)

  @@map("filtros_salvos")
}

model Oportunidade {
  id                    UUID     @id @default(uuid())
  usuarioId             UUID     @map("usuario_id")
  numeroControlePncp    String   @map("numero_controle_pncp")
  status                String   @default("em_analise")
  prioridade            String   @default("media")
  responsavelId         UUID?    @map("responsavel_id")
  observacoesIniciais   String?  @map("observacoes_iniciais")
  createdAt             DateTime @default(now()) @map("created_at")
  updatedAt             DateTime @updatedAt @map("updated_at")

  usuario       Usuario       @relation("Dono", fields: [usuarioId], references: [id], onDelete: Cascade)
  responsavel   Usuario?      @relation("Responsavel", fields: [responsavelId], references: [id])
  analise       AnaliseTecnica?
  cotacao       Cotacao?
  propostas     Proposta[]

  @@unique([usuarioId, numeroControlePncp])
  @@map("oportunidades")
}

model AnaliseTecnica {
  id                   UUID     @id @default(uuid())
  oportunidadeId       UUID     @unique @map("oportunidade_id")
  capacidadeTecnica    String?  @map("capacidade_tecnica")
  temHabilitacao       String?  @map("tem_habilitacao")
  concorrenciaAlta     String?  @map("concorrencia_alta")
  requerVisita         Boolean  @default(false) @map("requer_visita")
  observacoesTecnicas  String?  @map("observacoes_tecnicas")
  riscos               String[]
  nivelRisco           Int?     @map("nivel_risco")
  notasRiscos          String?  @map("notas_riscos")
  documentos           Json?
  parecer              String?
  justificativaParecer String   @default("") @map("justificativa_parecer")
  finalizado           Boolean  @default(false)
  createdAt            DateTime @default(now()) @map("created_at")
  updatedAt            DateTime @updatedAt @map("updated_at")

  oportunidade  Oportunidade @relation(fields: [oportunidadeId], references: [id], onDelete: Cascade)

  @@map("analises_tecnicas")
}

model Cotacao {
  id              UUID     @id @default(uuid())
  oportunidadeId  UUID     @unique @map("oportunidade_id")
  itens           Json     @default("[]")
  bdiPct          Decimal  @default(0) @db.Decimal(5,2) @map("bdi_pct")
  impostoPct      Decimal  @default(0) @db.Decimal(5,2) @map("imposto_pct")
  freteRs         Decimal  @default(0) @db.Decimal(18,2) @map("frete_rs")
  custoAdicionalRs Decimal @default(0) @db.Decimal(18,2) @map("custo_adicional_rs")
  descAdicional   String?  @map("desc_adicional")
  totalCusto      Decimal? @db.Decimal(18,2) @map("total_custo")
  totalProposta   Decimal? @db.Decimal(18,2) @map("total_proposta")
  margemTotal     Decimal? @db.Decimal(5,2) @map("margem_total")
  notas           String?
  finalizado      Boolean  @default(false)
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  oportunidade  Oportunidade @relation(fields: [oportunidadeId], references: [id], onDelete: Cascade)

  @@map("cotacoes")
}

model Proposta {
  id                     UUID     @id @default(uuid())
  oportunidadeId         UUID     @map("oportunidade_id")
  versao                 Int      @default(1)
  razaoSocial            String   @map("razao_social")
  cnpj                   String
  endereco               String?
  responsavelLegal       String?  @map("responsavel_legal")
  telefone               String?
  emailContato           String?  @map("email_contato")
  validadeDias           Int      @default(60) @map("validade_dias")
  prazoEntrega           String?  @map("prazo_entrega")
  localEntrega           String?  @map("local_entrega")
  formaPagamento         String?  @map("forma_pagamento")
  garantias              String?
  observacoes            String?
  itens                  Json     @default("[]")
  totalProposta          Decimal? @db.Decimal(18,2) @map("total_proposta")
  status                 String   @default("rascunho")
  canalEnvio             String?  @map("canal_envio")
  dataEnvio              DateTime? @map("data_envio")
  protocoloEnvio         String?  @map("protocolo_envio")
  comprovanteUrl         String?  @map("comprovante_url")
  resultado              String?
  posicaoRanking         Int?     @map("posicao_ranking")
  valorVencedor          Decimal? @db.Decimal(18,2) @map("valor_vencedor")
  motivoDesclassificacao String?  @map("motivo_desclassificacao")
  observacoesResultado   String?  @map("observacoes_resultado")
  pdfUrl                 String?  @map("pdf_url")
  createdAt              DateTime @default(now()) @map("created_at")
  updatedAt              DateTime @updatedAt @map("updated_at")

  oportunidade  Oportunidade @relation(fields: [oportunidadeId], references: [id], onDelete: Cascade)

  @@map("propostas")
}
```

---

## 5. API Routes — Especificação Detalhada

### 5.1 Auth

```
POST   /api/auth/cadastro
POST   /api/auth/login              ← NextAuth credentials
GET    /api/auth/verificar-email?token=xxx
POST   /api/auth/reenviar-verificacao
POST   /api/auth/esqueci-senha      { email }
POST   /api/auth/reset-senha        { token, novaSenha }
```

### 5.2 Pregões (read-only, fonte: tabela contratacoes)

```
GET    /api/pregoes
  Query params:
    q               — busca textual (trigram no objeto_compra)
    ufs             — ex: PR,SC,SP (multi)
    municipio       — texto
    situacao        — ex: 1,2,3 (ids)
    modalidade      — ex: 6
    modo_disputa    — ex: 1,2
    valor_min       — número
    valor_max       — número
    esfera          — F|E|M
    poder           — N|E|J|M|O
    cnpj_orgao      — texto
    orgao           — texto (razão social)
    srp             — true|false
    orcamento_sig   — true|false
    encerra_de      — ISO date
    encerra_ate     — ISO date
    abertura_de     — ISO date
    abertura_ate    — ISO date
    publicado_de    — ISO date
    publicado_ate   — ISO date
    numero_pncp     — texto exato
    numero_processo — texto
    page            — default 1
    per_page        — default 20, max 100
    sort            — publicacao_desc | encerramento_asc | valor_desc | valor_asc

  Response 200:
    {
      data: Contratacao[],
      total: number,
      page: number,
      per_page: number,
      total_pages: number
    }

GET    /api/pregoes/:numeroPNCP
  Response 200: Contratacao (com itens incluídos)

GET    /api/pregoes/:numeroPNCP/itens
  Response 200: Item[]

GET    /api/pregoes/stats
  Response 200: { total, abertos, encerrando48h, porUF: [...], porModalidade: [...] }
```

### 5.3 Oportunidades

```
GET    /api/oportunidades
  Query: status | prioridade | responsavel | page | per_page | sort
  Response 200: { data: Oportunidade[], total, ... }

POST   /api/oportunidades
  Body: { numeroPNCP, observacoesIniciais, prioridade, responsavelId }
  Response 201: Oportunidade
  Response 409: { error: "Pregão já está na pipeline", status: "..." }

GET    /api/oportunidades/kanban
  Response 200: { em_analise: [], em_cotacao: [], proposta_criada: [], proposta_enviada: [], ganho: [], perdido: [] }

GET    /api/oportunidades/:id
  Response 200: Oportunidade (com pregão, analise, cotacao, propostas)

PATCH  /api/oportunidades/:id
  Body: { status?, prioridade?, responsavelId?, observacoesIniciais? }
  Response 200: Oportunidade

DELETE /api/oportunidades/:id
  Response 204

POST   /api/oportunidades/bulk
  Body: { numerosControlePNCP: string[], prioridade, observacoes }
  Response 201: { criadas: number, duplicadas: number }
```

### 5.4 Análise Técnica

```
GET    /api/oportunidades/:id/analise
  Response 200: AnaliseTecnica | null

POST   /api/oportunidades/:id/analise
  Body: { capacidadeTecnica, temHabilitacao, concorrenciaAlta, requerVisita,
          observacoesTecnicas, riscos[], nivelRisco, notasRiscos, documentos[],
          parecer, justificativaParecer }
  Response 201: AnaliseTecnica

PATCH  /api/oportunidades/:id/analise
  Body: (campos parciais)
  Response 200: AnaliseTecnica

POST   /api/oportunidades/:id/analise/finalizar
  Body: { parecer, justificativaParecer }
  Efeito: analise.finalizado = true, oportunidade.status → em_cotacao (se parecer=participar)
  Response 200: { analise, oportunidade }
```

### 5.5 Cotação

```
GET    /api/oportunidades/:id/cotacao
  Response 200: Cotacao | null

POST   /api/oportunidades/:id/cotacao
  Body: { itens[], bdiPct, impostoPct, freteRs, custoAdicionalRs, descAdicional, notas }
  Response 201: Cotacao

PATCH  /api/oportunidades/:id/cotacao
  Body: (campos parciais)
  Response 200: Cotacao

POST   /api/oportunidades/:id/cotacao/finalizar
  Efeito: cotacao.finalizado = true, oportunidade.status → proposta_criada
  Response 200: { cotacao, oportunidade }
```

### 5.6 Proposta

```
GET    /api/oportunidades/:id/proposta
  Response 200: Proposta[] (todas as versões)

POST   /api/oportunidades/:id/proposta
  Body: { razaoSocial, cnpj, endereco, responsavelLegal, telefone, emailContato,
          validadeDias, prazoEntrega, localEntrega, formaPagamento, garantias,
          observacoes, itens[] }
  Efeito: versao auto-incrementa, oportunidade.status → proposta_criada
  Response 201: Proposta

PATCH  /api/oportunidades/:id/proposta/:propostaId
  Restrição: só se status = 'rascunho'
  Body: (campos parciais)
  Response 200: Proposta

POST   /api/oportunidades/:id/proposta/:propostaId/pdf
  Response 200: { pdfUrl: string }    ← URL do PDF gerado

POST   /api/oportunidades/:id/proposta/:propostaId/enviar
  Body: { canalEnvio, dataEnvio, protocoloEnvio?, comprovanteUrl? }
  Efeito: proposta.status → enviada, oportunidade.status → proposta_enviada
  Response 200: { proposta, oportunidade }

POST   /api/oportunidades/:id/proposta/:propostaId/resultado
  Body: { resultado, posicaoRanking?, valorVencedor?, motivoDesclassificacao?, observacoesResultado? }
  Efeito: proposta.status → resultado, oportunidade.status → resultado
  Response 200: { proposta, oportunidade }
```

### 5.7 Filtros Salvos

```
GET    /api/filtros-salvos            → FiltroSalvo[]
POST   /api/filtros-salvos            Body: { nome, criterios, notificar }
PATCH  /api/filtros-salvos/:id        Body: { nome?, notificar? }
DELETE /api/filtros-salvos/:id
```

### 5.8 Usuário / Perfil

```
GET    /api/me                        → dados do usuário logado
PATCH  /api/me                        Body: { nome, cnpj, razaoSocial, segmentos, ufs, ... }
PATCH  /api/me/senha                  Body: { senhaAtual, novaSenha }
```

---

## 6. Fluxos de Autenticação

### 6.1 Cadastro + Verificação

```
1. POST /api/auth/cadastro
   → Valida campos
   → bcrypt.hash(senha, 12)
   → INSERT usuarios (status = 'pending')
   → Gera token JWT (tipo='verificacao', exp=24h)
   → INSERT tokens_email
   → Envia email: "Verifique seu email"
   → Retorna 201

2. Usuário clica no link → GET /verificar-email?token=xxx
   → Valida token (existe, não usado, não expirado)
   → UPDATE usuarios SET email_verificado=true, status='active'
   → UPDATE tokens_email SET usado=true
   → Redireciona para /login?verificado=true
```

### 6.2 Login + Sessão

```
NextAuth Credentials Provider:
  - Busca usuário por email
  - Verifica status != 'blocked' e bloqueado_ate < NOW()
  - bcrypt.compare(senha, senhaHash)
  - Se erro: incrementa tentativas_login, bloqueia se >= 5
  - Se sucesso: zera tentativas_login
  - Verifica email_verificado=true
  - Retorna { id, nome, email, status }

Session callback: adiciona id ao token JWT
Middleware: redireciona /api/* e /(dashboard)/* para /login se sem sessão
```

### 6.3 Reset de senha

```
1. POST /api/auth/esqueci-senha { email }
   → Busca usuário (sempre retorna 200 para não revelar emails)
   → Gera token JWT (tipo='reset_senha', exp=1h)
   → Envia email com link /reset-senha?token=xxx

2. POST /api/auth/reset-senha { token, novaSenha }
   → Valida token
   → bcrypt.hash(novaSenha, 12)
   → UPDATE usuarios SET senha_hash
   → Invalida token
   → Retorna 200
```

---

## 7. Query de Listagem de Pregões (SQL Base)

```sql
-- Gerada dinamicamente em /api/pregoes
-- Usa Prisma queryRaw para aproveitar os índices existentes

SELECT
    c.numero_controle_pncp,
    c.numero_compra,
    c.objeto_compra,
    c.orgao_razao_social,
    c.unidade_uf_sigla,
    c.unidade_municipio_nome,
    c.valor_total_estimado,
    c.data_abertura_proposta,
    c.data_encerramento_proposta,
    c.situacao_compra_id,
    c.situacao_compra_nome,
    c.modalidade_nome,
    c.modo_disputa_nome,
    c.srp,
    -- Urgência calculada
    CASE
        WHEN c.data_encerramento_proposta < NOW() THEN 'expirado'
        WHEN c.data_encerramento_proposta < NOW() + INTERVAL '24 hours' THEN 'critico'
        WHEN c.data_encerramento_proposta < NOW() + INTERVAL '72 hours' THEN 'urgente'
        ELSE 'normal'
    END AS urgencia,
    -- Se está na pipeline do usuário
    o.id AS oportunidade_id,
    o.status AS pipeline_status
FROM contratacoes c
LEFT JOIN oportunidades o
    ON o.numero_controle_pncp = c.numero_controle_pncp
    AND o.usuario_id = $usuarioId
WHERE
    -- Busca textual
    ($q IS NULL OR c.objeto_compra ILIKE '%' || $q || '%'
        OR c.objeto_compra % $q)  -- trigram similarity
    -- UF
    AND ($ufs IS NULL OR c.unidade_uf_sigla = ANY($ufs))
    -- Município
    AND ($municipio IS NULL OR c.unidade_municipio_nome ILIKE '%' || $municipio || '%')
    -- Situação
    AND ($situacao IS NULL OR c.situacao_compra_id = ANY($situacao))
    -- Modalidade
    AND ($modalidade IS NULL OR c.modalidade_id = ANY($modalidade))
    -- Valor
    AND ($valor_min IS NULL OR c.valor_total_estimado >= $valor_min)
    AND ($valor_max IS NULL OR c.valor_total_estimado <= $valor_max)
    -- Esfera
    AND ($esfera IS NULL OR c.orgao_esfera_id = $esfera)
    -- Poder
    AND ($poder IS NULL OR c.orgao_poder_id = $poder)
    -- Datas
    AND ($encerra_de IS NULL OR c.data_encerramento_proposta >= $encerra_de)
    AND ($encerra_ate IS NULL OR c.data_encerramento_proposta <= $encerra_ate)
    AND ($publicado_de IS NULL OR c.data_publicacao_pncp >= $publicado_de)
    AND ($publicado_ate IS NULL OR c.data_publicacao_pncp <= $publicado_ate)
    -- SRP
    AND ($srp IS NULL OR c.srp = $srp)
    -- Número exato
    AND ($numero_pncp IS NULL OR c.numero_controle_pncp = $numero_pncp)
ORDER BY
    CASE WHEN $sort = 'encerramento_asc' THEN c.data_encerramento_proposta END ASC,
    CASE WHEN $sort = 'valor_desc' THEN c.valor_total_estimado END DESC,
    CASE WHEN $sort = 'valor_asc' THEN c.valor_total_estimado END ASC,
    c.data_publicacao_pncp DESC  -- default
LIMIT $per_page
OFFSET ($page - 1) * $per_page;
```

---

## 8. Geração de PDF da Proposta

```typescript
// lib/pdf.ts
// Usar @react-pdf/renderer

interface PropostaPDFProps {
  proposta: Proposta;
  pregao: Contratacao;
  empresa: { razaoSocial, cnpj, endereco, responsavel, telefone, email };
}

// Estrutura do PDF:
// 1. Cabeçalho com logo + dados da empresa proponente
// 2. Destinatário: órgão licitante + número PNCP + objeto
// 3. Tabela de itens: nº | descrição | qtd | unidade | vlr unit | vlr total
// 4. Resumo: subtotal | BDI | impostos | frete | TOTAL GERAL
// 5. Condições comerciais: prazo | local | pagamento | garantias
// 6. Validade da proposta
// 7. Observações
// 8. Local, data e assinatura

// Gerar e salvar: armazenar como base64 ou salvar em volume do Dokploy
// PDF URL: /api/oportunidades/:id/proposta/:propostaId/pdf (stream)
```

---

## 9. Componentes UI — Especificação

### 9.1 FiltrosConsulta

```typescript
// Estado gerenciado com useReducer ou Zustand
interface FiltrosState {
  q: string;
  ufs: string[];
  municipio: string;
  situacao: number[];
  modalidade: number[];
  modoDisputa: number[];
  valorMin: number | null;
  valorMax: number | null;
  esfera: string | null;
  poder: string | null;
  cnpjOrgao: string;
  orgao: string;
  srp: boolean | null;
  orcamentoSigiloso: boolean | null;
  encerraDe: Date | null;
  encerraAte: Date | null;
  aberturaDe: Date | null;
  aberturaAte: Date | null;
  publicadoDe: Date | null;
  publicadoAte: Date | null;
  numeroPncp: string;
  numeroProcesso: string;
}

// Comportamento:
// - Filtros básicos visíveis; avançados em Collapsible
// - Cada mudança dispara debounce 400ms → fetch
// - Botão "Limpar filtros" reseta state
// - Botão "Salvar filtro" abre modal com campo nome
// - Filtros aplicados mostrados como badges removíveis no topo da tabela
```

### 9.2 TabelaPregoes

```typescript
// Seleção múltipla com checkboxes
// Estado: selectedIds: Set<string>
// Seleção de todos: seleciona apenas a página atual
// Ação em lote aparece em barra fixa no bottom quando selection.size > 0:
//   "X pregões selecionados — Enviar para análise"
```

### 9.3 KanbanBoard

```typescript
// Colunas fixas: em_analise | em_cotacao | proposta_criada | proposta_enviada | ganho | perdido
// Drag-and-drop com @hello-pangea/dnd
// Ao soltar card em outra coluna → PATCH /api/oportunidades/:id { status }
// Cards clicáveis → /pipeline/:id
// Cada coluna mostra: qty de cards + soma de valores
```

### 9.4 CountdownTimer

```typescript
// Props: targetDate: Date, size: 'sm'|'md'|'lg'
// Output: "3d 4h 22m" ou "22h 15m" ou "45m" ou "EXPIRADO"
// Update a cada 30s via setInterval
// Cor: verde > 7d | amarelo 3-7d | laranja 1-3d | vermelho < 24h
```

---

## 10. Middleware de Proteção de Rotas

```typescript
// middleware.ts
import { auth } from "@/lib/auth";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthPage = req.nextUrl.pathname.startsWith("/(auth)");
  const isApiRoute = req.nextUrl.pathname.startsWith("/api");
  const isPublicApi = ["/api/auth"].some(p => req.nextUrl.pathname.startsWith(p));

  if (!isLoggedIn && !isAuthPage && !isPublicApi) {
    return Response.redirect(new URL("/login", req.nextUrl));
  }

  if (isLoggedIn && isAuthPage) {
    return Response.redirect(new URL("/dashboard", req.nextUrl));
  }
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

---

## 11. Emails Transacionais

| Template | Trigger | Conteúdo |
|---|---|---|
| `boas-vindas` | Cadastro | Nome, link de verificação, botão "Verificar email" |
| `reset-senha` | Solicitação reset | Nome, link de reset (1h), aviso se não solicitou |
| `pregoes-novos` | Cron diário | X novos pregões por filtro salvo, tabela resumo, link consulta |
| `urgencia-48h` | Cron a cada 6h | Pregões em análise encerrando em 48h, countdown |
| `urgencia-24h` | Cron a cada hora | Idem para 24h, mais urgente |

---

## 12. Variáveis de Ambiente

```env
# .env.local
DATABASE_URL=postgresql://dockplusai:k9mwqvbpth2fxnsd@82.25.86.197:5460/pregoes
NEXTAUTH_URL=https://pregoes.dockplusai.dev
NEXTAUTH_SECRET=<gerar com: openssl rand -hex 32>

# Email (SMTP próprio ou Resend)
SMTP_HOST=mail.dockplusai.com
SMTP_PORT=587
SMTP_USER=pregoes@dockplusai.com
SMTP_PASS=<senha>
SMTP_FROM=Portal de Pregões <pregoes@dockplusai.com>

# Ou Resend
RESEND_API_KEY=re_xxx

# Upload de comprovantes (Cloudflare R2)
R2_ACCOUNT_ID=424b98a9052c55050cc0f1de271192dc
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=portal-pregoes
R2_PUBLIC_URL=https://...

NODE_ENV=production
```

---

## 13. Deployment no Dokploy

**Projeto:** `portal-pregoes` (existente)

**Serviços adicionais:**
1. `sync-worker` — já criado (Python, roda a cada 15 min)
2. `pregoes-app` — Next.js app (a criar)
   - Repo: `dockplusai-ops/portal-pregoes-app`
   - Dockerfile: Next.js padrão
   - Porta: 3000
   - Domínio: `pregoes.dockplusai.dev`
   - Env: todas as variáveis acima

**Banco:** `pregoes-db` (existente, PostgreSQL 17, porta 5460)

---

## 14. Fases de Desenvolvimento

### Fase 1 — Base (Semana 1-2)
- [ ] Setup Next.js 15 + Prisma + shadcn/ui
- [ ] Schema migrations (novas tabelas)
- [ ] Auth completo (cadastro, verificação email, login, reset)
- [ ] Layout base (sidebar, header, rotas protegidas)
- [ ] Dashboard com KPIs reais

### Fase 2 — Consulta (Semana 2-3)
- [ ] API de pregões com todos os filtros
- [ ] Tabela de resultados com paginação, seleção múltipla
- [ ] Detalhamento completo do pregão
- [ ] Filtros salvos

### Fase 3 — Pipeline (Semana 3-4)
- [ ] Enviar para análise (individual + lote)
- [ ] Pipeline Kanban + tabela
- [ ] Detalhamento da oportunidade

### Fase 4 — Análise e Custo (Semana 4-5)
- [ ] Formulário de análise técnica
- [ ] Módulo de custo/precificação com cálculos automáticos

### Fase 5 — Proposta (Semana 5-6)
- [ ] Formulário de proposta
- [ ] Geração de PDF
- [ ] Registro de envio e resultado

### Fase 6 — Notificações e polish (Semana 6)
- [ ] Emails transacionais (urgência, novidades)
- [ ] Ajustes de UX, responsividade
- [ ] Testes e deploy

---

## 15. Acceptance Criteria Técnicos

### Auth
- [ ] bcrypt cost 12, senha mínimo 8 chars com regras
- [ ] Token de verificação expira em 24h, reset em 1h
- [ ] 5 tentativas → bloqueio 15 min registrado em `bloqueado_ate`
- [ ] Middleware bloqueia acesso sem sessão a todas as rotas do dashboard

### Consulta
- [ ] Query com 5+ filtros retorna em < 500ms (índices validados)
- [ ] Busca textual usa `pg_trgm` (índice `idx_contratacoes_objeto_trgm`)
- [ ] Paginação correta com `OFFSET`/`LIMIT` e contagem total separada

### Pipeline
- [ ] Unique constraint `(usuario_id, numero_controle_pncp)` previne duplicatas
- [ ] Status só avança no sentido correto do funil
- [ ] Auditoria: toda mudança de status registrada em `auditoria`

### PDF
- [ ] PDF gerado em < 3s para propostas com até 50 itens
- [ ] Formatação consistente independente do conteúdo

### Performance
- [ ] Dashboard KPIs: consultas < 200ms (índices em `situacao_compra_id`, `data_encerramento_proposta`)
- [ ] Listagem com filtros default: < 500ms
- [ ] Kanban: < 300ms (carrega apenas campos necessários)
