# =============================================================================
# Busca Semântica - Aula 03 (Parte 3)
# =============================================================================
# Script que implementa busca semântica em documentos markdown usando embeddings.
# Os documentos são divididos em diferentes granularidades (linhas, parágrafos e
# capítulos) e a busca retorna os trechos mais similares à consulta.
# =============================================================================

import math
import re
import sys
import time

# Corrige encoding do terminal Windows (cp1252 não suporta todos os caracteres Unicode)
sys.stdout.reconfigure(errors='replace')

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Carrega variáveis de ambiente do arquivo .env na raiz do projeto
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Configuração do cliente OpenAI via OpenRouter
import os

client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL'),
    api_key=os.getenv('OPENAI_API_KEY'),
)

# Constantes
MAX_CHARS = 6000
EMBEDDING_MODEL = 'openai/text-embedding-3-small'

# Caminho para os arquivos markdown gerados na Aula 02
PASTA_MD = Path(__file__).resolve().parent.parent / 'AULA_02' / 'md_output'


# =============================================================================
# Funções auxiliares
# =============================================================================

def get_embedding(texto: str) -> list[float]:
    """
    Gera o embedding de um texto usando a API da OpenAI (via OpenRouter).

    Parâmetros:
        texto: Texto para gerar o embedding.

    Retorna:
        Lista de floats representando o vetor de embedding.
    """
    texto = texto[:MAX_CHARS]
    resposta = client.embeddings.create(
        input=texto,
        model=EMBEDDING_MODEL,
    )
    return resposta.data[0].embedding


def similaridade_cosseno(embedding_a: list[float], embedding_b: list[float]) -> float:
    """
    Calcula a similaridade de cosseno entre dois vetores de embedding.

    Parâmetros:
        embedding_a: Primeiro vetor de embedding.
        embedding_b: Segundo vetor de embedding.

    Retorna:
        Valor float entre -1 e 1 representando a similaridade.
    """
    vec_a = np.array(embedding_a)
    vec_b = np.array(embedding_b)

    produto_escalar = np.dot(vec_a, vec_b)
    norma_a = np.linalg.norm(vec_a)
    norma_b = np.linalg.norm(vec_b)

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return float(produto_escalar / (norma_a * norma_b))


# =============================================================================
# Busca semântica
# =============================================================================

def busca_semantica(query: str, trechos: list[str], top_k: int = 3) -> list[dict]:
    """
    Realiza busca semântica em uma lista de trechos de texto.

    Gera embeddings para a consulta e para cada trecho, calcula a similaridade
    de cosseno e retorna os top_k trechos mais similares.

    Parâmetros:
        query: Texto da consulta.
        trechos: Lista de trechos de texto para buscar.
        top_k: Número de resultados a retornar (padrão: 3).

    Retorna:
        Lista de dicionários com 'Trecho' e 'Similaridade', ordenados por
        similaridade decrescente.
    """
    # Gera embedding da consulta
    embedding_query = get_embedding(query)

    resultados = []
    tamanho_batch = 10

    # Processa trechos em lotes de 10
    for i in range(0, len(trechos), tamanho_batch):
        batch = trechos[i:i + tamanho_batch]

        # Trunca cada trecho ao limite de caracteres
        batch_truncado = [trecho[:MAX_CHARS] for trecho in batch]

        # Gera embeddings para o lote via API
        resposta = client.embeddings.create(
            input=batch_truncado,
            model=EMBEDDING_MODEL,
        )

        # Calcula similaridade entre a consulta e cada trecho do lote
        for j, dado in enumerate(resposta.data):
            similaridade = similaridade_cosseno(embedding_query, dado.embedding)
            resultados.append({
                'Trecho': batch[j],
                'Similaridade': similaridade,
            })

        # Pausa entre lotes para evitar rate limiting
        if i + tamanho_batch < len(trechos):
            time.sleep(1)

    # Ordena por similaridade decrescente e retorna os top_k
    resultados.sort(key=lambda x: x['Similaridade'], reverse=True)
    return resultados[:top_k]


# =============================================================================
# Função principal
# =============================================================================

def main():
    """Função principal que executa as buscas semânticas nos documentos."""

    # -------------------------------------------------------------------------
    # Carrega todos os arquivos markdown
    # -------------------------------------------------------------------------
    arquivos_md = sorted(PASTA_MD.glob('*.md'))
    documentos = []
    for arquivo in arquivos_md:
        conteudo = arquivo.read_text(encoding='utf-8')
        documentos.append(conteudo)

    print(f'Total de arquivos markdown carregados: {len(documentos)}')
    print('=' * 80)

    # Consultas para busca
    query1 = 'O que é autonomia e opacidade algorítmica?'
    query2 = 'O que é o diário de bordo da IA?'

    # =========================================================================
    # BUSCA POR LINHA
    # =========================================================================
    print('\n>>> BUSCA POR LINHA')
    print('=' * 80)

    # Divide todos os documentos em linhas (remove vazias e muito curtas)
    linhas = []
    for doc in documentos:
        for linha in doc.split('\n'):
            linha_limpa = linha.strip()
            if linha_limpa and len(linha_limpa) >= 10:
                linhas.append(linha_limpa)

    print(f'Total de linhas: {len(linhas)}')
    print('-' * 80)

    # Busca query1 por linhas
    print(f'\nConsulta: "{query1}"')
    resultados_linhas_q1 = busca_semantica(query1, linhas, top_k=3)
    for idx, resultado in enumerate(resultados_linhas_q1, 1):
        trecho_exibido = resultado['Trecho'][:200]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    print('-' * 80)

    # Busca query2 por linhas
    print(f'\nConsulta: "{query2}"')
    resultados_linhas_q2 = busca_semantica(query2, linhas, top_k=3)
    for idx, resultado in enumerate(resultados_linhas_q2, 1):
        trecho_exibido = resultado['Trecho'][:200]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    # =========================================================================
    # BUSCA POR PARÁGRAFO
    # =========================================================================
    print('\n\n>>> BUSCA POR PARAGRAFO')
    print('=' * 80)

    # Divide todos os documentos em parágrafos (separados por linhas duplas)
    paragrafos = []
    for doc in documentos:
        for paragrafo in doc.split('\n\n'):
            paragrafo_limpo = paragrafo.strip()
            if paragrafo_limpo and len(paragrafo_limpo) >= 20:
                paragrafos.append(paragrafo_limpo)

    print(f'Total de paragrafos: {len(paragrafos)}')
    print('-' * 80)

    # Busca query1 por parágrafos
    print(f'\nConsulta: "{query1}"')
    resultados_paragrafos_q1 = busca_semantica(query1, paragrafos, top_k=3)
    for idx, resultado in enumerate(resultados_paragrafos_q1, 1):
        trecho_exibido = resultado['Trecho'][:300]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    print('-' * 80)

    # Busca query2 por parágrafos
    print(f'\nConsulta: "{query2}"')
    resultados_paragrafos_q2 = busca_semantica(query2, paragrafos, top_k=3)
    for idx, resultado in enumerate(resultados_paragrafos_q2, 1):
        trecho_exibido = resultado['Trecho'][:300]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    # =========================================================================
    # BUSCA POR CAPÍTULO
    # =========================================================================
    print('\n\n>>> BUSCA POR CAPITULO')
    print('=' * 80)

    # Divide todos os documentos por cabeçalhos markdown (# ou ##)
    capitulos = []
    for doc in documentos:
        partes = re.split(r'(?=^#{1,2}\s)', doc, flags=re.MULTILINE)
        for parte in partes:
            parte_limpa = parte.strip()
            if parte_limpa and len(parte_limpa) >= 30:
                capitulos.append(parte_limpa)

    print(f'Total de capitulos: {len(capitulos)}')

    # Exibe os títulos dos capítulos encontrados
    print('\nTitulos dos capitulos:')
    for idx, capitulo in enumerate(capitulos, 1):
        # Extrai a primeira linha como título
        titulo = capitulo.split('\n')[0].strip()
        print(f'  {idx}. {titulo}')

    print('-' * 80)

    # Busca query1 por capítulos
    print(f'\nConsulta: "{query1}"')
    resultados_capitulos_q1 = busca_semantica(query1, capitulos, top_k=3)
    for idx, resultado in enumerate(resultados_capitulos_q1, 1):
        trecho_exibido = resultado['Trecho'][:400]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    print('-' * 80)

    # Busca query2 por capítulos
    print(f'\nConsulta: "{query2}"')
    resultados_capitulos_q2 = busca_semantica(query2, capitulos, top_k=3)
    for idx, resultado in enumerate(resultados_capitulos_q2, 1):
        trecho_exibido = resultado['Trecho'][:400]
        print(f'\n  TOP {idx} (Similaridade: {resultado["Similaridade"]:.4f})')
        print(f'  {trecho_exibido}')

    print('\n' + '=' * 80)
    print('Busca semantica concluida!')


if __name__ == '__main__':
    main()
