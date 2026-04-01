#!/usr/bin/env python3
"""
Portal Pregões - PNCP Sync
Busca 200 pregões a cada execução (cron: a cada 15 min)
Começa pelos mais novos, avança no histórico progressivamente
"""

import os
import sys
import json
import time
import logging
import requests
import psycopg2
import psycopg2.extras
from datetime import date, timedelta, datetime

# ===== CONFIG =====
DB_URL = os.getenv("DATABASE_URL", 
    "postgresql://dockplusai:k9mwqvbpth2fxnsd@82.25.86.197:5460/pregoes")

PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
BATCH_SIZE = 200
PAGE_SIZE  = 20   # máximo que a API retorna de forma estável
MODALIDADES = [6]  # 6 = Pregão Eletrônico

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("sync")


def get_conn():
    return psycopg2.connect(DB_URL)


def fetch_page(modalidade_id: int, data_inicial: str, data_final: str, pagina: int) -> dict:
    """Busca uma página da API PNCP"""
    url = f"{PNCP_BASE}/contratacoes/publicacao"
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "codigoModalidadeContratacao": modalidade_id,
        "pagina": pagina,
        "tamanhoPagina": PAGE_SIZE,
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                log.warning("Rate limit, aguardando 5s...")
                time.sleep(5)
            else:
                log.error(f"HTTP {r.status_code}: {r.text[:200]}")
                return {}
        except Exception as e:
            log.error(f"Erro na requisição (tentativa {attempt+1}): {e}")
            time.sleep(2)
    return {}


def upsert_contratacao(cur, item: dict) -> str:
    """Insere ou atualiza uma contratação. Retorna 'insert' ou 'update'."""
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    orgao_sub = item.get("orgaoSubRogado") or {}
    unidade_sub = item.get("unidadeSubRogada") or {}
    amparo = item.get("amparoLegal") or {}
    instrumento = item.get("tipoInstrumentoConvocatorioNome")

    sql = """
    INSERT INTO contratacoes (
        numero_controle_pncp, ano_compra, numero_compra, sequencial_compra, processo,
        modalidade_id, modalidade_nome, situacao_compra_id, situacao_compra_nome,
        modo_disputa_id, modo_disputa_nome,
        objeto_compra, valor_total_estimado, valor_total_homologado,
        orcamento_sigiloso, srp,
        data_publicacao_pncp, data_inclusao, data_atualizacao, data_atualizacao_global,
        data_abertura_proposta, data_encerramento_proposta,
        amparo_legal_codigo, amparo_legal_nome, amparo_legal_descricao,
        tipo_instrumento_codigo, tipo_instrumento_nome,
        link_sistema_origem, link_processo_eletronico, informacao_complementar,
        justificativa_presencial, usuario_nome,
        orgao_cnpj, orgao_razao_social, orgao_poder_id, orgao_esfera_id,
        unidade_codigo, unidade_nome, unidade_municipio_nome,
        unidade_uf_sigla, unidade_uf_nome, unidade_codigo_ibge,
        orgao_subrogado_cnpj, orgao_subrogado_razao,
        unidade_subrogada_codigo, unidade_subrogada_nome,
        raw_json
    ) VALUES (
        %(numero_controle_pncp)s, %(ano_compra)s, %(numero_compra)s,
        %(sequencial_compra)s, %(processo)s,
        %(modalidade_id)s, %(modalidade_nome)s, %(situacao_compra_id)s, %(situacao_compra_nome)s,
        %(modo_disputa_id)s, %(modo_disputa_nome)s,
        %(objeto_compra)s, %(valor_total_estimado)s, %(valor_total_homologado)s,
        %(orcamento_sigiloso)s, %(srp)s,
        %(data_publicacao_pncp)s, %(data_inclusao)s, %(data_atualizacao)s, %(data_atualizacao_global)s,
        %(data_abertura_proposta)s, %(data_encerramento_proposta)s,
        %(amparo_legal_codigo)s, %(amparo_legal_nome)s, %(amparo_legal_descricao)s,
        %(tipo_instrumento_codigo)s, %(tipo_instrumento_nome)s,
        %(link_sistema_origem)s, %(link_processo_eletronico)s, %(informacao_complementar)s,
        %(justificativa_presencial)s, %(usuario_nome)s,
        %(orgao_cnpj)s, %(orgao_razao_social)s, %(orgao_poder_id)s, %(orgao_esfera_id)s,
        %(unidade_codigo)s, %(unidade_nome)s, %(unidade_municipio_nome)s,
        %(unidade_uf_sigla)s, %(unidade_uf_nome)s, %(unidade_codigo_ibge)s,
        %(orgao_subrogado_cnpj)s, %(orgao_subrogado_razao)s,
        %(unidade_subrogada_codigo)s, %(unidade_subrogada_nome)s,
        %(raw_json)s
    )
    ON CONFLICT (numero_controle_pncp) DO UPDATE SET
        situacao_compra_id = EXCLUDED.situacao_compra_id,
        situacao_compra_nome = EXCLUDED.situacao_compra_nome,
        valor_total_homologado = EXCLUDED.valor_total_homologado,
        data_encerramento_proposta = EXCLUDED.data_encerramento_proposta,
        data_atualizacao = EXCLUDED.data_atualizacao,
        data_atualizacao_global = EXCLUDED.data_atualizacao_global,
        informacao_complementar = EXCLUDED.informacao_complementar,
        link_processo_eletronico = EXCLUDED.link_processo_eletronico,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW()
    """
    
    params = {
        "numero_controle_pncp": item.get("numeroControlePNCP"),
        "ano_compra": item.get("anoCompra"),
        "numero_compra": item.get("numeroCompra"),
        "sequencial_compra": item.get("sequencialCompra"),
        "processo": item.get("processo"),
        "modalidade_id": item.get("modalidadeId"),
        "modalidade_nome": item.get("modalidadeNome"),
        "situacao_compra_id": item.get("situacaoCompraId"),
        "situacao_compra_nome": item.get("situacaoCompraNome"),
        "modo_disputa_id": item.get("modoDisputaId"),
        "modo_disputa_nome": item.get("modoDisputaNome"),
        "objeto_compra": item.get("objetoCompra"),
        "valor_total_estimado": item.get("valorTotalEstimado"),
        "valor_total_homologado": item.get("valorTotalHomologado"),
        "orcamento_sigiloso": item.get("orcamentoSigiloso", False),
        "srp": item.get("srp", False),
        "data_publicacao_pncp": item.get("dataPublicacaoPncp"),
        "data_inclusao": item.get("dataInclusao"),
        "data_atualizacao": item.get("dataAtualizacao"),
        "data_atualizacao_global": item.get("dataAtualizacaoGlobal"),
        "data_abertura_proposta": item.get("dataAberturaProposta"),
        "data_encerramento_proposta": item.get("dataEncerramentoProposta"),
        "amparo_legal_codigo": amparo.get("codigo"),
        "amparo_legal_nome": amparo.get("nome"),
        "amparo_legal_descricao": amparo.get("descricao"),
        "tipo_instrumento_codigo": item.get("tipoInstrumentoConvocatorioCodigo"),
        "tipo_instrumento_nome": instrumento,
        "link_sistema_origem": item.get("linkSistemaOrigem"),
        "link_processo_eletronico": item.get("linkProcessoEletronico"),
        "informacao_complementar": item.get("informacaoComplementar"),
        "justificativa_presencial": item.get("justificativaPresencial"),
        "usuario_nome": item.get("usuarioNome"),
        "orgao_cnpj": orgao.get("cnpj"),
        "orgao_razao_social": orgao.get("razaoSocial"),
        "orgao_poder_id": orgao.get("poderId"),
        "orgao_esfera_id": orgao.get("esferaId"),
        "unidade_codigo": unidade.get("codigoUnidade"),
        "unidade_nome": unidade.get("nomeUnidade"),
        "unidade_municipio_nome": unidade.get("municipioNome"),
        "unidade_uf_sigla": unidade.get("ufSigla"),
        "unidade_uf_nome": unidade.get("ufNome"),
        "unidade_codigo_ibge": unidade.get("codigoIbge"),
        "orgao_subrogado_cnpj": orgao_sub.get("cnpj") if orgao_sub else None,
        "orgao_subrogado_razao": orgao_sub.get("razaoSocial") if orgao_sub else None,
        "unidade_subrogada_codigo": unidade_sub.get("codigoUnidade") if unidade_sub else None,
        "unidade_subrogada_nome": unidade_sub.get("nomeUnidade") if unidade_sub else None,
        "raw_json": json.dumps(item, ensure_ascii=False, default=str),
    }
    
    cur.execute(sql, params)
    return "insert" if cur.rowcount == 1 else "update"


def sync_batch():
    """Executa um batch de 200 registros"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Obter cursor atual
    cur.execute("SELECT last_data, last_page FROM sync_cursor WHERE id = 1")
    state = cur.fetchone()
    
    current_date = state["last_data"] if state["last_data"] else date.today()
    current_page = state["last_page"] if state["last_page"] else 1
    
    # Janela de 7 dias a partir da data atual
    data_final = current_date
    data_inicial = current_date - timedelta(days=7)
    
    log.info(f"Sync: {data_inicial} → {data_final}, página {current_page}")
    
    total_inseridos = 0
    total_atualizados = 0
    records_processed = 0
    
    # Registrar início do sync
    cur.execute("""
        INSERT INTO sync_log (modalidade_id, data_inicial, data_final, pagina, status)
        VALUES (%s, %s, %s, %s, 'running')
        RETURNING id
    """, (6, data_inicial, data_final, current_page))
    log_id = cur.fetchone()["id"]
    conn.commit()
    
    pagina = current_page
    next_date = data_inicial  # fallback se esgotar as páginas
    
    while records_processed < BATCH_SIZE:
        data_str_ini = data_inicial.strftime("%Y%m%d")
        data_str_fim = data_final.strftime("%Y%m%d")
        
        data = fetch_page(6, data_str_ini, data_str_fim, pagina)
        
        if not data or not data.get("data"):
            # Sem mais dados nesta janela, avançar para janela anterior
            log.info(f"Janela {data_str_ini}-{data_str_fim} esgotada. Recuando 7 dias.")
            data_final = data_inicial - timedelta(days=1)
            data_inicial = data_final - timedelta(days=7)
            pagina = 1
            
            # Salvaguarda: não ir antes de 2021 (PNCP foi criado em 2021)
            if data_final.year < 2021:
                log.info("Alcançou o limite histórico (2021). Reiniciando do presente.")
                cur.execute("""
                    UPDATE sync_cursor SET last_data = %s, last_page = 1, updated_at = NOW()
                    WHERE id = 1
                """, (date.today(),))
                conn.commit()
                break
            continue
        
        total_paginas = data.get("totalPaginas", 1)
        total_registros = data.get("totalRegistros", 0)
        
        log.info(f"Página {pagina}/{total_paginas} | {len(data['data'])} registros")
        
        for item in data["data"]:
            try:
                result = upsert_contratacao(cur, item)
                conn.commit()
                if result == "insert":
                    total_inseridos += 1
                else:
                    total_atualizados += 1
                records_processed += 1
                
                if records_processed >= BATCH_SIZE:
                    break
            except Exception as e:
                log.error(f"Erro ao inserir {item.get('numeroControlePNCP')}: {e}")
                conn.rollback()
        
        # Avançar página ou janela
        if pagina < total_paginas and records_processed < BATCH_SIZE:
            pagina += 1
        else:
            # Salvar posição atual e avançar janela
            if pagina >= total_paginas:
                data_final = data_inicial - timedelta(days=1)
                data_inicial = data_final - timedelta(days=7)
                pagina = 1
            break
        
        time.sleep(0.3)  # Respeito à API
    
    # Atualizar cursor
    cur.execute("""
        UPDATE sync_cursor SET last_data = %s, last_page = %s, updated_at = NOW()
        WHERE id = 1
    """, (data_inicial, pagina))
    
    # Finalizar log
    tp = total_paginas if isinstance(total_paginas, int) else 0
    tr = total_registros if isinstance(total_registros, int) else 0
    cur.execute("""
        UPDATE sync_log SET 
            finalizado_em = NOW(),
            total_paginas = %s,
            total_registros = %s,
            registros_inseridos = %s,
            registros_atualizados = %s,
            status = 'success'
        WHERE id = %s
    """, (tp, tr, total_inseridos, total_atualizados, log_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    log.info(f"✅ Batch concluído: +{total_inseridos} inseridos, ~{total_atualizados} atualizados")
    return total_inseridos, total_atualizados


if __name__ == "__main__":
    log.info("🚀 Iniciando sync PNCP...")
    inserted, updated = sync_batch()
    log.info(f"Done. Inseridos: {inserted}, Atualizados: {updated}")
