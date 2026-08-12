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
  pip install openai langchain-text-splitters pymupdf4llm numpy python-dotenv
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
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

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
)

BASE_DIR    = Path(__file__).resolve().parent
PASTA_PDF   = BASE_DIR / "arquivos"
PASTA_DOCS  = BASE_DIR / "documentos"
PASTA_RES   = BASE_DIR / "results"
PASTA_DOCS.mkdir(exist_ok=True)
PASTA_RES.mkdir(exist_ok=True)

MAX_CHARS       = 6000
EMBEDDING_MODEL = "openai/text-embedding-3-small"
BATCH_SIZE      = 20   # chunks por chamada à API
SLEEP_BETWEEN   = 1.5  # segundos entre batches


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
        print(f"    [Markdown] Já existe: {nome_md.name}")
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
        "nome": "Por parágrafo",
        "chunk_size": 5000, "chunk_overlap": 0,
        "splitter": CharacterTextSplitter(
            separator="\n\n", chunk_size=5000, chunk_overlap=0, is_separator_regex=False
        ),
    },
    {
        "test_id": 8, "tipo": "sentenca",
        "strategy": "by_sentence_grouped_3",
        "nome": "Por sentença (3 agrupadas)",
        "chunk_size": None, "chunk_overlap": 0,
        "splitter": None,  # usa split_por_sentencas_agrupadas()
    },
    {
        "test_id": 9, "tipo": "texto",
        "strategy": "recursive_hierarchical",
        "nome": "Recursivo hierárquico",
        "chunk_size": 500, "chunk_overlap": 50,
        "splitter": RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            chunk_size=500, chunk_overlap=50,
        ),
    },
    {
        "test_id": 10, "tipo": "markdown",
        "strategy": "markdown_headers",
        "nome": "Markdown headers (H1, H2, H3)",
        "chunk_size": None, "chunk_overlap": 0,
        "splitter": MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        ),
    },
]


# ─────────────────────────────────────────────
# Dividir texto em chunks
# ─────────────────────────────────────────────
def dividir_chunks(texto: str, est: dict) -> list:
    """Retorna lista de dicts com 'text' e 'metadata'."""
    tipo = est["tipo"]

    if tipo == "sentenca":
        textos = split_por_sentencas_agrupadas(texto, n=3)
        return [{"text": t, "metadata": {}} for t in textos if t.strip()]

    if tipo == "markdown":
        docs = est["splitter"].split_text(texto)
        resultados = []
        for doc in docs:
            if not doc.page_content.strip():
                continue
            meta = {k: v for k, v in doc.metadata.items()}
            resultados.append({"text": doc.page_content, "metadata": meta})
        return resultados

    # fixo / parágrafo / recursivo
    textos = est["splitter"].split_text(texto)
    return [{"text": t, "metadata": {}} for t in textos if t.strip() and len(t) >= 10]


# ─────────────────────────────────────────────
# Geração de embeddings via OpenRouter
# ─────────────────────────────────────────────
def gerar_embeddings(textos: list, sleep_s: float = SLEEP_BETWEEN) -> list:
    """Gera embeddings em batches, com retry simples."""
    vetores = []
    for i in range(0, len(textos), BATCH_SIZE):
        batch = [str(t)[:MAX_CHARS] for t in textos[i:i + BATCH_SIZE]]
        tentativas = 3
        for t in range(tentativas):
            try:
                resp = client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
                vetores.extend([d.embedding for d in resp.data])
                break
            except Exception as e:
                if t < tentativas - 1:
                    print(f"      [API] Erro ({e}), tentando novamente...")
                    time.sleep(5)
                else:
                    print(f"      [API] Falha após {tentativas} tentativas: {e}")
                    vetores.extend([[0.0] * 1536] * len(batch))

        if i + BATCH_SIZE < len(textos):
            time.sleep(sleep_s)

    return vetores


# ─────────────────────────────────────────────
# Salvar chunks + embeddings em JSON
# ─────────────────────────────────────────────
def salvar_json(chunks_data: list, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Processar 1 documento × 1 estratégia
# ─────────────────────────────────────────────
def processar(doc_id: str, doc_nome: str, texto: str, est: dict, pasta_doc: Path) -> dict:
    test_id  = est["test_id"]
    pasta_test = pasta_doc / f"test_{test_id:02d}"
    json_path  = pasta_test / "chunks_embeddings.json"

    if json_path.exists():
        print(f"      [Teste {test_id:02d}] Já existe, pulando.")
        # Lê estatísticas do arquivo existente
        with open(json_path, encoding="utf-8") as f:
            dados = json.load(f)
        sizes = [len(d["text"]) for d in dados]
        emb_dim = len(dados[0]["embedding"]) if dados else 0
        return {
            "test_id": test_id,
            "strategy": est["strategy"],
            "chunk_size": est["chunk_size"],
            "chunk_overlap": est["chunk_overlap"],
            "num_chunks": len(dados),
            "avg_chunk_size": round(np.mean(sizes), 1) if sizes else 0,
            "min_chunk_size": min(sizes) if sizes else 0,
            "max_chunk_size": max(sizes) if sizes else 0,
            "embedding_dimension": emb_dim,
        }

    print(f"      [Teste {test_id:02d}] {est['nome']}")

    # 1. Dividir
    chunks = dividir_chunks(texto, est)
    if not chunks:
        print(f"        → Nenhum chunk gerado.")
        return {}

    print(f"        → {len(chunks)} chunks gerados")

    # 2. Gerar embeddings
    textos_para_embedding = [c["text"] for c in chunks]
    vetores = gerar_embeddings(textos_para_embedding)

    # 3. Montar estrutura
    dados = []
    for idx, (chunk, vetor) in enumerate(zip(chunks, vetores), 1):
        chunk_id = f"{doc_id}_test{test_id:02d}_chunk{idx:04d}"
        tamanho  = len(chunk["text"])
        dados.append({
            "chunk_id":      chunk_id,
            "document_id":   doc_id,
            "document_name": doc_nome,
            "test_id":       test_id,
            "strategy":      est["strategy"],
            "chunk_size":    est["chunk_size"],
            "chunk_overlap": est["chunk_overlap"],
            "text":          chunk["text"],
            "embedding":     vetor,
            "metadata": {
                "char_count": tamanho,
                **chunk["metadata"],
            },
        })

    # 4. Salvar
    salvar_json(dados, json_path)
    print(f"        → Salvo em {json_path.relative_to(BASE_DIR)}")

    sizes = [d["metadata"]["char_count"] for d in dados]
    emb_dim = len(dados[0]["embedding"]) if dados else 0

    return {
        "test_id":           test_id,
        "strategy":          est["strategy"],
        "chunk_size":        est["chunk_size"],
        "chunk_overlap":     est["chunk_overlap"],
        "num_chunks":        len(dados),
        "avg_chunk_size":    round(np.mean(sizes), 1),
        "min_chunk_size":    min(sizes),
        "max_chunk_size":    max(sizes),
        "embedding_dimension": emb_dim,
    }


# ─────────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────────
def main():
    print("=" * 72)
    print("PIPELINE COMPLETO — PDF → Markdown → Chunking → Embeddings → JSON")
    print("=" * 72)

    # Descobrir PDFs
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

        # Pastas de saída
        pasta_doc = PASTA_RES / doc_id
        pasta_md  = pasta_doc / "markdown"
        pasta_md.mkdir(parents=True, exist_ok=True)

        # 1. PDF → Markdown
        md_path = converter_pdf(pdf_path, pasta_md)
        with open(md_path, encoding="utf-8") as f:
            texto = limpar_texto(f.read())

        print(f"    Texto: {len(texto):,} caracteres")

        # 2. 10 estratégias
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

    # 3. summary.json
    summary_path = PASTA_RES / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"documents": summary_docs}, f, ensure_ascii=False, indent=2)
    print(f"\n\nSummary salvo em: {summary_path}")

    # 4. Imprime tabela resumo
    print("\n" + "=" * 72)
    print("RESUMO POR ESTRATÉGIA (todos os documentos)")
    print("=" * 72)
    for doc in summary_docs:
        print(f"\n{doc['document_name']}:")
        for exp in doc["experiments"]:
            print(
                f"  Teste {exp['test_id']:02d} | {exp['strategy']:<30} | "
                f"Chunks: {exp['num_chunks']:5d} | "
                f"Média: {exp['avg_chunk_size']:7.1f} chars"
            )

    print("\nPipeline concluído!")


if __name__ == "__main__":
    main()
