# Comparacao de 10 Estrategias de Chunking

Projeto que compara **10 estrategias de chunking** para busca semantica usando a biblioteca `langchain-text-splitters` e embeddings via OpenRouter.

## Objetivo

Avaliar como diferentes formas de dividir texto impactam a qualidade da busca semantica, isolando variaveis como:
- **Tamanho do chunk** (200, 500, 1000, 2000 caracteres)
- **Overlap** (0%, 10%, 40%)
- **Estrutura natural** (paragrafo, sentenca)
- **Estrategia composta** (recursivo)
- **Estrutura semantica** (headings Markdown)

## Estrategias

| Grupo | Estrategia | Variavel Isolada |
|-------|-----------|-----------------|
| 1 | Fixo, 200 caracteres, sem overlap | tamanho (extremo baixo) |
| 2 | Fixo, 500, sem overlap | tamanho |
| 3 | Fixo, 1000, sem overlap | tamanho |
| 4 | Fixo, 2000, sem overlap | tamanho (extremo alto) |
| 5 | Fixo, 500, overlap 50 (10%) | overlap leve |
| 6 | Fixo, 500, overlap 200 (40%) | overlap pesado |
| 7 | Por paragrafo | estrutura natural |
| 8 | Por sentenca, agrupando 3 | estrutura natural |
| 9 | Recursivo (separadores hierarquicos) | estrategia composta |
| 10 | Por secao / heading do Markdown | estrutura semantica |

## Como Executar

### 1. Criar e ativar o ambiente virtual

```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar a API Key

Edite o arquivo `.env` com sua chave do OpenRouter:

```env
OPENAI_API_KEY=sua-chave-do-openrouter
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### 4. Executar

```bash
python chunking_comparativo.py
```

## Tecnologias

| Tecnologia | Descricao |
|---|---|
| **Python** | Linguagem de programacao |
| **LangChain Text Splitters** | Biblioteca de divisao de texto |
| **OpenAI SDK** | Geracao de embeddings |
| **OpenRouter** | Gateway de acesso a modelos de IA |
| **NumPy** | Computacao vetorial |

## Referencia

- [LangChain Text Splitters](https://docs.langchain.com/oss/python/integrations/splitters)
