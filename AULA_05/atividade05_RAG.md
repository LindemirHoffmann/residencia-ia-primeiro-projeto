# Atividade 05 — Projeto de Arquitetura RAG

**Autor:** Lindemir Hoffmann
**Data:** 17/08/2026
**Repositório:** residencia-ia-primeiro-projeto (GitHub)

---

## Sobre os cenários escolhidos

Escolhi dois cenários que conheço de perto e que contrastam em quase tudo: tipo de usuário, tipo de documento, volume, frequência de atualização e criticidade do erro.

**Cenário A** — Assistente de consulta jurídica para um escritório de advocacia trabalhista.
**Cenário B** — Assistente técnico para manutenção de equipamentos industriais (linha de produção de uma fábrica de alimentos).

A diferença central: no Cenário A o usuário é especializado, o documento é denso em texto e o erro pode custar uma causa. No Cenário B o usuário é um técnico consultando pelo celular, o documento mistura texto, diagrama e tabela, e o erro pode parar uma linha de produção ou machucar alguém.

---

# CENÁRIO A — Assistente Jurídico Trabalhista

---

## Parte 1 — Identificação do problema

### 1.1 Descrição do problema

**Qual é o problema?**

Um escritório de advocacia trabalhista de médio porte acumula, ao longo dos anos, centenas de contratos de prestação de serviço, teses jurídicas redigidas pelos sócios, pareceres, ementas de jurisprudência coletadas manualmente e legislação consolidada (CLT, Lei 13.467, legislação complementar). Hoje, quando um advogado júnior precisa saber se determinada cláusula de não-concorrência é válida ou qual é o entendimento do TST sobre sobreaviso em home office, ele abre pastas no servidor, faz buscas no Windows Explorer por palavra-chave e frequentemente liga para um sócio para perguntar onde está tal documento. O tempo gasto nessa busca chega a 30–40 minutos por consulta.

O sistema resolverá isso: o advogado faz uma pergunta em linguagem natural e recebe uma resposta fundamentada com citação da fonte.

**Quem usa?**

- **Advogados júnior** (0 a 3 anos de OAB): estão aprendendo, fazem muitas consultas pontuais, nível técnico médio, usam o computador no escritório.
- **Estagiários de direito**: nível técnico baixo no domínio jurídico, precisam de respostas que citem a fonte para poder verificar.
- **Advogados sênior** (eventualmente): para confirmar precedentes rápidos antes de uma audiência, geralmente pelo celular.

**Que informação o usuário consulta?**

- Se determinada prática é legal segundo a CLT vigente.
- Se o escritório já tem tese consolidada sobre determinado tema.
- Qual a jurisprudência dominante do TST em determinado assunto.
- Qual o prazo prescricional para determinado tipo de reclamação.

**De onde vêm as informações?**

- Servidor local do escritório (documentos Word, PDF).
- CLT e leis complementares em PDF (baixadas do Planalto).
- Coleção interna de ementas do TST (PDFs baixados periodicamente do site do tribunal).
- Pareceres e teses escritos pelos sócios em DOCX.

**Por que LLM sozinho não basta?**

A CLT foi reformada em 2017 (Lei 13.467), em 2019 e sofreu mudanças pontuais posteriores. Um LLM treinado em 2023 ou 2024 pode responder com base na CLT pré-reforma, ou com base em uma tese que o TST reverteu. Além disso, as teses do escritório são privadas — nenhum modelo de mercado as conhece.

**Como o usuário acessa?**

Interface web interna (intranet), acessível por navegador no escritório. Para os sênior que consultam em trânsito, também via app mobile com autenticação.

**Três perguntas reais que o usuário faria:**

1. *"O empregado pode acumular horas extras em home office e cobrar depois? O TST tem alguma súmula sobre isso?"*
2. *"Nossa tese de contrato por prazo determinado fraudado — onde está isso aqui no escritório? Já ganhamos com esse argumento antes?"*
3. *"Qual o prazo pra entrar com reclamação trabalhista depois que o funcionário foi demitido? E se for menor de idade?"*

---

### 1.2 Por que RAG?

**RAG é adequado porque:**

O problema envolve um corpus específico, privado e que muda periodicamente. O LLM precisa fundamentar cada resposta em documentos concretos, com citação de fonte — sem isso, o advogado não pode usar a resposta.

**Que conhecimento precisa ser fornecido?**

- Texto legislativo atualizado (CLT consolidada, leis complementares).
- Jurisprudência: ementas do TST, sumários, orientações jurisprudenciais.
- Documentos internos: teses, pareceres, contratos-modelo.

**Com que frequência muda?**

- Legislação: raramente (uma reforma trabalhista a cada vários anos, mas emendas pontuais a cada 6–12 meses).
- Jurisprudência TST: mensalmente, às vezes semanalmente.
- Teses internas: sob demanda, sempre que um sócio escreve um novo parecer.

**Documentos privados?**

Sim. As teses internas do escritório são o principal diferencial competitivo. Jamais podem ser enviadas para uma API pública.

**Exemplo concreto de resposta errada sem RAG:**

Pergunta: *"A reforma trabalhista de 2017 mudou o artigo 58 da CLT sobre tempo de deslocamento?"*

LLM sem RAG: *"O artigo 58 da CLT estabelece que o tempo de deslocamento é computado na jornada de trabalho quando o local for de difícil acesso."* — Isso era verdade até 2017. A Lei 13.467 revogou esse trecho. Um advogado júnior que acreditar nessa resposta pode entrar com uma ação perdida de antemão.

---

### 1.3 Limitações — quando RAG não é a resposta

**Busca por palavra-chave:** Funciona bem quando o usuário sabe exatamente o que procura. Se o advogado quer encontrar "cláusula 5.2 do contrato com a empresa X", um Ctrl+F no servidor resolve em 10 segundos. RAG é desnecessário e mais lento nesse caso.

**Banco de dados SQL:** Para perguntas quantitativas como "quantas causas ativas temos contra empresas do setor metalúrgico?" ou "qual foi o prazo médio de tramitação dos processos que ganhamos em 2024?", o RAG responderia mal ou inventaria. Isso pertence ao sistema de gestão processual (CRM jurídico) com SQL.

**Regras determinísticas:** Para prazos legais fixos — prescrição de 2 anos, aviso prévio de 30 dias — uma função simples que lê uma tabela de prazos é mais confiável e auditável do que RAG.

**API direta:** O Planalto e o TST oferecem APIs e buscas textuais. Para jurisprudência nova, acessar a API do tribunal diretamente pode ser mais atualizado do que qualquer base vetorizada.

**Combinação de técnicas:** O cenário ideal é RAG + SQL. O SQL cuida do que é estruturado (dados processuais, prazos, contagens). O RAG cuida do que é textual (legislação, teses, jurisprudência). O LLM no final coordena a resposta, usando os dois.

**Pergunta que RAG responderia mal, banco relacional bem:**

*"Quantos processos em andamento temos com pedido de horas extras acima de 100 horas e audiência marcada para o próximo mês?"*

Isso exige contar, filtrar por datas e cruzar campos — é SQL puro. O RAG não tem como contar registros espalhados em documentos.

**O que acontece se a pergunta exige contar, somar ou ordenar?**

RAG colapsa. Se o usuário perguntar "qual dos últimos 10 pareceres mais menciona o artigo 62 da CLT?", o sistema vai recuperar chunks relacionados ao art. 62, mas não vai conseguir contar sistematicamente em quantos documentos ele aparece. O pior cenário: resposta errada com aparência de resposta certa.

---

## Parte 2 — Organização dos documentos

**Tipos de arquivo existentes:**

- PDF (legislação, jurisprudência, ementas TST): principal formato de entrada.
- DOCX (pareceres e teses internas): formato nativo de trabalho dos advogados.
- HTML (cópia de páginas do TST, Planalto): raramente.

**Volume:** Estimativa inicial de 800–1.200 documentos. Ementas do TST: ~600. Legislação: ~50. Teses e pareceres internos: ~200–400.

**Tamanho típico:**
- CLT consolidada: ~200 páginas, ~1MB.
- Ementa TST individual: 2–10 páginas, 50–200KB.
- Parecer interno: 5–20 páginas, 100–500KB.

**Estrutura de pastas:**

```
documentos/
├── legislacao/
│   ├── clt_consolidada/
│   └── leis_complementares/
├── jurisprudencia/
│   ├── tst_sumulas/
│   ├── tst_ementas/
│   └── orientacoes_jurisprudenciais/
├── internos/
│   ├── teses/
│   ├── pareceres/
│   └── contratos_modelo/
└── _arquivo/
    └── (versoes obsoletas, nunca indexadas)
```

**Justificativa da estrutura:**

A divisão espelha como um advogado pensa ao buscar informação: primeiro decide se é questão de lei, de jurisprudência ou de posição interna do escritório. Essa divisão também é o filtro mais útil na busca. O filtro por `category` (que corresponde a essa pasta) reduz o espaço de busca e melhora a precisão.

A pasta `_arquivo` existe para separar versões obsoletas fisicamente. Um documento ali jamais entra no pipeline de ingestão.

**Documentos que não devem entrar na base:**
- Documentos com dados pessoais de clientes identificados (RG, CPF, dados bancários).
- Contratos com cláusulas de confidencialidade que impedem reprodução.
- Versões antigas/revogadas de documentos.

O script de ingestão tem uma lista de exclusão (`blocklist.txt`). Qualquer arquivo em `_arquivo/` é ignorado por configuração.

**Controle de versões:**

Cada documento tem `valid_until` e `superseded_by`. Na busca, o filtro padrão é `valid_until IS NULL OR valid_until > today`. Versões antigas ficam na base mas com `is_current = false`, para consulta explícita se necessário.

---

## Parte 3 — Pipeline de ingestão

### 3.1 Extração

**PDFs com texto selecionável:** Uso `pymupdf4llm` (já utilizado na Aula 04 deste projeto). Ele extrai o texto preservando estrutura de parágrafos e tabelas como Markdown.

**PDFs digitalizados:** OCR via `pytesseract` ou Google Document AI. O risco é qualidade: OCR ruim gera texto com erros de caractere. Esse foi um problema enfrentado na Aula 02 — alguns PDFs tinham camada de texto corrompida, e o texto extraído saía com hifens de quebra de linha no meio de palavras (daí o `limpar_texto()` no `chunking_refinado.py` do projeto).

**Tabelas:** São importantes e precisam ser mantidas. O `pymupdf4llm` converte tabelas para Markdown. Para tabelas complexas (células mescladas), uso passo adicional com LLM para descrever a tabela.

**Imagens:** Na maioria dos documentos jurídicos, imagens são apenas brasões e logos — descarto. Se houver imagem com conteúdo (ex: organograma), uso GPT-4o para gerar descrição textual.

**Problema real na Aula 02:** Rodapés e cabeçalhos de página se misturavam ao texto corrido. Em documentos jurídicos isso é mais grave: um número de página no meio do texto de uma cláusula gera chunk com informação corrompida.

---

### 3.2 Limpeza e normalização

**O que remover:**
- Cabeçalhos e rodapés repetidos (número de página, nome do tribunal).
- Marcas d'água ("CÓPIA NÃO CONTROLADA").
- Sumário/índice.
- Referências bibliográficas no fim de pareceres.

**O que padronizar:**
- Acentuação: normalizo com `unicodedata.normalize("NFC", texto)`.
- Quebras de linha hifenizadas: o `re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)` já no projeto resolve.
- Espaçamento duplo, tabulações.

**O que posso perder ao limpar demais:**

O risco real é remover numeração de artigos. Minha regra: nunca removo linhas que começam com `Art.`, `§`, `Inc.` ou numeração romana — são estrutura jurídica crítica.

---

### 3.3 Frequência de ingestão

- **Ingestão inicial (one-shot):** roda uma vez para os ~1.000 documentos existentes.
- **Ingestão incremental:** roda toda segunda-feira às 07h. Detecta novos documentos por hash MD5. Se o hash não existe, processa. Se existe mas `updated_at` mudou, reprocessa apenas aquele documento.

Reprocessar a base inteira seria impraticável semanalmente por custo de embedding.

---

## Parte 4 — Metadados

### 4.1 Metadados do documento

```json
{
  "document_id": "jur-tst-2024-0847",
  "title": "Acórdão TST — RR-1001-55.2022.5.04.0019",
  "author": "TST — Turma 3",
  "source": "https://tst.jus.br/web/guest/jurisprudencia",
  "document_type": "ementa_tst",
  "category": "jurisprudencia",
  "subcategory": "tst_ementas",
  "created_at": "2024-03-15",
  "updated_at": "2024-03-15",
  "ingested_at": "2024-03-18",
  "valid_until": null,
  "superseded_by": null,
  "is_current": true,
  "topics": ["horas_extras", "home_office", "sobreaviso"],
  "legislation_refs": ["art. 244 CLT", "Súmula 428 TST"],
  "access_level": "interno",
  "md5_hash": "a3f9..."
}
```

**Por que cada campo:**

- `document_id`: identificador único para cruzar com chunk e para citação de fonte.
- `title`: aparece na resposta ao usuário como citação.
- `author`: saber se é documento interno (sócio) ou externo (TST) muda a autoridade da fonte.
- `source`: URL para o documento original — o usuário pode verificar.
- `document_type`: filtro na busca — "só quero jurisprudência".
- `category` e `subcategory`: espelham a estrutura de pastas; permitem filtros hierárquicos.
- `created_at` / `updated_at`: para perguntas sobre legislação vigente em determinada data.
- `ingested_at`: controle operacional, útil para debug.
- `valid_until` / `superseded_by` / `is_current`: controle de versão — crítico para não servir CLT revogada.
- `topics`: extraídos via LLM (output estruturado, conforme praticado na Aula 02 do projeto).
- `legislation_refs`: artigos e súmulas mencionados — extração via LLM com validação regex.
- `access_level`: distingue documentos de acesso geral dos restritos a sócios.
- `md5_hash`: controle de duplicatas e de mudança de conteúdo.

### 4.2 Metadados do chunk

```json
{
  "document_id": "jur-tst-2024-0847",
  "chunk_id": "jur-tst-2024-0847-08",
  "page": 3,
  "section": "Ementa",
  "section_type": "ementa",
  "document_type": "ementa_tst",
  "category": "jurisprudencia",
  "is_current": true,
  "legislation_refs": ["art. 244 CLT", "Súmula 428 TST"],
  "text": "..."
}
```

**Filtro indispensável:** `category` + `is_current`. Pergunta crítica: *"Qual a posição atual do TST sobre sobreaviso?"*. Sem filtrar `category = jurisprudencia` e `is_current = true`, o sistema pode trazer um parecer interno de 2019 ou uma ementa superada.

**Citação ao usuário:**
> *Fonte: Acórdão TST — RR-1001-55.2022.5.04.0019, página 3, Seção: Ementa (publicado em 15/03/2024)*

**Metadado mais caro para acrescentar depois:** `topics` e `legislation_refs`. São extraídos via LLM durante a ingestão. Se esquecidos, tenho que reprocessar todos os ~1.000 documentos com chamadas de LLM — tempo e custo significativos.

**Como extrair:** Uso o `extrair_metadados.py` já desenvolvido no projeto, adaptado para o schema. Campos estruturais (`document_type`, `source`, `created_at`) vêm do nome do arquivo e pasta. Campos semânticos (`topics`, `legislation_refs`) exigem LLM com validação via Pydantic.

---

## Parte 5 — Chunking / Splitting

**Estratégia:** Splitting recursivo por hierarquia jurídica, com tamanho de 900–1.100 caracteres e overlap de 150 caracteres.

**Justificativa detalhada:**

A CLT e documentos jurídicos têm estrutura hierárquica: Título → Capítulo → Artigo → Parágrafo → Inciso. A unidade semântica mínima é o artigo completo com seus parágrafos. Artigos curtos têm 100–200 caracteres; artigos longos chegam a 800–1.200 caracteres.

Testei na Aula 04 que chunks abaixo de 600 caracteres frequentemente cortam um artigo no meio — o chunk termina depois do caput mas antes do parágrafo único que inverte o sentido. Isso é catastrófico em jurídico: "o empregador pode dispensar sem justa causa" (caput) + "salvo nos casos previstos no §1°" (parágrafo perdido em outro chunk) = resposta errada.

Com 1.000 caracteres, um artigo médio cabe inteiro. O overlap de 150 caracteres cobre a transição entre artigos adjacentes, que frequentemente têm relação contextual.

Para ementas do TST: splitting por seção (ementa, relatório, voto, conclusão) como divisor primário, depois recursivo por tamanho.

Para pareceres internos (DOCX): `MarkdownHeaderTextSplitter` por cabeçalhos H2/H3.

**Overlap de 150, não 200:** Testei no projeto que 200 de overlap causava duplicação excessiva — a mesma frase aparecia em 3 chunks consecutivos, inflando resultados com chunks redundantes.

**Tabelas:** Nunca corto dentro de uma tabela. Se não cabe no chunk, vira chunk próprio. Uma tabela cortada ao meio é inútil — aprendi isso na Aula 02 ao converter artigos acadêmicos.

**Como saber se o chunking foi bom:**

Três evidências: (1) precision@5 — para as perguntas de teste, quantos dos top-5 chunks são realmente relevantes? (2) completude — a resposta tem lacunas que indicam trecho não recuperado? (3) inspeção manual de 20–30 chunks aleatórios para checar cortes no meio de artigos.

---

## Parte 6 — Embeddings

| Item | Detalhe |
|---|---|
| **Modelo escolhido** | `text-embedding-3-small` (OpenAI) |
| **Dimensão do embedding** | 1.536 |
| **Suporta português?** | Sim |
| **É multilíngue?** | Sim |
| **Tamanho máximo de entrada** | ~8.191 tokens |
| **É open source?** | Não |
| **Pode ser executado localmente?** | Não |
| **Possui API?** | Sim (OpenAI API / OpenRouter) |
| **Custo aproximado** | U$0,02 por 1M tokens |
| **Fonte** | https://platform.openai.com/docs/models/text-embedding-3-small |

**Por que esse modelo:**

Já usei o `text-embedding-3-small` nas Aulas 03 e 04 via OpenRouter e o desempenho em português foi sólido. O limite de 8.191 tokens é generoso — meus chunks de ~200 tokens têm margem confortável.

Custo estimado: 1.000 docs × 20 chunks × 200 tokens = ~4M tokens ≈ U$0,08. Custo irrelevante para a ingestão inicial.

**Alternativa descartada:** `multilingual-e5-large` (Microsoft, open source, local) — seria ótimo para sigilo, mas exige GPU. O escritório não tem infraestrutura local com GPU, tornando a latência em CPU inaceitável para uso interativo.

**Documentos sigilosos vs. API:** Para o conjunto mais sensível (teses internas), avalio `nomic-embed-text` via `ollama` em CPU — latência de 1–3 segundos por chunk é aceitável para ingestão batch noturna.

**Relação com chunking:** O limite de 8.191 tokens é muito maior que meus chunks de ~200 tokens. Isso significa que nunca precisarei truncar por limitação do modelo — a decisão de chunking é guiada pela semântica, não pelo limite técnico. Se tivesse escolhido `all-MiniLM-L6-v2` (512 tokens), teria que limitar chunks a ~400 tokens, forçando cortes em artigos longos.

---

# CENÁRIO B — Assistente de Manutenção Industrial

---

## Parte 1 — Identificação do problema

### 1.1 Descrição do problema

**Qual é o problema?**

Uma fábrica de alimentos de médio porte tem linhas de produção com ~80 equipamentos diferentes: enchedoras, seladores, pasteurizadores, esteiras, compressores. Os manuais estão em PDF, muitos em inglês ou italiano (da fabricante original), alguns traduzidos internamente em DOCX. Além dos manuais, existem ordens de serviço históricas (registros de manutenção passada) e boletins técnicos de recall ou atualização de peças.

Quando um técnico está na linha às 3h da manhã com um equipamento parado, ele não tem como procurar em um servidor de arquivos. Ele pega o celular, descreve o sintoma e quer saber: o que é, como consertar, se há peça de reposição.

**Quem usa?**

- **Técnicos de manutenção** (nível técnico em mecânica/elétrica, não em TI): consultam em campo, com o celular com uma mão, às vezes com ruído e pressa. Não toleram respostas longas.
- **Engenheiro de manutenção** (supervisor): faz análise de falha após o fato, no escritório, via web.
- **Almoxarife**: verifica especificação de peças de reposição antes de comprar.

**Que informação o usuário consulta?**

- Procedimentos de diagnóstico de falha (sintoma → causa → ação).
- Especificação de peças de reposição (código, fabricante, tolerâncias).
- Procedimentos de lubrificação e troca de óleo (frequência, tipo).
- Histórico de falha em determinado equipamento.

**De onde vêm as informações?**

- Manuais técnicos em PDF (idiomas: português, inglês, italiano, espanhol).
- Ordens de serviço preenchidas em papel e digitalizadas mensalmente (PDFs escaneados).
- Boletins técnicos dos fabricantes (HTML, PDF).
- Planilha de peças de reposição (Excel).

**Por que LLM sozinho não basta?**

Os equipamentos são específicos de cada fabricante, com nomes de peças e códigos proprietários. Um LLM genérico pode sugerir procedimento que não se aplica aquele modelo específico — ou pior, sugerir peça com código errado. Em manutenção industrial, usar a peça errada pode destruir o equipamento ou criar risco de segurança alimentar.

**Como o usuário acessa?**

API com app mobile (Android) interno — design simplificado, campos grandes, acessível com luvas. Resposta deve ser curta e direta, com link para a seção do manual.

**Três perguntas reais:**

1. *"A enchedora linha 3 tá vibrando muito e deu alarme E-47, o que é isso?"*
2. *"Qual o torque de aperto dos parafusos da cabeça da bomba do pasteurizador Alfa Laval P3?"*
3. *"Quando foi a última vez que fizeram manutenção preventiva no compressor de ar da sala 2? O que foi feito?"*

---

### 1.2 Por que RAG?

**RAG é adequado porque:**

Os manuais são documentos específicos de cada equipamento, privados (alguns têm NDAs), e contêm tabelas técnicas, esquemas e procedimentos passo a passo que nenhum LLM genérico conhece. A busca semântica é necessária porque o técnico não sabe o nome correto do componente — ele descreve o sintoma.

**Com que frequência muda?**

- Manuais: raramente (só quando fabricante emite revisão).
- Boletins técnicos: mensalmente, às vezes com urgência (recall).
- Ordens de serviço: diariamente.
- Planilha de peças: semanalmente.

**Exemplo concreto de resposta errada sem RAG:**

Pergunta: *"Qual o tipo de óleo para o redutor da enchedora Bosch SVE 2520?"*

LLM sem RAG: *"Redutores industriais geralmente utilizam óleo mineral ISO VG 220 ou 320."* — O manual da Bosch SVE 2520 especifica `Mobilgear 600 XP 220` com troca a cada 4.000h. Usar óleo genérico pode anular a garantia e acelerar desgaste do redutor.

---

### 1.3 Limitações — quando RAG não é a resposta

**Busca por palavra-chave:** Para código de alarme específico (ex: "E-47"), busca exata funciona melhor e mais rápida. Alarmes têm códigos exatos — semântica não ajuda.

**Banco de dados SQL:** "Quantas vezes o compressor da sala 2 falhou em 2024?" é SQL trivial; RAG tentaria responder lendo documentos e poderia errar na contagem.

**API direta:** A planilha de peças deveria ser banco de dados relacional com API de consulta. Para "qual o código da correia do transportador X?", busca exata na tabela é mais confiável.

**Regras determinísticas:** Intervalos de manutenção preventiva deveriam viver em um CMMS (Computerized Maintenance Management System), não em RAG.

**Combinação:** O ideal é RAG para diagnóstico e procedimento + SQL/CMMS para histórico e agendamento + busca exata para códigos de alarme e peças.

**Pergunta que banco relacional responderia melhor:**

*"Qual equipamento teve mais paradas não planejadas no último trimestre?"*

Exige agregar registros de ordens de serviço por equipamento e contar — RAG não consegue fazer isso com confiabilidade.

---

## Parte 2 — Organização dos documentos

**Tipos de arquivo:**

- PDF com texto selecionável: manuais modernos.
- PDF escaneado (imagem): ordens de serviço em papel, manuais antigos.
- DOCX: traduções e adaptações internas.
- XLSX: planilha de peças (não entra no RAG — vai para banco relacional).
- HTML/PDF: boletins técnicos.
- JPEG/PNG: fotos de equipamentos.

**Volume:** 2.500–4.000 documentos. Manuais: ~200 (grandes, 100–500 páginas cada). Ordens de serviço: ~2.000–3.000 (1–2 páginas cada). Boletins técnicos: ~300–500.

**Estrutura de pastas:**

```
documentos/
├── manuais/
│   ├── enchedoras/
│   ├── pasteurizadores/
│   ├── compressores/
│   ├── transportadores/
│   └── outros/
├── ordens_servico/
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
├── boletins_tecnicos/
│   ├── recalls/
│   └── atualizacoes/
├── fotos/
└── _obsoletos/
```

**Justificativa da estrutura:**

A subpasta por tipo de equipamento dentro de manuais permite filtrar por `equipment_type` antes da busca vetorial — reduz drasticamente o espaço de busca. Uma pergunta sobre a enchedora não deve vasculhar o manual do pasteurizador. A subpasta por ano em ordens de serviço permite descarte controlado de registros antigos.

**Controle de versão de manuais:** Igual ao Cenário A — `is_current` + `superseded_by`. Quando fabricante emite revisão R2, a R1 recebe `is_current = false`.

---

## Parte 3 — Pipeline de ingestão

### 3.1 Extração

**PDFs com texto selecionável:** `pymupdf4llm` para manuais estruturados.

**PDFs escaneados (principal desafio):** As ordens de serviço em papel são o maior problema — milhares de documentos, escritas à mão ou preenchidas com letra de forma irregular. Usaria:
1. `pytesseract` com pré-processamento via OpenCV (binarização, deskew) para texto impresso.
2. Google Document AI ou Azure Form Recognizer para escrita à mão.

Risco alto: letra mal reconhecida no código de uma peça ("O" virado "0") gera informação incorreta. Para ordens de serviço, armazeno o texto com flag de baixa confiança se o OCR score for < 0,85.

**Tabelas:** Críticas nos manuais técnicos. Para tabelas complexas com células mescladas (comuns em manuais europeus), uso GPT-4o multimodal para extrair como JSON estruturado.

**Imagens:** Os manuais têm diagramas de peças explodidas, esquemas elétricos — têm valor real. Processo:
1. Extraio a imagem do PDF.
2. Envio para GPT-4o / Gemini 1.5 Flash para gerar descrição textual: *"Diagrama de peças explodidas do cabeçote de enchimento: (1) Pistão, (2) Anel de vedação Viton, (3) Válvula de entrada, código VE-2240..."*
3. A descrição vira texto e é indexada como chunk. A imagem original é linkada via `image_ref`.

**Problema real neste cenário:** Manuais em italiano escaneados com 150dpi — OCR com 20–30% de caracteres errados. Solução: extrai → OCR → traduz (DeepL API) → indexa. Qualidade imperfeita, mas melhor que nada.

---

### 3.2 Limpeza e normalização

**O que remover:**
- Cabeçalhos repetidos em cada página (número de revisão, nome do fabricante).
- Páginas de índice e lista de figuras.
- Avisos legais e disclaimers repetidos.
- Em ordens de serviço: campos vazios não preenchidos.

**O que padronizar:**
- Unidades: manuais europeus usam vírgula decimal (1,5 bar), americanos usam ponto (1.5 psi). Normalizo para ponto e SI quando possível — mas registro a unidade original nos metadados.
- Idioma: documentos em italiano e inglês são traduzidos antes da indexação, armazenando idioma original como metadado.

**O que posso perder ao limpar demais:**

Risco específico: remover códigos de peça. Um código como `SVE-2520-47B` pode parecer ruído. Minha regra: nunca removo strings que seguem padrões de código de equipamento ou peça.

---

### 3.3 Frequência de ingestão

- **Manuais:** one-shot + reprocessamento quando `md5_hash` muda.
- **Ordens de serviço:** ingestão diária agendada. Toda madrugada, o pipeline varre a pasta do dia e processa novas ordens.
- **Boletins técnicos:** mensal + imediato para recalls (urgência).

Sempre por documento individual — nunca reindexação completa da base.

---

## Parte 4 — Metadados

### 4.1 Metadados do documento

```json
{
  "document_id": "man-bosch-sve2520-r3",
  "title": "Manual Técnico Bosch SVE 2520 — Revisão 3",
  "manufacturer": "Bosch Packaging Technology",
  "equipment_type": "enchedora",
  "equipment_model": "SVE 2520",
  "equipment_line": "Linha 3",
  "source_language": "de",
  "document_type": "manual_tecnico",
  "revision": "R3",
  "created_at": "2021-06-01",
  "updated_at": "2023-11-10",
  "ingested_at": "2026-01-15",
  "is_current": true,
  "superseded_by": null,
  "valid_until": null,
  "access_level": "interno",
  "md5_hash": "f7c2...",
  "has_images": true,
  "translated": true,
  "original_language": "de"
}
```

**Por que cada campo:**

- `equipment_type` e `equipment_model`: filtros primários na busca. Pergunta sobre enchedora não deve trazer manual do pasteurizador.
- `equipment_line`: permite filtrar por linha de produção ("só documentos da Linha 3").
- `manufacturer`: relevante para boletins técnicos de recall — filtra por fabricante afetado.
- `source_language` / `translated`: indica se texto indexado é tradução — rastrear imprecisões.
- `revision`: para confirmar que está usando o manual mais atualizado.
- `has_images`: indica que existem chunks de descrição de imagem associados.

### 4.2 Metadados do chunk

```json
{
  "document_id": "man-bosch-sve2520-r3",
  "chunk_id": "man-bosch-sve2520-r3-034",
  "page": 47,
  "section": "Diagnóstico de Falhas",
  "subsection": "Alarme E-47",
  "chunk_type": "procedimento",
  "equipment_type": "enchedora",
  "equipment_model": "SVE 2520",
  "equipment_line": "Linha 3",
  "document_type": "manual_tecnico",
  "is_current": true,
  "image_ref": "man-bosch-sve2520-r3_p47_fig3.jpg",
  "text": "..."
}
```

**Filtro indispensável:** `equipment_model` + `is_current`. Sem filtrar `equipment_model = SVE 2520`, o sistema pode trazer procedimento de outro modelo onde o E-47 significa algo completamente diferente — ou onde o reset tem parâmetros diferentes.

**Citação ao usuário (app mobile):**
> *📖 Manual Bosch SVE 2520 (Rev. 3) — p. 47, Seção: Diagnóstico / Alarme E-47*

**Metadado mais caro para acrescentar depois:** `equipment_model` e `equipment_line`. Se esquecidos, tenho que reler todos os ~200 manuais (muitos com 500 páginas) para identificar o modelo — e para manuais em idioma estrangeiro, exige LLM para identificar a nomenclatura do fabricante.

**Como extrair:** `equipment_type` e `equipment_model` vêm do nome da pasta e arquivo. `equipment_line` vem de mapa de configuração mantido pelo engenheiro de manutenção. `section` e `subsection` vêm dos cabeçalhos Markdown após conversão.

---

## Parte 5 — Chunking / Splitting

**Estratégia:** Splitting hierárquico por seção do manual, com tamanho alvo de 600–800 caracteres e overlap de 100 caracteres.

**Justificativa detalhada:**

Manuais industriais são estruturados por seção funcional: Instalação, Operação, Manutenção, Diagnóstico de Falhas, Peças de Reposição. A unidade semântica relevante é o procedimento — uma sequência de passos que tipicamente ocupa 300–800 caracteres.

Uso chunks menores (600–800) que no Cenário A (900–1.100) porque:
1. Procedimentos são mais curtos e autocontidos.
2. A pergunta do técnico é pontual — ele quer a resposta do alarme E-47, não contexto amplo.
3. Chunks menores = mais precisão na recuperação. O técnico precisa de resposta direta, não de parágrafo longo.

O overlap de 100 caracteres (menor que no Cenário A) cobre a transição entre passos sem ser excessivo para documentos curtos como ordens de serviço.

**Ordens de serviço (1–2 páginas):** Sem chunking — o documento inteiro vira um único chunk. São curtos o suficiente e a unidade semântica é o registro completo (data + equipamento + problema + solução).

**Tabelas de alarmes:** Row-level chunking — cada linha (código + descrição + causa + ação) vira um chunk independente. A busca por "alarme E-47" deve encontrar especificamente a linha E-47, não a tabela inteira de 50 alarmes.

**Imagens:** A descrição textual gerada pelo LLM vira chunk vinculado ao chunk de texto via `image_ref`. A imagem em si não é indexada semanticamente.

**Como saber se o chunking foi bom:**

Testo com as 3 perguntas de referência. Para "deu alarme E-47, o que é isso?", o chunk correto deve aparecer no top-3. E o teste mais importante: um técnico de manutenção real lê a resposta e confirma se é utilizável? Esse teste humano supera qualquer métrica automática.

---

## Parte 6 — Embeddings

| Item | Detalhe |
|---|---|
| **Modelo escolhido** | `multilingual-e5-large-instruct` (Microsoft) |
| **Dimensão do embedding** | 1.024 |
| **Suporta português?** | Sim |
| **É multilíngue?** | Sim (94+ idiomas) |
| **Tamanho máximo de entrada** | 512 tokens |
| **É open source?** | Sim (Apache 2.0) |
| **Pode ser executado localmente?** | Sim (via HuggingFace / Ollama) |
| **Possui API?** | Via HuggingFace Inference API |
| **Custo aproximado** | Gratuito (local) |
| **Fonte** | https://huggingface.co/intfloat/multilingual-e5-large-instruct |

**Por que esse modelo:**

Diferente do Cenário A, aqui a confidencialidade é ainda mais crítica — manuais com NDA e dados operacionais sensíveis. Rodar o embedding localmente elimina o risco de envio de dados a servidores externos.

O suporte multilíngue nativo é essencial: manuais em alemão, italiano, inglês e português precisam ser comparados semanticamente com perguntas em português. O `multilingual-e5-large-instruct` foi treinado especificamente para recuperação multilíngue, e seus benchmarks no MTEB em retrieval multilíngue superam o `text-embedding-3-small` em vários idiomas europeus.

O limite de 512 tokens implica que meus chunks de 600–800 caracteres (~120–160 tokens) ficam bem dentro do limite — sem truncamento.

**Alternativa descartada:** `text-embedding-3-small` — descartado por confidencialidade (NDAs). Avaliei também `paraphrase-multilingual-mpnet-base-v2` (mais leve), mas desempenho em recuperação técnica é inferior ao `multilingual-e5-large-instruct` segundo benchmarks do MTEB.

**Documentos sigilosos vs. API:** Sim, isso mudou completamente a escolha. No Cenário A, a API foi justificada pela ausência de GPU e custo baixo. No Cenário B, NDAs e sigilo operacional justificam rodar localmente mesmo com latência maior.

**Relação com chunking:** O limite de 512 tokens (≈2.048 caracteres) orienta o tamanho máximo dos chunks. Meus chunks de 600–800 caracteres (~150–200 tokens) ficam com margem confortável. Se tivesse optado por chunks de 2.000 caracteres, estaria arriscando truncamento. Essa margem de segurança foi fator na escolha do tamanho de chunk.

---

# Arquitetura Final

## Cenário A — Diagrama (Assistente Jurídico)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INGESTÃO                                   │
│                                                                     │
│  PDF/DOCX → pymupdf4llm → Limpeza/Normalização                     │
│                                    ↓                                │
│                         LLM (metadados via Pydantic)               │
│                                    ↓                                │
│                    Chunking Recursivo 900-1100 chars                │
│                         overlap 150 chars                           │
│                                    ↓                                │
│                  text-embedding-3-small (OpenAI API)               │
│                                    ↓                                │
│               Banco Vetorial (Qdrant / pgvector)                   │
└─────────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────────┐
│                          CONSULTA                                   │
│                                                                     │
│  Usuário (web/mobile)                                               │
│      ↓                                                              │
│  Pergunta em linguagem natural                                      │
│      ↓                                                              │
│  Filtros: category, is_current, access_level                       │
│      ↓                                                              │
│  Embedding da query (text-embedding-3-small)                       │
│      ↓                                                              │
│  Busca vetorial → Top-5 chunks relevantes                          │
│      ↓                                                              │
│  Montagem do prompt (pergunta + chunks + instrução de citação)     │
│      ↓                                                              │
│  LLM (GPT-4o / Claude) → Resposta com citação de fonte            │
│      ↓                                                              │
│  "Fonte: Acórdão TST — RR-1001, p.3, Ementa (15/03/2024)"        │
└─────────────────────────────────────────────────────────────────────┘
```

**Tabela de decisões — Cenário A:**

| Etapa | Decisão | Justificativa em uma linha |
|---|---|---|
| Extração | `pymupdf4llm` + OCR fallback | Testado no projeto; bom para PDFs jurídicos bem formatados |
| Limpeza | Remove rodapés/cabeçalhos, normaliza UTF-8, preserva `Art.`/`§` | Artigos legais são a âncora semântica crítica |
| Chunking | Recursivo, 900–1.100 chars, overlap 150 | Artigo CLT médio cabe inteiro; overlap cobre transição entre artigos |
| Metadados | `category`, `is_current`, `topics`, `legislation_refs` via LLM | Filtros de busca e citação de fonte com fundamento legal |
| Embeddings | `text-embedding-3-small` via API | Custo baixo, português sólido, margem de tokens confortável |

**Riscos e limitações — Cenário A:**

- O sistema não calcula prazos — se o usuário perguntar "meu prazo vence quando?", o LLM pode tentar calcular e errar.
- Jurisprudência do TST muda — se a ingestão semanal falhar, o sistema responde com dados desatualizados sem saber disso.
- Para documentos sigilosos (teses internas), o uso da API OpenAI representa risco de dados que precisa ser gerenciado contratualmente.
- PDFs com camada de texto corrompida (problema visto na Aula 02) contaminam a base e exigem inspeção periódica.

---

## Cenário B — Diagrama (Manutenção Industrial)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INGESTÃO                                   │
│                                                                     │
│  PDF texto  → pymupdf4llm                                          │
│  PDF scan   → OCR (pytesseract / Document AI)                      │
│  Imagens    → GPT-4o / Gemini 1.5 (descrição textual)             │
│      ↓                                                              │
│  Tradução (DeepL API) para PT-BR                                   │
│      ↓                                                              │
│  Limpeza → Normalização de unidades → LLM (metadados via Pydantic) │
│      ↓                                                              │
│  Chunking por seção (600–800 chars, overlap 100)                   │
│  Row-level para tabelas de alarmes                                  │
│  Documento completo para ordens de serviço                         │
│      ↓                                                              │
│  multilingual-e5-large-instruct (LOCAL, CPU)                       │
│      ↓                                                              │
│  Banco Vetorial LOCAL (Qdrant self-hosted)                         │
└─────────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────────┐
│                      CONSULTA (App Mobile)                          │
│                                                                     │
│  Técnico → app Android (interface simplificada)                    │
│      ↓                                                              │
│  Pergunta ou seleção de equipamento + sintoma                      │
│      ↓                                                              │
│  Filtros: equipment_model, equipment_line, is_current              │
│      ↓                                                              │
│  Embedding da query (multilingual-e5 local)                        │
│      ↓                                                              │
│  Busca vetorial → Top-3 chunks (mais restrito)                     │
│      ↓                                                              │
│  Prompt compacto → Resposta em 2–4 linhas + link para manual      │
│      ↓                                                              │
│  "📖 Manual Bosch SVE 2520 R3 — p.47, Alarme E-47"               │
└─────────────────────────────────────────────────────────────────────┘
```

**Tabela de decisões — Cenário B:**

| Etapa | Decisão | Justificativa em uma linha |
|---|---|---|
| Extração | pymupdf4llm + OCR + GPT-4o para imagens | Manuais multimodais exigem tratamento de diagrama; OS escaneadas exigem OCR |
| Limpeza | Remove disclaimers, normaliza unidades para SI | Unidades mistas confundem o modelo; disclaimers inflam tokens sem valor |
| Chunking | Seção 600–800 chars, row-level para tabelas, doc completo para OS | Granularidade adequada ao tipo de consulta do técnico em campo |
| Metadados | `equipment_model`, `equipment_line`, `is_current` como filtros | Sem filtro por modelo, sistema traz procedimento errado |
| Embeddings | `multilingual-e5-large-instruct` local | NDAs impedem API externa; multilinguismo nativo essencial |

**Riscos e limitações — Cenário B:**

- OCR de ordens de serviço manuscritas tem qualidade variável — chunks corrompidos podem contaminar respostas.
- Rodar embedding localmente em CPU é lento — manual de 500 páginas pode levar 15–30 minutos na ingestão.
- O sistema não substitui o CMMS para agendamento de preventiva.
- Tradução automática de termos técnicos específicos pode ser imprecisa.
- Sem GPU dedicada, a ingestão diária de ordens de serviço pode acumular fila em períodos de alto volume.

---

# Comparação entre os dois cenários

## Decisões diferentes — e por quê

| Aspecto | Cenário A (Jurídico) | Cenário B (Industrial) | Razão da diferença |
|---|---|---|---|
| **Modelo de embedding** | API externa (OpenAI) | Local (multilingual-e5) | NDAs no industrial > sigilo jurídico gerenciável via contrato |
| **Tamanho de chunk** | 900–1.100 chars | 600–800 chars | Artigo de lei é mais longo que procedimento técnico |
| **Overlap** | 150 chars | 100 chars | Transição entre artigos CLT é mais contextualmente dependente |
| **Tratamento de imagens** | Descarta (logos ornamentais) | Indexa descrição (diagramas críticos) | Em jurídico, imagens são decorativas; em industrial, são informação |
| **Tradução** | Não necessária | Sim (DE, IT, EN → PT) | Legislação brasileira é em PT; manuais industriais são multilíngues |
| **Frequência de ingestão** | Semanal (jurisprudência) | Diária (ordens de serviço) | OS são geradas continuamente; jurisprudência vem em lotes mensais |
| **Interface** | Web + mobile eventual | Mobile-first | Técnico está em campo; advogado está no escritório |

## Decisões iguais — reflexão

Ambos usam:
- `pymupdf4llm` para extração de PDFs com texto.
- Chunking recursivo como estratégia base.
- `is_current` + `superseded_by` para controle de versão.
- Ingestão incremental por hash MD5.
- LLM com output estruturado (Pydantic) para extração de metadados.

Essas decisões são iguais porque são boas práticas gerais de RAG, não porque repeti sem pensar. O controle de versão por `is_current` é necessário em qualquer cenário com documentos que mudam — seja a CLT ou o manual de manutenção. A ingestão incremental por hash é eficiente independente do volume. São princípios que se justificam em ambos os contextos.

## Se tivesse que construir apenas um

Escolheria o **Cenário B (Manutenção Industrial)**.

Por três razões:
1. **Impacto imediato mensurável:** uma linha parada por 2 horas em uma fábrica tem custo concreto em reais. O ganho de 30 minutos de diagnóstico do técnico tem ROI calculável e rápido.
2. **Menor risco regulatório:** no cenário jurídico, uma resposta errada pode ter consequência legal grave. No industrial, a resposta do sistema é sempre validada pelo técnico antes de agir — ele tem o contexto físico que o sistema não tem.
3. **Ambiente técnico mais propício:** a fábrica tem servidor local, viabilizando o modelo de embedding local sem depender de aprovação jurídica para uso de API externa com dados sigilosos.

---

# Uso de IA nesta atividade

Utilizei IA (Claude Sonnet via Antigravity/Google) como assistente de estruturação e revisão, não como gerador de conteúdo. O fluxo foi:

1. **Minha parte:** escolha dos cenários (baseados em contextos que conheço), todas as decisões técnicas e justificativas, redação de cada seção.
2. **IA como apoio:** verificação de coerência interna ("a decisão de chunking do Cenário B conflita com o limite de tokens do modelo?"), sugestão de estrutura de tabelas, revisão de texto.
3. **Verificação das fontes:** os dados técnicos dos modelos de embedding (dimensões, limites de token, suporte a idiomas) foram verificados diretamente nas páginas de documentação da OpenAI e HuggingFace — não confiei no que a IA disse sobre eles.
4. **O que avaliei na resposta da IA:** consistência técnica (não aceitar afirmação sobre limite de tokens sem checar a documentação), relevância ao cenário específico (respostas genéricas foram descartadas).

---

# Referências

1. **OpenAI — text-embedding-3-small documentation:**
   https://platform.openai.com/docs/models/text-embedding-3-small

2. **HuggingFace — multilingual-e5-large-instruct:**
   https://huggingface.co/intfloat/multilingual-e5-large-instruct

3. **MTEB Leaderboard — benchmarks de modelos de embedding:**
   https://huggingface.co/spaces/mteb/leaderboard

4. **LangChain Text Splitters — documentação oficial:**
   https://python.langchain.com/docs/concepts/text_splitters/

5. **pymupdf4llm — documentação:**
   https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/

6. **Google Document AI — OCR para formulários:**
   https://cloud.google.com/document-ai

7. **DeepL API — tradução técnica:**
   https://developers.deepl.com/docs

8. **CLT — Decreto-Lei nº 5.452/1943 consolidado (Planalto):**
   https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm

9. **Lei 13.467/2017 — Reforma Trabalhista:**
   https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13467.htm

10. **Qdrant — banco vetorial self-hosted:**
    https://qdrant.tech/documentation/

11. **Tesseract OCR:**
    https://github.com/tesseract-ocr/tesseract

12. **OpenCV — pré-processamento de imagem para OCR:**
    https://opencv.org/

13. **Mermaid Live (ferramenta de diagramação):**
    https://mermaid.live/
