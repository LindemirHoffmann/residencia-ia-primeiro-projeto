"""
converter_pdfs.py
-----------------
Converte todos os PDFs da pasta 'arquivos/' para Markdown (.md)
e salva na pasta 'documentos/'.

Requer: pip install pymupdf4llm
"""

import os
import re
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    raise ImportError("Instale com: pip install pymupdf4llm")


# ------------------------------------------------------------
# Configuração de pastas
# ------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parent
PASTA_PDF  = BASE_DIR / "arquivos"
PASTA_MD   = BASE_DIR / "documentos"
PASTA_MD.mkdir(exist_ok=True)


# ------------------------------------------------------------
# Limpeza de texto extraído de PDF
# ------------------------------------------------------------
def limpar_texto(texto: str) -> str:
    """Remove artefatos comuns na extração de PDF:
    - Hifens de quebra de linha  (pa-  lavra → palavra)
    - Espaços extras
    - Cabeçalhos/rodapés repetidos de página (linhas < 5 chars)
    """
    # Junta palavras quebradas por hífen no fim da linha
    texto = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)
    # Remove linhas muito curtas (numeração de página, etc.)
    linhas = [l for l in texto.splitlines() if len(l.strip()) > 4 or l.strip() == ""]
    return "\n".join(linhas)


# ------------------------------------------------------------
# Conversão principal
# ------------------------------------------------------------
def converter_pdfs():
    pdfs = sorted(PASTA_PDF.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em: {PASTA_PDF}")
        return

    print(f"Encontrados {len(pdfs)} PDFs em '{PASTA_PDF}'")
    print(f"Salvando Markdown em '{PASTA_MD}'\n")

    ok = 0
    erros = []

    for pdf in pdfs:
        nome_md = PASTA_MD / (pdf.stem + ".md")
        print(f"  [{ok+1}/{len(pdfs)}] {pdf.name}", end=" ... ")

        try:
            # pymupdf4llm extrai o PDF em Markdown estruturado
            md_text = pymupdf4llm.to_markdown(str(pdf))
            md_text = limpar_texto(md_text)

            with open(nome_md, "w", encoding="utf-8") as f:
                f.write(f"# {pdf.stem.replace('_', ' ').title()}\n\n")
                f.write(md_text)

            tamanho_kb = nome_md.stat().st_size // 1024
            print(f"OK  ({tamanho_kb} KB)")
            ok += 1

        except Exception as e:
            print(f"ERRO: {e}")
            erros.append((pdf.name, str(e)))

    print(f"\n{'='*50}")
    print(f"Concluído: {ok}/{len(pdfs)} arquivos convertidos.")
    if erros:
        print("Erros:")
        for nome, msg in erros:
            print(f"  {nome}: {msg}")
    else:
        print("Sem erros!")


if __name__ == "__main__":
    converter_pdfs()
