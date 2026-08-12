# =============================================================================
# Comparacao de 10 Estrategias de Chunking com LangChain Splitters
# =============================================================================
# Este script compara diferentes estrategias de divisao de texto (chunking)
# para busca semantica, usando a biblioteca langchain-text-splitters.
# Cada estrategia isola uma variavel (tamanho, overlap, estrutura) para
# avaliar o impacto na qualidade da busca semantica.
# =============================================================================

import math
import os
import re
import sys
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Corrige encoding do terminal Windows
sys.stdout.reconfigure(errors='replace')

# Carrega variaveis de ambiente da RAIZ do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

# Configuracao do cliente OpenAI via OpenRouter
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1'),
    api_key=os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY'),
)

# Constantes
MAX_CHARS = 6000
EMBEDDING_MODEL = 'openai/text-embedding-3-small'
PASTA_DOCS = Path(__file__).resolve().parent / 'documentos'

# Queries de teste
QUERIES = [
    'O que e autonomia e opacidade algoritmica?',
    'O que e o diario de bordo da IA?',
]


# =============================================================================
# Funcoes auxiliares
# =============================================================================

def get_embedding(texto):
    """Gera embedding de um texto via OpenRouter."""
    texto = str(texto)[:MAX_CHARS]
    resposta = client.embeddings.create(
        input=texto,
        model=EMBEDDING_MODEL,
    )
    return resposta.data[0].embedding


def similaridade_cosseno(vec_a, vec_b):
    """Calcula similaridade de cosseno entre dois vetores."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def busca_semantica(query, chunks, top_k=3):
    """
    Realiza busca semantica: gera embeddings para query e chunks,
    retorna os top_k mais similares.
    """
    vec_query = get_embedding(query)
    resultados = []
    batch_size = 10

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_truncado = [str(c)[:MAX_CHARS] for c in batch]

        resposta = client.embeddings.create(
            input=batch_truncado,
            model=EMBEDDING_MODEL,
        )

        for j, dado in enumerate(resposta.data):
            sim = similaridade_cosseno(vec_query, dado.embedding)
            resultados.append({
                'Trecho': batch[j],
                'Similaridade': sim,
            })

        if i + batch_size < len(chunks):
            time.sleep(1)

    resultados.sort(key=lambda x: x['Similaridade'], reverse=True)
    return resultados[:top_k]


def carregar_documentos():
    """Carrega todos os arquivos .md da pasta documentos/."""
    documentos = []
    arquivos = sorted(PASTA_DOCS.glob('*.md'))
    for arq in arquivos:
        conteudo = arq.read_text(encoding='utf-8')
        documentos.append(conteudo)
    print(f'Documentos carregados: {len(documentos)} arquivos')
    return documentos


def estatisticas_chunks(chunks):
    """Retorna estatisticas dos chunks."""
    tamanhos = [len(str(c)) for c in chunks]
    return {
        'total': len(chunks),
        'media': int(np.mean(tamanhos)) if tamanhos else 0,
        'min': min(tamanhos) if tamanhos else 0,
        'max': max(tamanhos) if tamanhos else 0,
    }


# =============================================================================
# Estrategia 8 — Por sentenca, agrupando 3
# =============================================================================

def split_por_sentencas_agrupadas(texto, n=3):
    """Divide o texto em sentencas e agrupa N sentencas por chunk."""
    sentencas = re.split(r'(?<=[.!?])\s+', texto.strip())
    sentencas = [s.strip() for s in sentencas if len(s.strip()) > 10]
    chunks = []
    for i in range(0, len(sentencas), n):
        grupo = sentencas[i:i + n]
        chunks.append(' '.join(grupo))
    return [c for c in chunks if len(c) > 10]


# =============================================================================
# As 10 estrategias de chunking
# =============================================================================

def criar_estrategias():
    """Define as 10 estrategias de chunking usando LangChain Splitters."""
    from langchain_text_splitters import (
        CharacterTextSplitter,
        RecursiveCharacterTextSplitter,
        MarkdownHeaderTextSplitter,
    )

    estrategias = []

    # ---- Grupo 1: Fixo, 200 caracteres, sem overlap (tamanho extremo baixo) ----
    estrategias.append({
        'grupo': 1,
        'nome': 'Fixo 200 chars, sem overlap',
        'variavel': 'tamanho (extremo baixo)',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=200,
            chunk_overlap=0,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 2: Fixo, 500, sem overlap (tamanho) ----
    estrategias.append({
        'grupo': 2,
        'nome': 'Fixo 500 chars, sem overlap',
        'variavel': 'tamanho',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=500,
            chunk_overlap=0,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 3: Fixo, 1000, sem overlap (tamanho) ----
    estrategias.append({
        'grupo': 3,
        'nome': 'Fixo 1000 chars, sem overlap',
        'variavel': 'tamanho',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=1000,
            chunk_overlap=0,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 4: Fixo, 2000, sem overlap (tamanho extremo alto) ----
    estrategias.append({
        'grupo': 4,
        'nome': 'Fixo 2000 chars, sem overlap',
        'variavel': 'tamanho (extremo alto)',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=2000,
            chunk_overlap=0,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 5: Fixo, 500, overlap 50 (10%) ----
    estrategias.append({
        'grupo': 5,
        'nome': 'Fixo 500, overlap 50 (10%)',
        'variavel': 'overlap leve',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=500,
            chunk_overlap=50,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 6: Fixo, 500, overlap 200 (40%) ----
    estrategias.append({
        'grupo': 6,
        'nome': 'Fixo 500, overlap 200 (40%)',
        'variavel': 'overlap pesado',
        'splitter': CharacterTextSplitter(
            separator='',
            chunk_size=500,
            chunk_overlap=200,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 7: Por paragrafo (estrutura natural) ----
    estrategias.append({
        'grupo': 7,
        'nome': 'Por paragrafo',
        'variavel': 'estrutura natural',
        'splitter': CharacterTextSplitter(
            separator='\n\n',
            chunk_size=5000,
            chunk_overlap=0,
            is_separator_regex=False,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 8: Por sentenca, agrupando 3 (estrutura natural) ----
    # Usa split_por_sentencas_agrupadas(): divide em sentencas e agrupa 3 por chunk
    estrategias.append({
        'grupo': 8,
        'nome': 'Por sentenca, agrupando 3',
        'variavel': 'estrutura natural',
        'splitter': None,  # usa split_por_sentencas_agrupadas()
        'tipo': 'sentenca',
    })

    # ---- Grupo 9: Recursivo (separadores hierarquicos) ----
    # Prioriza: paragrafos → linhas → espacos → caracteres
    estrategias.append({
        'grupo': 9,
        'nome': 'Recursivo (hierarquico)',
        'variavel': 'estrategia composta',
        'splitter': RecursiveCharacterTextSplitter(
            separators=['\n\n', '\n', '. ', '! ', '? ', ' ', ''],
            chunk_size=500,
            chunk_overlap=50,
        ),
        'tipo': 'texto',
    })

    # ---- Grupo 10: Por secao / heading do Markdown (3 niveis) ----
    estrategias.append({
        'grupo': 10,
        'nome': 'Por secao/heading Markdown',
        'variavel': 'estrutura semantica',
        'splitter': MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ('#', 'h1'),
                ('##', 'h2'),
                ('###', 'h3'),
            ],
        ),
        'tipo': 'markdown',
    })

    return estrategias


# =============================================================================
# Funcao principal
# =============================================================================

def main():
    print('=' * 80)
    print('  COMPARACAO DE 10 ESTRATEGIAS DE CHUNKING')
    print('  Usando LangChain Text Splitters + Busca Semantica via OpenRouter')
    print('=' * 80)
    print()

    # Carregar documentos
    documentos = carregar_documentos()
    texto_completo = '\n\n'.join(documentos)
    print(f'Tamanho total do texto: {len(texto_completo)} caracteres')
    print()

    # Criar estrategias
    estrategias = criar_estrategias()

    # Tabela de resultados finais
    resultados_finais = []

    for est in estrategias:
        grupo = est['grupo']
        nome = est['nome']
        variavel = est['variavel']
        splitter = est['splitter']

        print('-' * 80)
        print(f'GRUPO {grupo}: {nome}')
        print(f'Variavel isolada: {variavel}')
        print('-' * 80)

        # Dividir texto em chunks
        try:
            if est['tipo'] == 'markdown':
                # MarkdownHeaderTextSplitter retorna Documents com page_content
                chunks_docs = splitter.split_text(texto_completo)
                chunks = [doc.page_content for doc in chunks_docs if doc.page_content.strip()]
            elif est['tipo'] == 'sentenca':
                # Estrategia 8: agrupa 3 sentencas por chunk via regex
                chunks = split_por_sentencas_agrupadas(texto_completo, n=3)
            else:
                chunks = splitter.split_text(texto_completo)
                chunks = [c for c in chunks if c.strip()]
        except Exception as e:
            print(f'  ERRO ao dividir: {e}')
            print()
            continue

        # Filtrar chunks muito pequenos (menos de 10 caracteres)
        chunks = [c for c in chunks if len(c.strip()) >= 10]

        # Estatisticas
        stats = estatisticas_chunks(chunks)
        print(f'  Chunks gerados: {stats["total"]}')
        print(f'  Tamanho medio:  {stats["media"]} chars')
        print(f'  Tamanho min:    {stats["min"]} chars')
        print(f'  Tamanho max:    {stats["max"]} chars')
        print()

        # Busca semantica para cada query
        melhores_sims = []
        for qi, query in enumerate(QUERIES, 1):
            print(f'  Query {qi}: "{query}"')

            try:
                top_resultados = busca_semantica(query, chunks, top_k=3)
                melhor_sim = top_resultados[0]['Similaridade'] if top_resultados else 0.0
                melhores_sims.append(melhor_sim)

                for idx, r in enumerate(top_resultados, 1):
                    trecho_curto = r['Trecho'][:150].replace('\n', ' ')
                    print(f'    TOP {idx} (Sim: {r["Similaridade"]:.4f}): {trecho_curto}...')
            except Exception as e:
                print(f'    ERRO na busca: {e}')
                melhores_sims.append(0.0)

            print()

        # Salvar resultado para tabela final
        resultados_finais.append({
            'grupo': grupo,
            'nome': nome,
            'variavel': variavel,
            'num_chunks': stats['total'],
            'tam_medio': stats['media'],
            'sim_q1': melhores_sims[0] if len(melhores_sims) > 0 else 0.0,
            'sim_q2': melhores_sims[1] if len(melhores_sims) > 1 else 0.0,
        })

    # =========================================================================
    # Tabela comparativa final
    # =========================================================================
    print()
    print('=' * 120)
    print('  TABELA COMPARATIVA FINAL')
    print('=' * 120)
    print()

    # Cabecalho
    header = (
        f'{"Grupo":<6} '
        f'{"Estrategia":<32} '
        f'{"Variavel":<25} '
        f'{"Chunks":>7} '
        f'{"Tam.Med":>8} '
        f'{"Sim Q1":>8} '
        f'{"Sim Q2":>8} '
        f'{"Media":>8}'
    )
    print(header)
    print('-' * 120)

    for r in resultados_finais:
        media_sim = (r['sim_q1'] + r['sim_q2']) / 2
        linha = (
            f'{r["grupo"]:<6} '
            f'{r["nome"]:<32} '
            f'{r["variavel"]:<25} '
            f'{r["num_chunks"]:>7} '
            f'{r["tam_medio"]:>8} '
            f'{r["sim_q1"]:>8.4f} '
            f'{r["sim_q2"]:>8.4f} '
            f'{media_sim:>8.4f}'
        )
        print(linha)

    print('-' * 120)

    # Melhor estrategia
    if resultados_finais:
        melhor = max(resultados_finais, key=lambda x: (x['sim_q1'] + x['sim_q2']) / 2)
        print(f'\nMelhor estrategia (maior media de similaridade):')
        print(f'  Grupo {melhor["grupo"]}: {melhor["nome"]}')
        print(f'  Sim Q1: {melhor["sim_q1"]:.4f} | Sim Q2: {melhor["sim_q2"]:.4f} | Media: {(melhor["sim_q1"] + melhor["sim_q2"]) / 2:.4f}')

    print()
    print('=' * 120)
    print('Comparacao concluida!')


if __name__ == '__main__':
    main()
