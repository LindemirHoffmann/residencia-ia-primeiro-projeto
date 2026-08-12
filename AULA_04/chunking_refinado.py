"""
chunking_refinado.py
--------------------
Comparação de 10 estratégias de chunking com overlap calibrado,
usando os documentos Markdown gerados por converter_pdfs.py.

Requer: pip install openai langchain-text-splitters numpy pandas matplotlib python-dotenv
"""

import os
import glob
import time
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

# ------------------------------------------------------------
# Configuração
# ------------------------------------------------------------
# Carrega .env da raiz do projeto (dois níveis acima de AULA 04)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)
MAX_CHARS       = 6000
EMBEDDING_MODEL = "openai/text-embedding-3-small"

BASE_DIR  = Path(__file__).resolve().parent
PASTA_MD  = BASE_DIR / "documentos"

# Queries voltadas para os temas dos artigos
QUERIES = [
    "O que é o mecanismo de atenção (attention mechanism) em modelos de linguagem?",
    "Como funciona o fine-tuning com RLHF (Reinforcement Learning from Human Feedback)?",
    "O que são scaling laws e como elas influenciam o desempenho de LLMs?",
]


# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------
def limpar_texto(texto: str) -> str:
    """Remove hifens de quebra de linha herdados do PDF."""
    return re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)


def get_embedding(texto: str):
    texto = str(texto)[:MAX_CHARS]
    resp  = client.embeddings.create(input=texto, model=EMBEDDING_MODEL)
    return resp.data[0].embedding


def similaridade_cosseno(a, b):
    a, b  = np.array(a), np.array(b)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))


def busca_semantica(query: str, chunks: list, top_k: int = 3):
    vec_q     = get_embedding(query)
    resultados = []
    batch_size = 10

    for i in range(0, len(chunks), batch_size):
        lote = [str(c)[:MAX_CHARS] for c in chunks[i:i + batch_size]]
        resp = client.embeddings.create(input=lote, model=EMBEDDING_MODEL)
        for j, dado in enumerate(resp.data):
            sim = similaridade_cosseno(vec_q, dado.embedding)
            resultados.append({"Trecho": chunks[i + j], "Similaridade": sim})
        if i + batch_size < len(chunks):
            time.sleep(1)

    resultados.sort(key=lambda x: x["Similaridade"], reverse=True)
    return resultados[:top_k]


def estatisticas_chunks(chunks: list) -> dict:
    tamanhos = [len(str(c)) for c in chunks]
    if not tamanhos:
        return {"total": 0, "media": 0, "min": 0, "max": 0}
    return {
        "total": len(chunks),
        "media": int(np.mean(tamanhos)),
        "min":   min(tamanhos),
        "max":   max(tamanhos),
    }


# ------------------------------------------------------------
# Carregamento dos documentos
# ------------------------------------------------------------
def carregar_documentos() -> str:
    caminhos = sorted(PASTA_MD.glob("*.md"))
    if not caminhos:
        raise FileNotFoundError(
            f"Nenhum .md encontrado em {PASTA_MD}.\n"
            "Execute primeiro: python converter_pdfs.py"
        )
    textos = []
    for c in caminhos:
        with open(c, encoding="utf-8") as f:
            textos.append(f.read())
    print(f"Carregados {len(textos)} documentos Markdown.")
    texto = "\n\n".join(textos)
    texto = limpar_texto(texto)
    print(f"Total: {len(texto):,} caracteres\n")
    return texto


# ------------------------------------------------------------
# Definição das 10 estratégias calibradas
# ------------------------------------------------------------
def definir_estrategias() -> list:
    return [
        # --- Fixo (CharacterTextSplitter) ---
        {
            "grupo": 1, "tipo": "texto",
            "nome": "Fixo 256, sem overlap",
            "variavel": "baseline mínimo",
            "splitter": CharacterTextSplitter(separator="", chunk_size=256, chunk_overlap=0),
        },
        {
            "grupo": 2, "tipo": "texto",
            "nome": "Fixo 512, sem overlap",
            "variavel": "tamanho padrão RAG",
            "splitter": CharacterTextSplitter(separator="", chunk_size=512, chunk_overlap=0),
        },
        {
            "grupo": 3, "tipo": "texto",
            "nome": "Fixo 1024, sem overlap",
            "variavel": "bloco maior",
            "splitter": CharacterTextSplitter(separator="", chunk_size=1024, chunk_overlap=0),
        },
        # --- Fixo com overlaps calibrados ---
        {
            "grupo": 4, "tipo": "texto",
            "nome": "Fixo 512, overlap 64 (12%)",
            "variavel": "overlap leve",
            "splitter": CharacterTextSplitter(separator="", chunk_size=512, chunk_overlap=64),
        },
        {
            "grupo": 5, "tipo": "texto",
            "nome": "Fixo 512, overlap 128 (25%)",
            "variavel": "overlap moderado",
            "splitter": CharacterTextSplitter(separator="", chunk_size=512, chunk_overlap=128),
        },
        {
            "grupo": 6, "tipo": "texto",
            "nome": "Fixo 512, overlap 256 (50%)",
            "variavel": "overlap pesado",
            "splitter": CharacterTextSplitter(separator="", chunk_size=512, chunk_overlap=256),
        },
        # --- Recursivo com overlaps calibrados ---
        {
            "grupo": 7, "tipo": "texto",
            "nome": "Recursivo 512, overlap 64",
            "variavel": "recursivo leve",
            "splitter": RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64),
        },
        {
            "grupo": 8, "tipo": "texto",
            "nome": "Recursivo 512, overlap 128",
            "variavel": "recursivo moderado",
            "splitter": RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=128),
        },
        {
            "grupo": 9, "tipo": "texto",
            "nome": "Recursivo 1024, overlap 128",
            "variavel": "recursivo grande",
            "splitter": RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128),
        },
        # --- Estrutura Markdown ---
        {
            "grupo": 10, "tipo": "markdown",
            "nome": "Por seção/heading Markdown",
            "variavel": "estrutura semântica",
            "splitter": MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
            ),
        },
    ]


# ------------------------------------------------------------
# Execução principal
# ------------------------------------------------------------
def main():
    texto = carregar_documentos()
    estrategias = definir_estrategias()
    resultados_finais = []

    for est in estrategias:
        grupo   = est["grupo"]
        nome    = est["nome"]
        variavel = est["variavel"]
        splitter = est["splitter"]

        print("=" * 72)
        print(f"GRUPO {grupo}: {nome}")
        print(f"Variável: {variavel}")
        print("=" * 72)

        # Dividir texto em chunks
        try:
            if est["tipo"] == "markdown":
                docs   = splitter.split_text(texto)
                chunks = [d.page_content for d in docs if d.page_content.strip()]
            else:
                chunks = [c for c in splitter.split_text(texto) if c.strip()]
        except Exception as e:
            print(f"  ERRO ao dividir: {e}\n")
            continue

        chunks = [c for c in chunks if len(c.strip()) >= 20]
        stats  = estatisticas_chunks(chunks)
        print(f"  Chunks: {stats['total']} | "
              f"Média: {stats['media']} chars | "
              f"Min: {stats['min']} | Max: {stats['max']}")

        # Busca semântica para cada query
        sims = []
        for qi, query in enumerate(QUERIES, 1):
            print(f"\n  Query {qi}: {query}")
            try:
                top = busca_semantica(query, chunks, top_k=3)
                melhor = top[0]["Similaridade"] if top else 0.0
                sims.append(melhor)
                for idx, r in enumerate(top, 1):
                    preview = " ".join(r["Trecho"].split())[:180]
                    print(f"    TOP {idx} (sim={r['Similaridade']:.4f}): {preview}...")
            except Exception as e:
                print(f"    ERRO na busca: {e}")
                sims.append(0.0)

        media = round(np.mean(sims), 4) if sims else 0.0
        resultados_finais.append({
            "Grupo":     grupo,
            "Estratégia": nome,
            "Variável":  variavel,
            "Chunks":    stats["total"],
            "Tam.Médio": stats["media"],
            "Sim Q1":    round(sims[0], 4) if len(sims) > 0 else 0.0,
            "Sim Q2":    round(sims[1], 4) if len(sims) > 1 else 0.0,
            "Sim Q3":    round(sims[2], 4) if len(sims) > 2 else 0.0,
            "Média":     media,
        })
        print()

    # ----------------------------------------------------------
    # Tabela comparativa
    # ----------------------------------------------------------
    df = pd.DataFrame(resultados_finais).sort_values("Média", ascending=False)
    print("\n" + "=" * 72)
    print("TABELA COMPARATIVA FINAL (ordenada por Média de Similaridade)")
    print("=" * 72)
    print(df.to_string(index=False))

    # ----------------------------------------------------------
    # Gráfico de barras
    # ----------------------------------------------------------
    df_plot = pd.DataFrame(resultados_finais).sort_values("Grupo")
    x      = np.arange(len(df_plot))
    w      = 0.2
    cores  = ["#4285F4", "#EA4335", "#FBBC04", "#34A853"]

    fig, ax = plt.subplots(figsize=(16, 6))
    ax.bar(x - 1.5*w, df_plot["Sim Q1"], w, label="Q1 – Atenção",       color=cores[0])
    ax.bar(x - 0.5*w, df_plot["Sim Q2"], w, label="Q2 – RLHF",          color=cores[1])
    ax.bar(x + 0.5*w, df_plot["Sim Q3"], w, label="Q3 – Scaling Laws",   color=cores[2])
    ax.bar(x + 1.5*w, df_plot["Média"],  w, label="Média",               color=cores[3])

    ax.set_xticks(x)
    ax.set_xticklabels([f"G{int(g)}" for g in df_plot["Grupo"]], fontsize=9)
    ax.set_xlabel("Estratégia de Chunking")
    ax.set_ylabel("Similaridade Cosseno")
    ax.set_title("Chunking Refinado — 10 Estratégias com Overlap Calibrado")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Legenda com nomes completos abaixo do gráfico
    legenda = " | ".join([f"G{int(r['Grupo'])}: {r['Estratégia']}" for _, r in df_plot.iterrows()])
    fig.text(0.5, -0.04, legenda, ha="center", fontsize=7, family="monospace", wrap=True)

    plt.tight_layout()

    saida_png = BASE_DIR / "chunking_refinado_resultado.png"
    plt.savefig(saida_png, dpi=150, bbox_inches="tight")
    print(f"\nGráfico salvo em: {saida_png}")
    plt.show()


if __name__ == "__main__":
    main()
