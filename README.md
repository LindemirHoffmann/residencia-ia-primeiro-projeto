# 🤖 Residência em IA Generativa — Primeiro Projeto

Projeto desenvolvido durante a **Residência em Trilhas de Tecnologias de IA Generativa com RAG**, com foco na exploração de modelos de linguagem (LLMs) através da API do [OpenRouter](https://openrouter.ai/).

## 📁 Estrutura do Projeto

```
├── AULA_01/
│   ├── hello_llm.py            # Primeira interação com LLM
│   └── hello_llm.ipynb         # Versão Jupyter Notebook
├── AULA_02/
│   ├── *.pdf                   # PDFs dos artigos originais
│   ├── md_output/              # Artigos convertidos para Markdown
│   └── json_output/            # Metadados extraídos em JSON
├── AULA 03/
│   ├── atividade03.ipynb         # Notebook da atividade (Google Colab)
│   ├── embeddings_distancias.py  # Embeddings, distância euclidiana e cosseno
│   └── busca_semantica.py        # Busca semântica em documentos Markdown
├── AULA 04/
│   ├── arquivos/                 # PDFs dos artigos (não versionado)
│   ├── documentos/               # Markdowns gerados pelo converter (não versionado)
│   ├── converter_pdfs.py         # Converte PDFs → Markdown com pymupdf4llm
│   ├── chunking_comparativo.py   # Comparação de 10 estratégias de chunking
│   ├── chunking_comparativo.ipynb# Versão Google Colab
│   ├── chunking_refinado.py      # Chunking calibrado com overlaps refinados
│   └── chunking_refinado.ipynb   # Versão Google Colab
├── atv/
│   └── *.pdf                   # PDFs das atividades
├── converter.py                # Script de conversão PDF → Markdown (Docling)
├── extrair_metadados.py        # Script de extração de metadados via LLM
├── .env.example                # Exemplo de variáveis de ambiente
├── .gitignore                  # Arquivos ignorados pelo Git
├── requirements.txt            # Dependências do projeto
└── README.md
```

## 🚀 Como Executar

### 1. Clonar o repositório

```bash
git clone https://github.com/LindemirHoffmann/residencia-ia-primeiro-projeto.git
cd residencia-ia-primeiro-projeto
```

### 2. Criar e ativar o ambiente virtual

```bash
# Criar o venv
python -m venv venv

# Ativar no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Ativar no Windows (CMD)
venv\Scripts\activate

# Ativar no Linux/macOS
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env` com suas informações:

```env
OPENAI_API_KEY=sua-api-key-do-openrouter
OPENAI_MODEL=gpt-5.4-mini
OPENAI_BASE_URL=https://openrouter.ai/api/v1

OPENROUTER_API_KEY=sua-chave-do-openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

> 💡 **Dica:** Crie sua API key gratuitamente em [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)

### 5. Executar o projeto

**Aula 01 — Hello LLM:**
```bash
cd AULA_01
python hello_llm.py
```

**Aula 02 — Conversão de PDF para Markdown:**
```bash
python converter.py
```

**Aula 02 — Extração de metadados via LLM:**
```bash
python extrair_metadados.py
```

**Aula 03 — Embeddings e Distância:**
```bash
cd "AULA 03"
python embeddings_distancias.py
```

**Aula 03 — Busca Semântica:**
```bash
cd "AULA 03"
python busca_semantica.py
```

**Aula 04 — Converter PDFs para Markdown:**
```bash
cd "AULA 04"
python converter_pdfs.py
```

**Aula 04 — Chunking Comparativo (10 estratégias):**
```bash
cd "AULA 04"
python chunking_comparativo.py
```

**Aula 04 — Chunking Refinado (overlaps calibrados):**
```bash
cd "AULA 04"
python chunking_refinado.py
```

### 6. Executar a Aula 03 no Google Colab

A Aula 03 possui um notebook (`atividade03.ipynb`) preparado para rodar diretamente no **Google Colab**.

**Passo 1 — Abrir o notebook no Colab:**
- Faça upload do arquivo `AULA 03/atividade03.ipynb` no [Google Colab](https://colab.research.google.com/), ou
- Se o repositório estiver no GitHub, abra diretamente via: `Arquivo → Abrir notebook → GitHub`

**Passo 2 — Configurar a API Key como Secret:**
1. No Colab, clique no ícone de **🔑 chave** na barra lateral esquerda (Secrets)
2. Clique em **"Adicionar novo secret"**
3. Defina o **Nome** como: `OPENROUTER_API_KEY`
4. Cole o **Valor** com sua chave da API do OpenRouter
5. Ative o toggle **"Acesso ao notebook"**

> 💡 **Dica:** O notebook usa `google.colab.userdata.get('OPENROUTER_API_KEY')` para ler a chave de forma segura, sem expor no código.

**Passo 3 — Executar as células:**
- Execute todas as células em ordem (`Runtime → Run all` ou `Ctrl+F9`)
- O notebook irá:
  - Instalar a dependência `openai` automaticamente
  - Calcular distâncias euclidiana e de cosseno entre embeddings
  - Gerar gráfico 3D com PCA
  - Comparar frases com uma frase âncora
  - Realizar busca semântica nos arquivos Markdown (necessário fazer upload dos `.md` da Aula 02)

> ⚠️ **Upload dos arquivos Markdown:** Na Parte 3 (Busca Semântica), o notebook solicita o upload dos arquivos `.md` da pasta `AULA_02/md_output/`. Tenha esses arquivos prontos para enviar quando solicitado.

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
|---|---|
| **Python 3.14** | Linguagem de programação |
| **OpenAI SDK** | Biblioteca para interação com LLMs |
| **OpenRouter** | Gateway de acesso a diversos modelos de IA |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |
| **Jupyter Notebook** | Ambiente interativo para experimentação |
| **Docling** | Conversão de documentos PDF para Markdown |
| **Requests** | Chamadas HTTP para APIs REST |
| **NumPy** | Computação vetorial e manipulação de arrays |
| **Matplotlib** | Geração de gráficos e visualizações |
| **scikit-learn** | PCA para redução de dimensionalidade |
| **Pandas** | Manipulação e exibição de dados tabulares |
| **pymupdf4llm** | Conversão de PDFs para Markdown estruturado |
| **LangChain Text Splitters** | Estratégias de chunking (fixo, recursivo, Markdown) |

## 📌 Aulas

| Aula | Tema | Status |
|---|---|---|
| Aula 01 | Hello LLM — Primeira interação com modelo de linguagem | ✅ Concluída |
| Aula 02 | Conversão de PDFs para Markdown e extração de metadados com LLM | ✅ Concluída |
| Aula 03 | Embeddings, Distância Euclidiana, Cosseno e Busca Semântica | ✅ Concluída |
| Aula 04 | Chunking Comparativo — 10 estratégias com overlaps calibrados e PDF → Markdown | ✅ Concluída |

## 📝 Licença

Projeto desenvolvido para fins educacionais durante a Residência em Trilhas de Tecnologias de IA Generativa.

---

Feito por [Lindemir Hoffmann](https://github.com/LindemirHoffmann) 🚀