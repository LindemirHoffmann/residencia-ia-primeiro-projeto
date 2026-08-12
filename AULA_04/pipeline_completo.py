"""
pipeline_completo.py
--------------------
Pipeline: PDF → Markdown → 10 Estratégias de Chunking → Embeddings → JSON

Estrutura de saída:
  results/
  ├── <documento>/
  │   ├── markdown/<documento>.md
  │   ├── test_01/chunks_embeddings.json
  │   ├── ...
  │   └── test_10/chunks_embeddings.json
  └── summary.json

Requer:
  pip install openai langchain-text-splitters pymupdf4llm numpy python-dotenv sentence-transformers
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

try:
    import pymupdf4llm
except ImportError:
    raise ImportError("Instale com: pip install pymupdf4llm")

# Corrige encoding do terminal Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(errors="replace")

# ─────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO — escolha do modelo de embedding
#
#   USE_HUGGINGFACE = True  → roda LOCAL, 100% gratuito
#                             modelo: all-MiniLM-L6-v2 (384 dims)
#
#   USE_HUGGINGFACE = False → usa OpenRouter API (requer créditos)
#                             modelo: text-embedding-3-small (1536 dims)
# ─────────────────────────────────────────────────────────────────
USE_HUGGINGFACE = True   # <── mude para False para usar OpenRouter

HF_MODEL      = "sentence-transformers/all-MiniLM-L6-v2"
OR_MODEL      = "openai/text-embedding-3-small"
BATCH_SIZE    = 64   # maior batch = mais rápido no HuggingFace local
SLEEP_BETWEEN = 0.5  # segundos entre batches (só relevante no OpenRouter)
MAX_CHARS     = 6000

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ── Inicializa modelo ──────────────────────────────────────────────
if USE_HUGGINGFACE:
    from sentence_transformers import SentenceTransformer
    print("[Embedding] Carregando modelo HuggingFace:", HF_MODEL)
    _hf_model = SentenceTransformer(HF_MODEL)
    EMBEDDING_DIM   = _hf_model.get_sentence_embedding_dimension()
    EMBEDDING_MODEL = HF_MODEL
    print(f"[Embedding] OK! Dimensao: {EMBEDDING_DIM}")
else:
    from openai import OpenAI
    _or_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
    )
    EMBEDDING_DIM   = 1536
    EMBEDDING_MODEL = OR_MODEL

BASE_DIR   = Path(__file__).resolve().parent
PASTA_PDF  = BASE_DIR / "arquivos"
PASTA_DOCS = BASE_DIR / "documentos"
PASTA_RES  = BASE_DIR          # resultados salvos direto em AULA_04/
PASTA_DOCS.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# Limpeza de texto extraído de PDF
# ─────────────────────────────────────────────
def limpar_texto(texto: str) -> str:
    texto = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)
    linhas = [l for l in texto.splitlines() if len(l.strip()) > 4 or l.strip() == ""]
    return "\n".join(linhas)


# ─────────────────────────────────────────────
# Conversão PDF → Markdown
# ─────────────────────────────────────────────
def converter_pdf(pdf_path: Path, pasta_md: Path) -> Path:
    nome_md = pasta_md / (pdf_path.stem + ".md")
    if nome_md.exists():
        print(f"    [Markdown] Ja existe: {nome_md.name}")
        return nome_md

    print(f"    [Markdown] Convertendo {pdf_path.name}...", end=" ")
    md = pymupdf4llm.to_markdown(str(pdf_path))
    md = limpar_texto(md)
    titulo = pdf_path.stem.replace("_", " ").title()
    with open(nome_md, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n{md}")
    print(f"OK ({nome_md.stat().st_size // 1024} KB)")
    return nome_md


# ─────────────────────────────────────────────
# Estratégia 8 — Por sentença, agrupando 3
# ─────────────────────────────────────────────
def split_por_sentencas_agrupadas(texto: str, n: int = 3) -> list:
    sentencas = re.split(r"(?<=[.!?])\s+", texto.strip())
    sentencas = [s.strip() for s in sentencas if len(s.strip()) > 10]
    chunks = []
    for i in range(0, len(sentencas), n):
        grupo = sentencas[i:i + n]
        chunks.append(" ".join(grupo))
    return [c for c in chunks if len(c) > 10]


# ─────────────────────────────────────────────
# Definição das 10 estratégias
# ─────────────────────────────────────────────
ESTRATEGIAS = [
    {
        "test_id": 1, "tipo": "texto",
        "strategy": "fixed_200_no_overlap",
        "nome": "Fixo 200 chars, sem overlap",
        "chunk_size": 200, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(separator="", chunk_size=200, chunk_overlap=0),
    },
    {
        "test_id": 2, "tipo": "texto",
        "strategy": "fixed_500_no_overlap",
        "nome": "Fixo 500 chars, sem overlap",
        "chunk_size": 500, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=0),
    },
    {
        "test_id": 3, "tipo": "texto",
        "strategy": "fixed_1000_no_overlap",
        "nome": "Fixo 1000 chars, sem overlap",
        "chunk_size": 1000, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(separator="", chunk_size=1000, chunk_overlap=0),
    },
    {
        "test_id": 4, "tipo": "texto",
        "strategy": "fixed_2000_no_overlap",
        "nome": "Fixo 2000 chars, sem overlap",
        "chunk_size": 2000, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(separator="", chunk_size=2000, chunk_overlap=0),
    },
    {
        "test_id": 5, "tipo": "texto",
        "strategy": "fixed_500_overlap_50",
        "nome": "Fixo 500 chars, overlap 50",
        "chunk_size": 500, "chunk_overlap": 50,
        "splitter": CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=50),
    },
    {
        "test_id": 6, "tipo": "texto",
        "strategy": "fixed_500_overlap_200",
        "nome": "Fixo 500 chars, overlap 200",
        "chunk_size": 500, "chunk_overlap": 200,
        "splitter": CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=200),
    },
    {
        "test_id": 7, "tipo": "paragrafo",
        "strategy": "by_paragraph",
        "nome": "Por paragrafo",
        "chunk_size": 5000, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(
            separator="\n\n", chunk_size=5000, chunk_overlap=0, is_separator_regex=False
        ),
    },
    {
        "test_id": 8, "tipo": "sentenca",
        "strategy": "by_sentence_grouped_3",
        "nome": "Por sentenca (3 agrupadas)",
        "chunk_size": None, "chunk_overlap": 0,
        "splitter": None,
    },
    {
        "test_id": 9, "tipo": "texto",
        "strategy": "recursive_hierarchical",
        "nome": "Recursivo hierarquico",
        "chunk_size": 500, "chunk_overlap": 50,
        "splitter": RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            chunk_size=500, chunk_overlap=50,
        ),
    },
    {
        "test_id": 10, "tipo": "markdown",
        "strategy": "markdown_headers",
        "nome": "Markdown headers (H1/H2/H3)",
        "chunk_size": None, "chunk_overlap": 0,
        "splitter": MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        ),
    },
]


# ─────────────────────────────────────────────
# Geração de embeddings (HuggingFace ou OpenRouter)
# ─────────────────────────────────────────────
def gerar_embeddings(textos: list) -> list:
    if USE_HUGGINGFACE:
        # Roda localmente — rápido, sem custo
        vetores = _hf_model.encode(
            textos,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return vetores.tolist()
    else:
        # OpenRouter API — requer créditos
        vetores = []
        for i in range(0, len(textos), BATCH_SIZE):
            batch = [str(t)[:MAX_CHARS] for t in textos[i:i + BATCH_SIZE]]
            for tentativa in range(3):
                try:
                    resp = _or_client.embeddings.create(input=batch, model=OR_MODEL)
                    vetores.extend([d.embedding for d in resp.data])
                    break
                except Exception as e:
                    if tentativa < 2:
                        print(f"      [API] Erro ({e}), tentando novamente...")
                        time.sleep(5)
                    else:
                        print(f"      [API] Falha: {e}")
                        vetores.extend([[0.0] * EMBEDDING_DIM] * len(batch))
            if i + BATCH_SIZE < len(textos):
                time.sleep(SLEEP_BETWEEN)
        return vetores


# ─────────────────────────────────────────────
# Dividir texto em chunks
# ─────────────────────────────────────────────
def dividir_chunks(texto: str, est: dict) -> list:
    tipo = est["tipo"]

    if tipo == "sentenca":
        textos = split_por_sentencas_agrupadas(texto, n=3)
        return [{"text": t, "metadata": {}} for t in textos if t.strip()]

    if tipo == "markdown":
        docs = est["splitter"].split_text(texto)
        return [
            {"text": doc.page_content, "metadata": dict(doc.metadata)}
            for doc in docs if doc.page_content.strip()
        ]

    textos = est["splitter"].split_text(texto)
    return [{"text": t, "metadata": {}} for t in textos if t.strip() and len(t) >= 10]


# ─────────────────────────────────────────────
# Processar 1 documento × 1 estratégia
# ─────────────────────────────────────────────
def processar(doc_id: str, doc_nome: str, texto: str, est: dict, pasta_doc: Path) -> dict:
    test_id    = est["test_id"]
    pasta_test = pasta_doc / f"test_{test_id:02d}"
    json_path  = pasta_test / "chunks_embeddings.json"

    if json_path.exists():
        print(f"      [Teste {test_id:02d}] Ja existe, pulando.")
        with open(json_path, encoding="utf-8") as f:
            dados = json.load(f)
        sizes   = [len(d["text"]) for d in dados]
        emb_dim = len(dados[0]["embedding"]) if dados else 0
        return {
            "test_id": test_id, "strategy": est["strategy"],
            "chunk_size": est["chunk_size"], "chunk_overlap": est["chunk_overlap"],
            "num_chunks": len(dados),
            "avg_chunk_size": round(np.mean(sizes), 1) if sizes else 0,
            "min_chunk_size": min(sizes) if sizes else 0,
            "max_chunk_size": max(sizes) if sizes else 0,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": emb_dim,
        }

    print(f"      [Teste {test_id:02d}] {est['nome']}")

    chunks = dividir_chunks(texto, est)
    if not chunks:
        print(f"        Nenhum chunk gerado.")
        return {}

    chunks = [c for c in chunks if len(c["text"].strip()) >= 10]
    print(f"        {len(chunks)} chunks")

    textos_para_emb = [c["text"] for c in chunks]
    vetores = gerar_embeddings(textos_para_emb)

    dados = []
    for idx, (chunk, vetor) in enumerate(zip(chunks, vetores), 1):
        dados.append({
            "chunk_id":      f"{doc_id}_test{test_id:02d}_chunk{idx:04d}",
            "document_id":   doc_id,
            "document_name": doc_nome,
            "test_id":       test_id,
            "strategy":      est["strategy"],
            "chunk_size":    est["chunk_size"],
            "chunk_overlap": est["chunk_overlap"],
            "text":          chunk["text"],
            "embedding":     vetor,
            "metadata": {
                "char_count":      len(chunk["text"]),
                "embedding_model": EMBEDDING_MODEL,
                **chunk["metadata"],
            },
        })

    pasta_test.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"        Salvo em {json_path.relative_to(BASE_DIR)}")

    sizes = [d["metadata"]["char_count"] for d in dados]
    return {
        "test_id": test_id, "strategy": est["strategy"],
        "chunk_size": est["chunk_size"], "chunk_overlap": est["chunk_overlap"],
        "num_chunks": len(dados),
        "avg_chunk_size": round(np.mean(sizes), 1),
        "min_chunk_size": min(sizes),
        "max_chunk_size": max(sizes),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": len(dados[0]["embedding"]) if dados else 0,
    }


# ─────────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────────
def main():
    print("=" * 70)
    print("PIPELINE COMPLETO — PDF -> Markdown -> Chunking -> Embeddings -> JSON")
    print(f"Modelo de embedding: {EMBEDDING_MODEL}")
    print("=" * 70)

    pdfs = sorted(PASTA_PDF.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em {PASTA_PDF}")
        return

    print(f"\nEncontrados {len(pdfs)} PDFs.\n")
    summary_docs = []

    for pdf_path in pdfs:
        doc_id   = re.sub(r"[^a-z0-9_]", "_", pdf_path.stem.lower())
        doc_nome = pdf_path.name
        print(f"\n{'='*60}")
        print(f"Documento: {doc_nome}")
        print(f"{'='*60}")

        pasta_doc = PASTA_RES / doc_id
        pasta_md  = pasta_doc / "markdown"
        pasta_md.mkdir(parents=True, exist_ok=True)

        md_path = converter_pdf(pdf_path, pasta_md)
        with open(md_path, encoding="utf-8") as f:
            texto = limpar_texto(f.read())
        print(f"    Texto: {len(texto):,} caracteres")

        experimentos = []
        for est in ESTRATEGIAS:
            try:
                resultado = processar(doc_id, doc_nome, texto, est, pasta_doc)
                if resultado:
                    experimentos.append(resultado)
            except Exception as e:
                print(f"      [Teste {est['test_id']:02d}] ERRO: {e}")

        summary_docs.append({
            "document_id":   doc_id,
            "document_name": doc_nome,
            "total_chars":   len(texto),
            "experiments":   experimentos,
        })

    # summary.json
    summary_path = PASTA_RES / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"embedding_model": EMBEDDING_MODEL, "documents": summary_docs},
                  f, ensure_ascii=False, indent=2)
    print(f"\nSummary salvo em: {summary_path}")

    # Tabela resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    for doc in summary_docs:
        print(f"\n{doc['document_name']}:")
        for exp in doc["experiments"]:
            print(f"  Teste {exp['test_id']:02d} | {exp['strategy']:<30} | "
                  f"Chunks: {exp['num_chunks']:5d} | Media: {exp['avg_chunk_size']:7.1f} chars")

    print("\nPipeline concluido!")


if __name__ == "__main__":
    main()
