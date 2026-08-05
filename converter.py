import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"

from docling.document_converter import DocumentConverter
from pathlib import Path

pasta_pdf = Path(r"C:\Users\Administrator\Documents\projeto ia\residencia-ia-primeiro-projeto\AULA_02")
pasta_saida = Path(r"C:\Users\Administrator\Documents\projeto ia\residencia-ia-primeiro-projeto\AULA_02\md_output")
pasta_saida.mkdir(exist_ok=True)

converter = DocumentConverter()

for pdf in pasta_pdf.glob("*.pdf"):
    print(f"Convertendo: {pdf.name} ...")
    try:
        result = converter.convert(str(pdf))
        markdown = result.document.export_to_markdown()

        nome_md = pdf.stem + ".md"
        caminho_saida = pasta_saida / nome_md

        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"  [OK] Salvo em: {caminho_saida}")
    except Exception as e:
        print(f"  [ERRO] Ao converter {pdf.name}: {e}")

print("\nConversao finalizada!")
