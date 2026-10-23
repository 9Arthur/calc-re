# `trabalho/ptbr` — pacote de recursos pt-BR (`./binarios-ptbr`)

Data: 2026-10-22. Análise só estática. `binarios-ptbr/` não foi alterado: `sha256sum -c hashes-originais.txt`
dá 19/19 OK, antes e depois do trabalho.

Legenda: **[O]** OBSERVADO (bytes, offsets, metadados) · **[I]** INFERIDO.

## 1. Arquivos produzidos

| Arquivo | Conteúdo |
|---|---|
| `recursos.json`, `CEngineStrings.tsv`, `Resources.tsv` | saída de `python3 -I trabalho/scripts/pri_dump.py binarios-ptbr/resources.pri trabalho/ptbr --esquema binarios/resources.pri` (mesmo formato de `trabalho/pri`). Os TSV têm as colunas `PT-BR` e `PT-PT` |
| `validacao-pri.json` | saída de `python3 -I trabalho/scripts/pri_valida.py binarios/resources.pri trabalho/pri binarios-ptbr/resources.pri trabalho/ptbr --ids trabalho/cengine-ids.json --saida trabalho/ptbr/validacao-pri.json` |
| `../scripts/blockmap_check.py` | confere os arquivos de um pacote contra o `AppxBlockMap.xml` |

## 2. Identidade e integridade do pacote [O]

- `binarios-ptbr/AppxManifest.xml`: `Identity Name="Microsoft.WindowsCalculator"`,
  `Publisher="CN=Microsoft Corporation, …"`, **`Version="11.2607.0.0"`**, `ResourceId="split.language-pt"`,
  `<ResourcePackage>true</ResourcePackage>`, `Resources`: `pt-br`, `pt-pt`. É a mesma identidade e a mesma
  versão do pacote principal (`binarios/AppxManifest.xml`, Fase 1).
- BlockMap (`python3 -I trabalho/scripts/blockmap_check.py binarios-ptbr`): HashMethod SHA-256; 2 arquivos.
  `resources.pri` declarado com 53 616 bytes = tamanho no disco, e o único bloco de 64 KiB confere
  (`UC5VCvHGjZ/AGNa9t/Rcj62Ocd5qbLrfB47iGp033/I=`). `AppxManifest.xml` também confere.
  O SHA-256 do arquivo inteiro é `502e550a…26f12` (igual a `hashes-originais.txt`).
- Assinatura (`AppxSignature.p7x`, cabeçalho `PKCX` + PKCS#7): o conteúdo assinado (SpcIndirectData,
  marcador `APPX` no offset 144) traz `AXBM` = `7c8c4955…24ff9b0` = SHA-256 de `binarios-ptbr/AppxBlockMap.xml`.
  A cadeia de hashes fica assim: **assinatura → BlockMap → `resources.pri`**. A verificação criptográfica da
  assinatura não foi feita (mesma ressalva da Fase 1, L6).
- Certificado de assinatura igual ao do pacote principal (`CN=Microsoft Corporation`, válido de 2026-08-05
  17:38:20Z a 2026-08-08). O carimbo de tempo RFC 3161 (TSTInfo `genTime`) é **2026-08-05 17:48:44.643Z**,
  com serial da TSA `6A5F95700B5C`. No pacote principal, é **2026-08-05 17:48:50.877Z**, com serial `6A5F95700C19`.
  Ou seja, os dois foram carimbados com 6 s de diferença, com seriais da TSA na mesma faixa (`6A5F9570…`).
- Esquema: a seção `[mrm_hschemaex]` do PRI pt-BR está **vazia** (40 bytes = só cabeçalho + rodapé). O
  resource map traz a referência de esquema: versão 1.0, checksum **0x55A27B9B**, 661 escopos, 1323 itens,
  `ms-appx://Microsoft.WindowsCalculator/`. São exatamente os valores do `[mrm_hschemaex]` do PRI principal.

**Sobre a data de 2025** informada pelo usuário: os arquivos copiados para `./binarios-ptbr` têm mtime local de
2026-10-22, que é a hora da cópia. A data de 2025 não é observável nos arquivos daqui. [I] Ela deve vir da
data de entrada ZIP do `.msix` ou da pasta em `WindowsApps`. Os empacotadores costumam gravar ali uma data
fixa ou a do arquivo de origem, e isso não indica a versão. As evidências de versão acima, que são o manifesto,
a cadeia assinatura→BlockMap→PRI, o carimbo de tempo de 2026-08-05 junto com o do principal e o checksum de
esquema idêntico, são todas internas e assinadas. **Conclusão [O+I]: o `resources.pri` pt-BR pertence ao
build 11.2607.0.0.**

## 3. Conteúdo [O]

- 6 seções: `[mrm_decn_info]`, `[mrm_pridescex]`, `[mrm_hschemaex]` (vazia), `[mrm_res_map2_]` e 2 ×
  `[mrm_dataitem]`. Qualificadores: Language = `PT-BR` (prioridade 700) e `PT-PT` (700). Decisão 2 = conjuntos
  [PT-PT, PT-BR] e decisão 0 = vazia.
- O resource map tem 1138 dos 1323 itens do esquema, em grupos esparsos (19 entradas item→grupo e 15 grupos):
  - **1032 itens com valor PT-BR e PT-PT**. É exatamente o mesmo conjunto das 1032 chaves que têm EN-GB no
    pacote principal;
  - **106 itens com decisão vazia**, sem valor neste pacote. Todos estão entre as 242 chaves só-EN-US do pacote
    principal. Exemplos: `CEngineStrings/11` (`÷`), `CEngineStrings/12` (`×`), atalhos de teclado.
- `CEngineStrings` traduzidas: só as 9 mensagens de erro do motor.

| chave | EN-US | PT-BR | PT-PT | data item PT-BR |
|---|---|---|---|---|
| 99 | Cannot divide by zero | Não é possível dividir por zero | (igual) | 4/701 @0x98C0 |
| 100 | Invalid input | Entrada inválida | (igual) | 4/899 @0xA598 |
| 101 | Result is undefined | Resultado indefinido | O resultado é indefinido | 4/898 @0xA580 |
| 105 | Not enough memory | Memória insuficiente | (igual) | 4/897 @0xA568 |
| 107, 119, 120 | Overflow | Estouro | Capacidade excedida | 4/895 @0xA548 |
| 108, 118 | Result not defined | Resultado não definido | (igual) | 4/896 @0xA550 |

- [I] Os símbolos e nomes de função do motor (`÷`, `×`, `+`, `sin`, `cis`, `sqr`, `negate`…) não são
  localizados. No Windows em pt-BR eles devem vir do candidato EN-US do pacote principal, por fallback do
  ResourceLoader/MRT. Esse fallback não foi observado.
- Outras mensagens úteis (`Resources.tsv`): `DivideByZero` = "Não é possível dividir por zero";
  `Overflow` = "Estouro (o número é muito grande)" (PT-PT "Transbordo (o número é demasiado grande)");
  `Format_MaxDigitsReached` = "Nº máximo de dígitos alcançado. %1"; `Format_CalculatorResults` =
  "A exibição é %1". `Format_CalculatorExpression` vale "Expression é %1" no PT-BR, ou seja, está
  parcialmente sem tradução no próprio recurso (PT-PT: "Expressão é %1").

## 4. Uso como checagem extra do parser [O]

`validacao-pri.json → alinhamento_en_pt`: 1032 chaves comuns EN-US/PT-BR, 212 com texto idêntico (nomes
próprios, siglas, unidades); 0 divergências nas 6 chaves só de símbolos/dígitos; 0 divergências na contagem de
placeholders `%n`; 0 chaves PT sem EN. Os nomes de dígitos `num0..9Button` dão Zero, Um, Dois, Três, Quatro,
Cinco, Seis, Sete, Oito, Nove (10/10). A distinção PT-BR/PT-PT é coerente com cada variante: "muito grande" vs.
"demasiado grande", "Estouro" vs. "Capacidade excedida". Isso confirma que os conjuntos de qualificadores não
estão trocados.
