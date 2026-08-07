"""
Atividade 03 - IA
Distância Euclidiana, Distância de Cosseno e Comparação de Frases

Este script implementa as Partes 1 e 2 do notebook da Aula 03:
- Parte 1: Funções de distância e teste com embeddings reais + gráfico 3D (PCA)
- Parte 2: Comparação de frases usando uma frase âncora
"""

import os
import sys
import math
import itertools
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para encontrar o .env
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (necessário para projeção 3D)
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis de ambiente do arquivo .env na raiz do projeto
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Configura o cliente OpenAI com OpenRouter
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Constantes
MAX_CHARS = 6000  # Limite de caracteres por trecho para não estourar os 8192 tokens da API
EMBEDDING_MODEL = 'openai/text-embedding-3-small'


# ---------------------------------------------------------------------------
# Funções auxiliares para geração de embeddings
# ---------------------------------------------------------------------------

def get_embedding(texto):
    """
    Gera o embedding de um texto usando a API do OpenRouter.
    Se o texto for uma tupla (rótulo, frase), usa apenas a frase.
    Trunca textos muito longos.
    """
    if isinstance(texto, tuple):
        texto = texto[1]
    texto = texto[:MAX_CHARS]
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texto
    )
    return response.data[0].embedding


def get_embeddings_batch(textos):
    """
    Gera embeddings para uma lista de textos de uma vez.
    Trunca cada texto ao limite de caracteres.
    """
    textos_truncados = [t[:MAX_CHARS] for t in textos]
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=textos_truncados
    )
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Funções de distância
# ---------------------------------------------------------------------------

def distancia_euclidiana(embedding_a, embedding_b):
    """
    Calcula a distância euclidiana entre dois embeddings.
    d = sqrt(sum((a_i - b_i)^2))
    Recebe dois vetores de qualquer dimensão, desde que possuam o mesmo tamanho.
    """
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Os dois embeddings devem possuir a mesma dimensão.")

    soma = sum((a - b) ** 2 for a, b in zip(embedding_a, embedding_b))
    return math.sqrt(soma)


def similaridade_cosseno(embedding_a, embedding_b):
    """
    Calcula a similaridade de cosseno entre dois embeddings.
    sim = (A · B) / (||A|| * ||B||)
    Retorna um valor entre -1 e 1 (1 = idênticos, 0 = ortogonais).
    """
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Os dois embeddings devem possuir a mesma dimensão.")

    produto_escalar = sum(a * b for a, b in zip(embedding_a, embedding_b))
    norma_a = math.sqrt(sum(a ** 2 for a in embedding_a))
    norma_b = math.sqrt(sum(b ** 2 for b in embedding_b))

    if norma_a == 0 or norma_b == 0:
        raise ValueError("Não é possível calcular para vetores nulos.")

    return produto_escalar / (norma_a * norma_b)


def distancia_cosseno(embedding_a, embedding_b):
    """
    Calcula a distância de cosseno entre dois embeddings.
    distância = 1 - similaridade
    """
    return 1 - similaridade_cosseno(embedding_a, embedding_b)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def main():
    # ==================================================================
    # PARTE 1 — Funções de Distância
    # ==================================================================

    print("=" * 60)
    print("PARTE 1 — Funções de Distância")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1.1 Teste com vetores simples
    # ------------------------------------------------------------------
    print("\n--- Teste com vetores simples ---\n")

    embedding_a = [1, 0, 0]
    embedding_b = [0, 1, 0]
    embedding_c = [1, 0, 0]

    print("Embeddings de teste:")
    print(f"  embedding_a = {embedding_a}")
    print(f"  embedding_b = {embedding_b}")
    print(f"  embedding_c = {embedding_c}")

    print("\n>> embedding_a x embedding_b")
    print(f"   Dist. Euclidiana: {distancia_euclidiana(embedding_a, embedding_b):.4f}")
    print(f"   Dist. Cosseno:    {distancia_cosseno(embedding_a, embedding_b):.4f}")

    print("\n>> embedding_a x embedding_c")
    print(f"   Dist. Euclidiana: {distancia_euclidiana(embedding_a, embedding_c):.4f}")
    print(f"   Dist. Cosseno:    {distancia_cosseno(embedding_a, embedding_c):.4f}")

    print("\n>> embedding_b x embedding_c")
    print(f"   Dist. Euclidiana: {distancia_euclidiana(embedding_b, embedding_c):.4f}")
    print(f"   Dist. Cosseno:    {distancia_cosseno(embedding_b, embedding_c):.4f}")

    # ------------------------------------------------------------------
    # 1.2 Teste com embeddings reais (palavras agrupadas por categoria)
    # ------------------------------------------------------------------
    print("\n--- Teste com embeddings reais ---\n")

    palavras_animais = ['gato', 'cachorro', 'felino']
    palavras_veiculos = ['carro', 'moto', 'caminhão']
    palavras_frutas = ['banana', 'maçã', 'goiaba']

    todas_palavras = palavras_animais + palavras_veiculos + palavras_frutas

    # Gera os embeddings via OpenRouter
    print("Gerando embeddings para as palavras...")
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=todas_palavras
    )

    embs_palavras = {}
    for palavra, item in zip(todas_palavras, response.data):
        embs_palavras[palavra] = item.embedding

    print("Embeddings gerados com sucesso!\n")

    # Tabela comparativa de distâncias entre todos os pares
    pares = list(itertools.combinations(todas_palavras, 2))
    print(f"{'Par':<25} {'Dist. Euclidiana':>18} {'Dist. Cosseno':>15}")
    print("-" * 60)
    for p1, p2 in pares:
        d_euc = distancia_euclidiana(embs_palavras[p1], embs_palavras[p2])
        d_cos = distancia_cosseno(embs_palavras[p1], embs_palavras[p2])
        print(f"{p1 + ' x ' + p2:<25} {d_euc:>18.4f} {d_cos:>15.4f}")

    # ------------------------------------------------------------------
    # 1.3 Gráfico 3D com PCA
    # ------------------------------------------------------------------
    print("\nGerando gráfico 3D com PCA...")

    nomes = list(embs_palavras.keys())
    matriz = np.array([embs_palavras[p] for p in nomes])

    pca = PCA(n_components=3)
    coords_3d = pca.fit_transform(matriz)

    # Define as cores por categoria
    cores = []
    for palavra in nomes:
        if palavra in palavras_animais:
            cores.append('#4285F4')   # Azul — Animais
        elif palavra in palavras_veiculos:
            cores.append('#EA4335')   # Vermelho — Veículos
        else:
            cores.append('#34A853')   # Verde — Frutas

    fig = plt.figure(figsize=(12, 9), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(
        coords_3d[:, 0], coords_3d[:, 1], coords_3d[:, 2],
        c=cores, s=120, depthshade=True
    )

    for i, nome in enumerate(nomes):
        ax.text(
            coords_3d[i, 0], coords_3d[i, 1], coords_3d[i, 2],
            '  ' + nome, fontsize=11
        )

    ax.set_title('Embeddings de palavras reduzidos para 3D (via PCA)', fontsize=14)
    ax.set_xlabel('Componente 1')
    ax.set_ylabel('Componente 2')
    ax.set_zlabel('Componente 3')
    plt.tight_layout()

    # Salva o gráfico como PNG na pasta AULA_03
    caminho_grafico = Path(__file__).resolve().parent / 'embeddings_3d_pca.png'
    plt.savefig(caminho_grafico, dpi=150, bbox_inches='tight')
    print(f"Gráfico salvo em: {caminho_grafico}")
    plt.close()

    # ==================================================================
    # PARTE 2 — Comparação de Frases (Frase Âncora)
    # ==================================================================

    print("\n" + "=" * 60)
    print("PARTE 2 — Comparação de Frases (Frase Âncora)")
    print("=" * 60)

    frase_ancora = 'O cachorro correu no parque e brincou com a bola.'

    frases_comparacao = [
        ("Similar (mesmo sentido, palavras diferentes)",
         "Um cão estava correndo no jardim e brincando com seu brinquedo."),
        ("Relacionado (mesmo contexto de animais)",
         "O gato dormiu na almofada da sala durante toda a tarde."),
        ("Diferente (outro domínio - economia)",
         "A taxa de juros do banco central subiu dois pontos percentuais."),
        ("Oposto/Negação",
         "Nenhum animal esteve no parque e o cão permaneceu preso em casa."),
    ]

    # Gerar o embedding da âncora
    print(f'\nFrase âncora: "{frase_ancora}"\n')
    print("Gerando embeddings das frases...")

    vec_ancora = np.array(get_embedding(frase_ancora), dtype=np.float32)

    # Gerar os embeddings das comparações
    vecs_comp = []
    for rotulo, frase in frases_comparacao:
        vec = np.array(get_embedding(frase), dtype=np.float32)
        vecs_comp.append(vec)

    # Montar tabela de resultados
    print(f"\n{'Categoria':<50} {'Dist. Euclid.':>14} {'Sim. Cosseno':>14} {'Dist. Cosseno':>14}")
    print("-" * 95)

    for (rotulo, frase), vec in zip(frases_comparacao, vecs_comp):
        d_euc = distancia_euclidiana(vec_ancora, vec)
        s_cos = similaridade_cosseno(vec_ancora, vec)
        d_cos = distancia_cosseno(vec_ancora, vec)
        print(f"{rotulo:<50} {d_euc:>14.4f} {s_cos:>14.4f} {d_cos:>14.4f}")

    print("\n" + "-" * 95)
    print("Frases comparadas:")
    for rotulo, frase in frases_comparacao:
        print(f'  • {rotulo}: "{frase}"')

    print("\nConcluído!")


if __name__ == '__main__':
    main()
