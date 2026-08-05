import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuracao da API OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

# Pastas
PASTA_MD = Path(r"C:\Users\Administrator\Documents\projeto ia\residencia-ia-primeiro-projeto\AULA_02\md_output")
PASTA_JSON = Path(r"C:\Users\Administrator\Documents\projeto ia\residencia-ia-primeiro-projeto\AULA_02\json_output")
PASTA_JSON.mkdir(exist_ok=True)

# Modelos gratuitos para tentar em ordem
MODELOS_FREE = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "poolside/laguna-xs-2.1:free",
]


def extrair_metadados(conteudo_md: str) -> dict:
    """
    Recebe o conteudo de um arquivo .md e retorna um objeto JSON estruturado
    com os metadados extraidos usando Structured Outputs via OpenRouter.
    """

    # Limitar conteudo enviado (primeiros 3000 chars)
    trecho = conteudo_md[:3000]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    for modelo in MODELOS_FREE:
        payload = {
            "model": modelo,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Voce e um assistente que extrai metadados de artigos academicos. "
                        "Analise o conteudo fornecido e extraia as informacoes solicitadas. "
                        "Retorne APENAS o JSON estruturado, sem texto adicional, sem markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Extraia os metadados do seguinte artigo academico em Markdown:\n\n"
                        f"{trecho}\n\n"
                        f"Retorne SOMENTE um JSON valido com os campos: "
                        f'"titulo" (string), "autores" (lista de strings), "ano" (inteiro). '
                        f"Nao inclua nenhum texto antes ou depois do JSON."
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "metadados_artigo",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "titulo": {
                                "type": "string",
                                "description": "Titulo completo do trabalho/artigo"
                            },
                            "autores": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista com os nomes dos autores"
                            },
                            "ano": {
                                "type": "integer",
                                "description": "Ano de publicacao do trabalho"
                            }
                        },
                        "required": ["titulo", "autores", "ano"],
                        "additionalProperties": False
                    }
                }
            }
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 429:
                print(f"    Rate limit com {modelo}, aguardando 10s...")
                time.sleep(10)
                continue

            if response.status_code == 402:
                print(f"    Sem creditos para {modelo}, tentando proximo...")
                continue

            response.raise_for_status()

            resultado = response.json()
            conteudo_resposta = resultado["choices"][0]["message"]["content"]

            # Tentar parse do JSON
            metadados = json.loads(conteudo_resposta)
            return metadados

        except json.JSONDecodeError:
            # Se nao veio JSON puro, tentar extrair
            import re
            json_match = re.search(r'\{.*\}', conteudo_resposta, re.DOTALL)
            if json_match:
                metadados = json.loads(json_match.group())
                return metadados
            print(f"    Resposta nao-JSON de {modelo}, tentando proximo...")
            continue

        except Exception as e:
            print(f"    Erro com {modelo}: {e}")
            time.sleep(5)
            continue

    raise Exception("Nenhum modelo disponivel retornou resultado valido")


def main():
    print("=" * 60)
    print("  TAREFA 2 - Extracao de Metadados dos Arquivos Markdown")
    print("=" * 60)
    print()

    todos_metadados = {}

    for arquivo_md in sorted(PASTA_MD.glob("*.md")):
        print(f"Processando: {arquivo_md.name} ...")

        # Ler conteudo do arquivo .md
        with open(arquivo_md, "r", encoding="utf-8") as f:
            conteudo = f.read()

        try:
            # Extrair metadados via API com Structured Outputs
            metadados = extrair_metadados(conteudo)

            # Salvar JSON individual
            nome_json = arquivo_md.stem + "_metadados.json"
            caminho_json = PASTA_JSON / nome_json

            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(metadados, f, ensure_ascii=False, indent=2)

            todos_metadados[arquivo_md.stem] = metadados

            print(f"  [OK] Metadados extraidos:")
            print(f"        Titulo:  {metadados['titulo']}")
            print(f"        Autores: {', '.join(metadados['autores'])}")
            print(f"        Ano:     {metadados['ano']}")
            print(f"        Salvo em: {caminho_json}")
            print()

        except Exception as e:
            print(f"  [ERRO] {e}")
            print()

        # Delay entre arquivos para evitar rate limit
        time.sleep(3)

    # Salvar todos os metadados em um unico arquivo consolidado
    caminho_consolidado = PASTA_JSON / "todos_metadados.json"
    with open(caminho_consolidado, "w", encoding="utf-8") as f:
        json.dump(todos_metadados, f, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"Arquivo consolidado salvo em: {caminho_consolidado}")
    print("Extracao finalizada!")


if __name__ == "__main__":
    main()
