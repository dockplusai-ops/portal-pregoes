#!/usr/bin/env python3
"""
Portal Pregões - Categorizador via Perplexity (sonar)
Classifica cada licitação em uma categoria para uso nos filtros da UI.

Uso:
  python3 categorizar.py                 # processa todos sem categoria
  python3 categorizar.py --limit 500     # processa apenas 500
  python3 categorizar.py --dry-run       # simula sem salvar
  python3 categorizar.py --recategorize  # reprocessa todos (inclusive já categorizados)
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import psycopg2
import psycopg2.extras

# ===== CONFIG =====
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dockplusai:k9mwqvbpth2fxnsd@82.25.86.197:5460/pregoes"
)
PPLX_API_KEY = os.getenv("PPLX_API_KEY", "")  # set via env var: export PPLX_API_KEY=pplx-...
PPLX_MODEL   = "sonar"
BATCH_SIZE   = 20     # licitações por requisição (reduz custo de request)
SLEEP_BATCH  = 1.0    # segundos entre requisições
MAX_TOKENS   = 80     # suficiente para JSON com 20 categorias

CATEGORIAS = [
    "TI & Telecom",
    "Saúde & Medicamentos",
    "Obras & Engenharia",
    "Serviços Gerais",
    "Mobiliário & Equipamentos",
    "Veículos & Transporte",
    "Alimentação",
    "Segurança & Vigilância",
    "Consultoria & Capacitação",
    "Limpeza & Conservação",
    "Material de Escritório",
    "Outros",
]
CATEGORIAS_STR = ", ".join(CATEGORIAS)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("categorizar")


def build_prompt(objetos: list[str]) -> str:
    itens = "\n".join(f"{i+1}. {o[:200]}" for i, o in enumerate(objetos))
    return (
        f"Classifique cada licitação em UMA das categorias abaixo. "
        f"Responda APENAS um JSON array com as categorias na mesma ordem.\n\n"
        f"Categorias: {CATEGORIAS_STR}\n\n"
        f"{itens}\n\n"
        f'Formato: ["cat1","cat2",...] (exatamente {len(objetos)} itens)'
    )


def classify_batch(objetos):  # list[str] -> list[str] | None
    """Envia um batch para a Perplexity e retorna lista de categorias."""
    prompt = build_prompt(objetos)
    payload = {
        "model": PPLX_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(3):
        try:
            r = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                # Extrair JSON do conteúdo (pode vir com markdown)
                if "```" in content:
                    content = content.split("```")[1].strip()
                    if content.startswith("json"):
                        content = content[4:].strip()
                parsed = json.loads(content)
                if isinstance(parsed, list) and len(parsed) == len(objetos):
                    # Validar que cada categoria é válida
                    result = []
                    for cat in parsed:
                        cat_clean = cat.strip().strip("*").strip()
                        if cat_clean in CATEGORIAS:
                            result.append(cat_clean)
                        else:
                            # Fuzzy match: ver se contém substring de alguma categoria
                            matched = next(
                                (c for c in CATEGORIAS if c.lower() in cat_clean.lower() or cat_clean.lower() in c.lower()),
                                "Outros"
                            )
                            result.append(matched)
                    return result
                else:
                    log.warning(f"Resposta inválida (len={len(parsed) if isinstance(parsed, list) else 'N/A'}): {content[:100]}")
            elif r.status_code == 429:
                log.warning("Rate limit, aguardando 10s...")
                time.sleep(10)
            else:
                log.error(f"HTTP {r.status_code}: {r.text[:200]}")
        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error (tentativa {attempt+1}): {e} — conteúdo: {content[:100]}")
        except Exception as e:
            log.error(f"Erro na requisição (tentativa {attempt+1}): {e}")
            time.sleep(2)

    return None


def run(limit=None, dry_run=False, recategorize=False):  # limit: int | None
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Buscar registros a categorizar
    where = "" if recategorize else "WHERE categoria IS NULL"
    limit_sql = f"LIMIT {limit}" if limit else ""
    cur.execute(f"""
        SELECT numero_controle_pncp, objeto_compra
        FROM contratacoes
        {where}
        ORDER BY data_publicacao_pncp DESC
        {limit_sql}
    """)
    rows = cur.fetchall()

    total = len(rows)
    log.info(f"Total a categorizar: {total}")
    if total == 0:
        log.info("Nada a fazer!")
        return

    total_cost = 0.0
    total_success = 0
    total_errors = 0

    # Processar em batches
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        objetos = [r["objeto_compra"] or "" for r in batch]
        ids = [r["numero_controle_pncp"] for r in batch]

        log.info(f"Batch {i//BATCH_SIZE + 1} — registros {i+1}–{min(i+BATCH_SIZE, total)}/{total}")

        categorias = classify_batch(objetos)

        if categorias is None:
            log.error(f"Falha no batch {i//BATCH_SIZE + 1}, pulando...")
            total_errors += len(batch)
            continue

        # Custo estimado: $0.005 por request + tokens
        total_cost += 0.005

        if dry_run:
            for j, (id_, cat) in enumerate(zip(ids, categorias)):
                log.info(f"  [DRY] {id_} → {cat}")
        else:
            # Update em batch
            update_data = [(cat, id_) for id_, cat in zip(ids, categorias)]
            psycopg2.extras.execute_batch(
                cur,
                "UPDATE contratacoes SET categoria = %s WHERE numero_controle_pncp = %s",
                update_data,
                page_size=BATCH_SIZE
            )
            conn.commit()

        total_success += len(batch)
        log.info(f"  ✅ {len(batch)} categorizados | custo acumulado: ~${total_cost:.3f}")

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_BATCH)

    cur.close()
    conn.close()

    log.info("=" * 50)
    log.info(f"Concluído: {total_success} sucesso, {total_errors} erros")
    log.info(f"Custo estimado total: ~${total_cost:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categoriza licitações via Perplexity")
    parser.add_argument("--limit", type=int, default=None, help="Máximo de registros a processar")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar no banco")
    parser.add_argument("--recategorize", action="store_true", help="Reprocessa já categorizados")
    args = parser.parse_args()

    run(limit=args.limit, dry_run=args.dry_run, recategorize=args.recategorize)
