# 🤖 Residência em IA Generativa — Primeiro Projeto

Projeto desenvolvido durante a **Residência em Trilhas de Tecnologias de IA Generativa com RAG**, com foco na exploração de modelos de linguagem (LLMs) através da API do [OpenRouter](https://openrouter.ai/).

## 📁 Estrutura do Projeto

```
├── AULA_01/
│   ├── hello_llm.py        # Script principal - primeira interação com LLM
│   └── hello_llm.ipynb     # Versão Jupyter Notebook
├── .env.example             # Exemplo de variáveis de ambiente
├── .gitignore               # Arquivos ignorados pelo Git
├── requirements.txt         # Dependências do projeto
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
```

> 💡 **Dica:** Crie sua API key gratuitamente em [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)

### 5. Executar o projeto

```bash
cd AULA_01
python hello_llm.py
```

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
|---|---|
| **Python 3.14** | Linguagem de programação |
| **OpenAI SDK** | Biblioteca para interação com LLMs |
| **OpenRouter** | Gateway de acesso a diversos modelos de IA |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |
| **Jupyter Notebook** | Ambiente interativo para experimentação |

## 📌 Aulas

| Aula | Tema | Status |
|---|---|---|
| Aula 01 | Hello LLM — Primeira interação com modelo de linguagem | ✅ Concluída |

## 📝 Licença

Projeto desenvolvido para fins educacionais durante a Residência em Trilhas de Tecnologias de IA Generativa.

---

Feito por [Lindemir Hoffmann](https://github.com/LindemirHoffmann) 🚀