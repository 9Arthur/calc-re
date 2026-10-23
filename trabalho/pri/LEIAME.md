# `trabalho/pri` — parse do `resources.pri` e dos XBF embutidos

Data: 2026-10-22. Alvo: `binarios/resources.pri` (608 760 bytes,
SHA-256 `ca2ef0ca049e95ce77d165ff4f5ce73d12fad30dba2551cfe6dc9ac8518c531a`).
Análise só estática. Nenhum binário do pacote foi executado e `binarios/` não foi alterado:
`sha256sum -c hashes-originais.txt` dá 15/15 OK depois do trabalho.

Legenda: **[O]** OBSERVADO, lido direto dos bytes, com offset, seção ou índice. **[I]** INFERIDO.
Todos os offsets são do arquivo `resources.pri`, salvo quando o texto indica um `.xbf`.

## 1. O que foi produzido

> **Nota de publicação (2026-10-23).** `../scripts/xbf_dump.py` e `../scripts/dados/xbf_framework_ids.json` não
> estão no repositório público: a desmontagem do fluxo de nós foi portada de chausner/XbfTools (Apache-2.0) e a
> tabela de IDs vem das tabelas desse projeto. Ficaram fora para não publicar obra derivada sem os avisos da
> licença. O layout do formato que o script implementa está descrito nas seções 5 e 5.1. As saídas listadas
> abaixo (`xbf/`, `xbf-nos/`, `xbf-strings/`, TSV e JSON) também não são publicadas, por serem extraídas do
> `resources.pri` da Microsoft.
>
> O parser `../scripts/pri_dump.py` também não está no repositório público: ele foi escrito tendo o código de
> chausner/PriTools (Apache-2.0) como referência e fica fora até a atribuição ser resolvida. O formato que ele
> implementa está descrito neste documento.

| Arquivo | Conteúdo |
|---|---|
| `../scripts/pri_dump.py` | parser PRI (biblioteca padrão). Uso: `python3 -I trabalho/scripts/pri_dump.py binarios/resources.pri trabalho/pri`. Para pacote de recursos (esquema vazio): acrescentar `--esquema binarios/resources.pri` (§8) |
| `../scripts/pri_valida.py` | validador independente do parser (§8); saída em `trabalho/ptbr/validacao-pri.json` |
| `../scripts/xbf_dump.py` | extrator e parser dos XBF. Uso: `python3 -I trabalho/scripts/xbf_dump.py binarios/resources.pri trabalho/pri --winmd trabalho/winmd/CalculatorApp.ViewModel.json` (rodar depois do `pri_dump.py`) |
| `../scripts/dados/xbf_framework_ids.json` | tabela de IDs de tipo, propriedade e enum do framework XAML, convertida de XbfTools (ver §2) |
| `recursos.json` | tudo o que foi interpretado: cabeçalho, TOC, 137 seções, descritor, qualificadores, conjuntos, decisões, resumo do esquema, resource map, data items, contagens, os 1323 itens com nome completo e candidatos (qualificadores, tipo de valor, origem `seção/item/offset/comprimento`, valor decodificado ou `sha256`) e `validacao` |
| `CEngineStrings.tsv`, `Resources.tsv` | `chave<TAB>idioma<TAB>valor`, com `\\`, `\t`, `\r` e `\n` escapados. 117 e 2189 linhas de dados |
| `blobs.json` | os 32 candidatos `EmbeddedData`: nome, offset, comprimento, sha256 |
| `xbf/<caminho>.xbf` | os 32 XBF copiados byte a byte. `<caminho>` é o nome PRI sem `Files/`, por exemplo `xbf/Views/MainPage.xbf` |
| `xbf-strings/<caminho>.txt` | cabeçalho, tabela de strings (índice, offset no .xbf, valor JSON), assemblies, namespaces de tipo, tipos, propriedades, namespaces XML, seções de nós e validações |
| `xbf-nos/<caminho>.txt` | desmontagem do fluxo de nós, uma linha por comando, com offset no .xbf e seção de nós. É heurística: ver §6 item 5 e §5.1 |
| `xbf-resumo.json` | por XBF: contagens, validações, notas, `x:Class`, `x:Name`, `x:Uid`, tipos e propriedades que não são do framework, pares propriedade=valor, bindings, botões e cruzamento com os nomes do view model |
| `xbf-botoes.tsv` | 266 objetos com `ButtonId` ou `CommandParameter`: XBF, `x:Name`, tipo, connectionId, valor, valor numérico do enum no winmd, AutomationId, texto EN-US do `AutomationProperties.Name` e do atalho |

Os XBF ficam em subpastas espelhando o caminho do PRI, e não em `xbf/<nome>.xbf` plano.
Motivo: há nomes repetidos em pastas diferentes, por exemplo `CommunityToolkit…/Themes/Generic.xbf` e
`GraphControl/Themes/generic.xbf`, que colidiriam num sistema de arquivos sem distinção de maiúsculas.

## 2. Referências de formato consultadas

Só documentação e código de parsers genéricos, sem nada específico da Calculadora (CLAUDE.md):
- `chausner/PriTools` (Apache-2.0), commit `765d4544`: `Package Resource Index File Format.md` e
  `PriFormat/Sections/*.cs`.
- `chausner/XbfTools` (Apache-2.0), commit `dbeadcd7`: `XbfFormat/XbfHeader.cs`, `XbfReader.cs`,
  `XbfType.cs`, `XbfProperty.cs` etc., e `XbfFrameworkTypes.cs`. Segundo o comentário do próprio arquivo,
  essas tabelas vêm do `GenXbf.dll` do Windows SDK 10.0.26100.0.

O `.md` do PriTools diverge do arquivo nas constantes de rodapé. Ele diz `0xF5DEDEFA` e `0xFFDEDEFA`.
Os bytes reais são `DE FA F5 DE`, ou seja u32 LE `0xDEF5FADE`, em todo fim de seção (ex.: 0x19D8), e
`DE FA FF DE` = `0xDEFFFADE` no rodapé do arquivo (0x949E8). O código C# do PriFormat usa esses mesmos
valores. [O]

## 3. Layout PRI implementado, com offsets deste arquivo

### 3.1 Cabeçalho, TOC e rodapé [O]
- `0x00` `char[8]` `mrm_pri2`; `0x08` u16 0; `0x0A` u16 1; `0x0C` u32 tamanho total 608760 (= tamanho do
  arquivo); `0x10` u32 offset da TOC `0x20`; `0x14` u32 offset da 1ª seção `0x1140`; `0x18` u16 nº de
  seções 137; `0x1A` u16 `0xFFFF`; `0x1C` u32 0.
- TOC: 137 entradas de 32 bytes em `0x20`–`0x113F`. Cada uma: `char[16]` id, u16 flags, u16 section
  flags, u32 qualificador, u32 offset relativo a `0x1140`, u32 comprimento.
- Cada seção tem cabeçalho de 32 bytes (`char[16]` id, u32 qualificador, u16 flags, u16 section flags,
  u32 comprimento, u32 0), conteúdo e rodapé de 8 bytes (u32 `0xDEF5FADE`, u32 comprimento). Seções
  contíguas e alinhadas a 8. Flags e qualificadores valem 0 em todas as 137.
- Rodapé do arquivo em `0x949E8`: u32 `0xDEFFFADE`, u32 608760, `char[8]` `mrm_pri2`.

### 3.2 Seções [O]
| # | identificador | offset no arquivo | comprimento | conteúdo |
|---|---|---|---|---|
| 0 | `[mrm_decn_info]\0` | 0x1140 | 2208 |  |
| 1 | `[mrm_pridescex]\0` | 0x19E0 | 336 |  |
| 2 | `[mrm_hschemaex] ` | 0x1B30 | 75624 |  |
| 3 | `[mrm_res_map2_]\0` | 0x14298 | 25800 |  |
| 4 | `[mrm_dataitem] \0` | 0x1A760 | 17848 | 891 strings, 0 blobs, 14232 bytes de dados |
| 5 | `[mrm_dataitem] \0` | 0x1ED18 | 3072 | 249 strings, 0 blobs, 2024 bytes de dados |
| 6 | `[mrm_dataitem] \0` | 0x1F918 | 459144 | 12 strings, 25 blobs, 458844 bytes de dados |
| 7–135 | `[mrm_dataitem] \0` | 0x8FAA0 … | 104–480 | 1 a 7 strings cada (caminhos de imagens por conjunto de qualificadores) |
| 136 | `[mrm_dataitem] \0` | 0x94960 | 136 | 1 string, 0 blobs, 80 bytes de dados |

### 3.3 `[mrm_pridescex]` (conteúdo em 0x1A00) [O]
Campos: u16 flags = 2 (`IsDeploymentMergeable`); u16 included-file-list = `0xFFFF` (ausente); u16 0;
nº de seções hschema/decision/resource map (1/1/1); resource map primário = seção 3; nº de seções
referenced-file = 0; nº de dataitem = 133; u16 0. Seguem as listas de índices: hschema [2], decision [0],
resmap [3], dataitem [4..136]. Elas coincidem com os identificadores da TOC.

### 3.4 `[mrm_decn_info]` (conteúdo em 0x1160) [O]
Cabeçalho com 6×u16: 23 qualificadores distintos, 23 qualificadores, 133 conjuntos, 9 decisões,
468 entradas na tabela de índices e 95 caracteres de valores. Depois vêm:
- decisões: (u16 1º índice, u16 n);
- conjuntos: (u16 1º índice, u16 n);
- qualificadores: (u16 distinto, u16 prioridade, u16 fallback, u16 0);
- distintos: (u16 atom, u16 tipo, u16 operador, u16 tipo de valor, u32 offset do valor em caracteres);
- tabela de índices u16;
- bloco de valores UTF-16 em 0x1918.

Qualificadores, no formato índice:tipo=valor (prioridade/fallback):
0 Language=(vazio, neutro) (0/0); 1 Language=EN-GB (700/976); 2 Language=EN-US (700/1000);
3 Contrast=BLACK; 9 Contrast=WHITE; 10 Scale=200; 11–13 AlternateForm=COLORFUL/LIGHTUNPLATED/UNPLATED;
4–8 e 14–22 TargetSize=16, 20, 24, 32, 64, 256, 30, 36, 40, 48, 60, 72, 80, 96.

Decisões e nº de conjuntos: d0=0 (nenhum item usa), d1=1 (neutro, 37 itens), d2=1 (só EN-US, 242 itens),
d3=2 (EN-US+EN-GB, 1032 itens), d4=129, d5=3, d6=4, d7=10, d8=15. As d4 a d8 servem às imagens de `Files/Assets`.

### 3.5 `[mrm_hschemaex]` (conteúdo em 0x1B50) [O]
- u16 1, u16 comprimento do nome único (39), u16 comprimento do nome (28), u16 0, `char[16]`
  `[def_hnamesx]  \0`.
- Versão: u16 major 1, u16 minor 0, u32 0, u32 checksum `0x55A27B9B`, u32 661 escopos, u32 1323 itens.
- Nome único `ms-appx://Microsoft.WindowsCalculator/`, nome `Microsoft.WindowsCalculator`.
- u16 0. Depois: u16 maior caminho = 110, u16 0, u32 1984 (= escopos + itens), u32 661, u32 1323,
  u32 0 caracteres no bloco Unicode, u32 comprimento total do bloco de nomes, u32 43624 bytes no bloco ASCII.
- 1984 entradas de 12 bytes: u16 pai, u16 comprimento do caminho completo, u16 1ª letra maiúscula,
  u8 comprimento do nome, u8 flags (bits 0–3 = bits altos do offset, 0x10 = escopo, 0x20 = nome ASCII),
  u16 offset do nome, u16 índice.
- 661×8 bytes de ScopeEx (u16 entrada, u16 nº de filhos, u16 1º filho, u16 0).
- 1323×u16 (item → entrada).
- Blocos de nomes. Todos os nomes deste arquivo estão no bloco ASCII, em 0x981E.

O nome completo junta os nomes dos ancestrais com `/`. O escopo raiz (índice 0) tem nome vazio e três
filhos: `CEngineStrings` (108 itens), `Files` (49) e `Resources` (1166). Os nomes de `x:Uid` aparecem
quebrados em escopos, por exemplo `Resources/num0Button/[using:CalculatorApp.Common]KeyboardShortcutManager/Character`.
O mesmo formato com `/` aparece nos valores `ResourceString.Name` dentro dos XBF.

### 3.6 `[mrm_res_map2_]` (conteúdo em 0x142B8) [O]
Cabeçalho: u16 0 / u16 0 (sem referências de ambiente, como esperado na v2); seção hschema 2; u16 0
(sem bloco de referência de esquema); seção decision 0; 7 tipos de valor; 1 entrada item→grupo;
1 grupo; u32 1323 iteminfos; u32 2546 candidatos; u32 0 bytes de dados embutidos; u32 0 de extensão.

Depois vêm:
- tabela de tipos de valor: 7×(u32 4, u32 tipo) = String, Path, EmbeddedData, AsciiString, Utf8String,
  AsciiPath, Utf8Path;
- item→grupo: (primeiro item 0, grupo 0);
- grupo: (1323 itens, a partir do iteminfo 0);
- 1323 iteminfos (u16 decisão, u16 1º candidato);
- 2546 candidatos de 8 bytes em 0x157C4.

Todos os candidatos são do tipo 1: u8 1, u8 índice do tipo de valor, u16 arquivo-fonte (sempre 0, ou
seja, o próprio PRI), u16 índice do data item, u16 seção do data item. O nº de candidatos de um item é o
nº de conjuntos da sua decisão, e o conjunto *j* da decisão vale para o candidato *1º+j*.

### 3.7 `[mrm_dataitem]` (133 seções) [O]
Formato: u32 0, u16 nº de strings, u16 nº de blobs, u32 bytes de dados, tabela de strings
(u16 offset, u16 comprimento), tabela de blobs (u32 offset, u32 comprimento) e os dados. Os offsets são
relativos ao início dos dados.

Total: 1355 "strings" e 25 blobs, ou 1380 data items.
- Seção 6 (dados em 0x1FA3C) guarda os valores neutros: 25 blobs XBF, 7 XBF registrados como "string" e
  5 caminhos.
- Seções 4 e 5 guardam os textos EN-US e EN-GB, com deduplicação: EN-US e EN-GB, ou chaves diferentes com
  o mesmo texto, apontam para o mesmo data item. Exemplo: `CEngineStrings/99` e `Resources/DivideByZero`
  usam ambos 4/695.
- Seções 7–136 guardam caminhos de imagem, uma por conjunto de qualificadores. As 130 seções têm 130
  conjuntos distintos.

[I] O nome "string" indica só a tabela de entradas com offset de 16 bits. Ela também guarda XBF binários
pequenos, por exemplo `Views/UnitConverter.xbf`, 21695 bytes, item 6/1. O MakePri parece usar essa
tabela sempre que offset e tamanho cabem em u16.

### 3.8 Decodificação dos valores [O]
`String`/`Path` são UTF-16LE, `AsciiString`/`AsciiPath` são ASCII e `Utf8String` é UTF-8, todos com
terminador nulo (2514/2514 strings o têm, e ele é removido no valor). `EmbeddedData` sai como offset,
comprimento e sha256.

Contagem por tipo: AsciiString 2213, Utf8String 91, String 2 (os dois `√` U+221A, `CEngineStrings/30` e
`/90`), AsciiPath 208, EmbeddedData 32. [I] O MakePri parece escolher a codificação mais compacta para
cada valor.

## 4. Contagens e validações (todas OK, 0 alertas) [O]
`recursos.json → validacao.verificacoes_ok` tem 26 verificações aprovadas. As principais:
- `tamanho_total` igual ao tamanho do arquivo; rodapé confere; TOC igual ao cabeçalho de cada uma das
  137 seções; rodapés de seção conferem; seções contíguas; última seção termina no rodapé.
- `pridescex`: as listas de seções coincidem com a TOC.
- `hschemaex`:
  - comprimento do nome, 1ª letra maiúscula e comprimento do caminho completo (calculado juntando com
    `/`) conferem nas 1984 entradas;
  - ScopeEx coerente com os campos `pai`;
  - maior caminho = 110;
  - fim dos blocos coincide com o fim da seção;
  - **o checksum CRC32 recalculado (`0x55A27B9B`) é igual ao gravado.**
- Esquema contra resource map: 1323 itens nos dois. Todos os 2546 candidatos são referenciados por algum
  item, e todos os 1380 data items por algum candidato. Nenhum item ficou sem candidato.
- O bloco de candidatos termina exatamente no fim da seção `res_map2`.

Contagens: 661 escopos e 1323 itens, sendo 108 `CEngineStrings`, 1166 `Resources` e 49 `Files`.
Candidatos: 1274 EN-US e 1032 EN-GB. Outros 240 não têm qualificador de idioma: são os 37 itens neutros
de `Files` (32 XBF e 5 caminhos) e 203 caminhos de imagem qualificados por Contrast, Scale, TargetSize ou
AlternateForm.

Em `Resources`, 1023 chaves têm EN-US e EN-GB, 143 só EN-US e nenhuma só EN-GB. Das 1023, 102 têm
textos diferentes, quase todas ordinais com espaço final no EN-GB (`1st` contra `1st `).
Em `CEngineStrings`, as 108 chaves têm EN-US e 9 também têm EN-GB (99, 100, 101, 105, 107, 108, 118,
119, 120), com texto idêntico.

## 5. Layout XBF v2 implementado (validado nos 32 blobs) [O]
Exemplo `Views/MainPage.xbf` (offsets no .xbf):
- `0x00` `XBF\0`;
- `0x04` u32 tamanho dos metadados = 4056: de `0x0C` até o fim da tabela de namespaces XML;
- `0x08` u32 tamanho dos nós = 2701: da tabela de seções de nós até o EOF;
- `0x0C`/`0x10` versão 2.1 (os 32 XBF são 2.1);
- `0x14`–`0x43`: 6×u64 offsets **relativos a 0x0C** (strings 0x78 → 0x84; assemblies 0xE38;
  namespaces de tipo 0xE3C; tipos 0xE40; propriedades 0xEF8; xmlns 0xFA4);
- `0x44` `char[64]` hash em hex ASCII (`2AEFE46B…8979`);
- tabela de strings em `0x84`: u32 n, depois n×(u32 nº de caracteres, UTF-16LE, u16 0);
- assemblies: n×(i32 tipo, i32 string);
- namespaces de tipo: n×(i32 assembly, i32 string);
- tipos: n×(i32 flags, i32 namespace, i32 string);
- propriedades: n×(i32 flags, i32 tipo dono, i32 string);
- xmlns: n×(i32 string);
- tabela de seções de nós: u32 n, depois n×(i32 offset dos nós, i32 offset posicional), relativos ao fim
  desta tabela (em MainPage, 9 seções e fluxo em `0x1030`).

Validações por arquivo, 538 aprovadas no total, 0 problemas:
- cada tabela começa exatamente no offset que o cabeçalho declara;
- `12 + metadata_size + node_size` é igual ao tamanho do arquivo;
- o fim da tabela xmlns está em `0x0C + metadata_size`;
- todos os índices das tabelas são válidos;
- toda string tem o u16 0 final;
- sha256 do blob igual ao de `recursos.json`;
- a desmontagem da raiz termina exatamente no fim da seção de nós 0, com pilhas consistentes.

### 5.1 Hipóteses usadas no XBF [I]
1. **Tipo com flag 2.** XbfTools não interpreta o campo de namespace. Aqui ele foi tratado como índice na
   tabela de namespaces XML. A hipótese é coerente em todos os casos, por exemplo
   `KeyboardShortcutManager` → `using:CalculatorApp.Common`, igual ao prefixo `[using:CalculatorApp.Common]`
   das chaves do PRI, e `Grapher` → `using:GraphControl`.
2. **ResourceDictionary tipo 10.** O XbfTools rejeita listas não vazias e deixa um layout comentado com
   2 offsets fixos. Aqui foi usado: lista1 = n×(u16 chave, 7bit k, k×7bit offset); lista2 vazia;
   lista3 = n×(7bit offset, 7bit m, m×(u16 tipo, u16 string)). A hipótese explica os 7 casos dos 6
   arquivos (App, Calculator, CalculatorProgrammerOperators, DateCalculator×2, GraphingCalculator,
   UnitConverter). São recursos condicionais `IsApiContractPresent`/`IsApiContractNotPresent`
   (`UniversalApiContract,7`/`,8`/`,14`). Nesses 6 arquivos, 2 a 6 seções de nós não são alcançadas a
   partir da raiz. Supõe-se que sejam as variantes condicionais, e elas foram desmontadas isoladamente
   (`xbf-resumo.json → notas`).
3. **Nomes de tipos e propriedades do framework** (IDs com bit 0x8000). Vêm da tabela do XbfTools para o
   SDK 10.0.26100. Os nomes fazem sentido no contexto (`Grid.RowDefinitions`, `RowDefinition.Height`,
   `ButtonBase.CommandParameter`), mas nada no arquivo comprova a tabela.

## 6. O que não foi possível determinar, ou ficou incerto
1. PRI: o significado de `atom`, `operador` e `tipo de valor` dos qualificadores distintos e o efeito das
   prioridades e do fallback na resolução em tempo de execução. Os valores foram lidos, mas a semântica
   não foi verificada.
2. PRI: o caminho de código para referências de ambiente (`res_map__` v1), bloco de extensão,
   `[def_file_list]` e `[mrm_rev_map]` foi implementado só parcialmente, ou não foi, porque essas
   estruturas não existem neste arquivo e não havia como testar. O parser avisa se aparecerem.
3. PRI: o critério do MakePri para distribuir os data items entre as 133 seções e para escolher a
   codificação de cada valor. Ver [I] em §3.7 e §3.8.
4. XBF: o significado do hash de 64 caracteres (supõe-se que seja um SHA-256 do XAML de origem, [I]),
   das flags de tipo e propriedade e do bloco posicional de linha e coluna, que não foi interpretado.
5. XBF: a desmontagem dos nós é heurística. É uma porta do XbfReader, cujo autor avisa que a derivou só da
   observação de arquivos. O nó `0x04` tem interpretação ambígua (texto literal, classe ou
   modificador/handler). Os `.txt` em `xbf-nos/` servem de pista, não de prova. As tabelas de §5 são
   estruturais e validadas.
6. `{x:Bind}`: [I] o compilador XAML transforma `x:Bind` em código gerado, e no XBF só fica o
   connectionId (nó `connect N`). Por isso os bindings do view model principal (ex.: `MainPage`,
   `HistoryList`) não aparecem no XBF. Evidência [O]: o winmd declara
   `prop Windows.UI.Xaml.Input.ICommand ButtonPressed { get; }` (`trabalho/winmd/CalculatorApp.ViewModel.txt`,
   linhas 1077, 1263, 2268, 2304 e 2514), mas nenhuma das 32 tabelas de strings XBF tem `ButtonPressed`
   como string isolada. Só aparecem as chaves de recurso `ButtonPressedBackground`/`Foreground` em `App.xbf`.
   Para ver esses bindings é preciso ler o código gerado no `CalculatorApp.dll`, na Fase 2/3. Os `{Binding}`
   clássicos aparecem e estão listados.
7. O texto de `CEngineStrings/23` é `cis` (bytes `63 69 73 00` em 0x1F8DC, data item 5/237). Os vizinhos
   são `22`=`sin` e `24`=`tan`, e as variantes `68`=`cos₀` etc. [I] Parece erro de digitação de `cos` no
   recurso. **Revalidado em §8**: não é erro do parser. O uso da chave pelo motor está em
   `relatorio/02-features/a-operacoes-basicas.md` §7.

## 7. Destaques

### (a) `CEngineStrings`: as 108 chaves com o valor EN-US
[O] Valores lidos dos data items indicados.
[I] Os símbolos subscritos marcam a unidade angular: `₀` (U+2080) em graus, `ᵣ` (U+1D63) em radianos e
`₉` (U+2089) em grados. A dedução vem das chaves alfabéticas `*Deg`/`*Rad`/`*Grad`, por exemplo
`CotDeg`=`cot₀`.
O view model expõe `AppResourceProvider.GetCEngineString(String key)` e `GetResourceString(String key)`
[O, `trabalho/winmd/CalculatorApp.ViewModel.txt`]. Supõe-se que leiam `CEngineStrings/*` e `Resources/*` [I].

| chave | valor EN-US | EN-GB | item | tipo | dataitem seção/item @offset no PRI |
|---|---|---|---|---|---|
| `2` | `CE` | — | 18 | AsciiString | 5/241 @0x1F8EC |
| `4` | `.` | — | 33 | AsciiString | 5/60 @0x1F320 |
| `6` | `AND` | — | 39 | AsciiString | 5/228 @0x1F8AC |
| `7` | `OR` | — | 44 | AsciiString | 5/223 @0x1F888 |
| `8` | `XOR` | — | 55 | AsciiString | 5/212 @0x1F81C |
| `9` | `Lsh` | — | 66 | AsciiString | 5/201 @0x1F7B8 |
| `10` | `Rsh` | — | 0 | AsciiString | 5/248 @0x1F90C |
| `11` | `÷` | — | 6 | Utf8String | 5/247 @0x1F908 |
| `12` | `×` | — | 9 | Utf8String | 5/246 @0x1F904 |
| `13` | `+` | — | 11 | AsciiString | 5/37 @0x1F2BC |
| `14` | `-` | — | 12 | AsciiString | 5/62 @0x1F328 |
| `15` | `Mod` | — | 13 | AsciiString | 5/245 @0x1F900 |
| `16` | `yroot` | — | 14 | AsciiString | 5/244 @0x1F8F8 |
| `17` | `^` | — | 15 | AsciiString | 5/3 @0x1F134 |
| `18` | `Int` | — | 16 | AsciiString | 5/243 @0x1F8F4 |
| `19` | `RoL` | — | 17 | AsciiString | 5/242 @0x1F8F0 |
| `20` | `RoR` | — | 19 | AsciiString | 5/240 @0x1F8E8 |
| `21` | `NOT` | — | 20 | AsciiString | 5/239 @0x1F8E4 |
| `22` | `sin` | — | 21 | AsciiString | 5/238 @0x1F8E0 |
| `23` | `cis` | — | 22 | AsciiString | 5/237 @0x1F8DC |
| `24` | `tan` | — | 23 | AsciiString | 5/236 @0x1F8D8 |
| `25` | `sinh` | — | 24 | AsciiString | 5/235 @0x1F8D0 |
| `26` | `cosh` | — | 25 | AsciiString | 5/234 @0x1F8C8 |
| `27` | `tanh` | — | 26 | AsciiString | 5/233 @0x1F8C0 |
| `28` | `ln` | — | 27 | AsciiString | 5/232 @0x1F8BC |
| `29` | `log` | — | 28 | AsciiString | 5/231 @0x1F8B8 |
| `30` | `√` | — | 29 | String | 5/200 @0x1F7B4 |
| `35` | `dms` | — | 30 | AsciiString | 5/230 @0x1F8B4 |
| `37` | `10^` | — | 31 | AsciiString | 5/202 @0x1F7BC |
| `38` | `%` | — | 32 | AsciiString | 5/40 @0x1F2CC |
| `40` | `Pi` | — | 34 | AsciiString | 4/227 @0x1C048 |
| `41` | `=` | — | 35 | AsciiString | 5/79 @0x1F3B4 |
| `47` | `Exp` | — | 36 | AsciiString | 5/229 @0x1F8B0 |
| `48` | `(` | — | 37 | AsciiString | 5/44 @0x1F2E0 |
| `49` | `)` | — | 38 | AsciiString | 5/88 @0x1F3F8 |
| `66` | `frac` | — | 40 | AsciiString | 5/227 @0x1F8A4 |
| `67` | `sin₀` | — | 41 | Utf8String | 5/226 @0x1F89C |
| `68` | `cos₀` | — | 42 | Utf8String | 5/225 @0x1F894 |
| `69` | `tan₀` | — | 43 | Utf8String | 5/224 @0x1F88C |
| `70` | `sin₀⁻¹` | — | 45 | Utf8String | 5/222 @0x1F87C |
| `71` | `cos₀⁻¹` | — | 46 | Utf8String | 5/221 @0x1F870 |
| `72` | `tan₀⁻¹` | — | 47 | Utf8String | 5/220 @0x1F864 |
| `73` | `sinᵣ` | — | 48 | Utf8String | 5/219 @0x1F85C |
| `74` | `cosᵣ` | — | 49 | Utf8String | 5/218 @0x1F854 |
| `75` | `tanᵣ` | — | 50 | Utf8String | 5/217 @0x1F84C |
| `76` | `sinᵣ⁻¹` | — | 51 | Utf8String | 5/216 @0x1F840 |
| `77` | `cosᵣ⁻¹` | — | 52 | Utf8String | 5/215 @0x1F834 |
| `78` | `tanᵣ⁻¹` | — | 53 | Utf8String | 5/214 @0x1F828 |
| `79` | `sin₉` | — | 54 | Utf8String | 5/213 @0x1F820 |
| `80` | `cos₉` | — | 56 | Utf8String | 5/211 @0x1F814 |
| `81` | `tan₉` | — | 57 | Utf8String | 5/210 @0x1F80C |
| `82` | `sin₉⁻¹` | — | 58 | Utf8String | 5/209 @0x1F800 |
| `83` | `cos₉⁻¹` | — | 59 | Utf8String | 5/208 @0x1F7F4 |
| `84` | `tan₉⁻¹` | — | 60 | Utf8String | 5/207 @0x1F7E8 |
| `85` | `sinh⁻¹` | — | 61 | Utf8String | 5/206 @0x1F7DC |
| `86` | `cosh⁻¹` | — | 62 | Utf8String | 5/205 @0x1F7D0 |
| `87` | `tanh⁻¹` | — | 63 | Utf8String | 5/204 @0x1F7C4 |
| `88` | `e^` | — | 64 | AsciiString | 5/203 @0x1F7C0 |
| `89` | `10^` | — | 65 | AsciiString | 5/202 @0x1F7BC |
| `90` | `√` | — | 67 | String | 5/200 @0x1F7B4 |
| `91` | `sqr` | — | 68 | AsciiString | 5/199 @0x1F7B0 |
| `92` | `cube` | — | 69 | AsciiString | 5/198 @0x1F7A8 |
| `94` | `fact` | — | 70 | AsciiString | 5/197 @0x1F7A0 |
| `95` | `1/` | — | 71 | AsciiString | 5/196 @0x1F79C |
| `96` | `degrees` | — | 72 | AsciiString | 5/195 @0x1F794 |
| `97` | `negate` | — | 73 | AsciiString | 5/194 @0x1F78C |
| `99` | `Cannot divide by zero` | `Cannot divide by zero` | 74 | AsciiString | 4/695 @0x1E1C4 |
| `100` | `Invalid input` | `Invalid input` | 1 | AsciiString | 4/890 @0x1ED00 |
| `101` | `Result is undefined` | `Result is undefined` | 2 | AsciiString | 4/889 @0x1ECEC |
| `105` | `Not enough memory` | `Not enough memory` | 3 | AsciiString | 4/888 @0x1ECD8 |
| `107` | `Overflow` | `Overflow` | 4 | AsciiString | 4/886 @0x1ECB8 |
| `108` | `Result not defined` | `Result not defined` | 5 | AsciiString | 4/887 @0x1ECC4 |
| `118` | `Result not defined` | `Result not defined` | 7 | AsciiString | 4/887 @0x1ECC4 |
| `119` | `Overflow` | `Overflow` | 8 | AsciiString | 4/886 @0x1ECB8 |
| `120` | `Overflow` | `Overflow` | 10 | AsciiString | 4/886 @0x1ECB8 |
| `Abs` | `abs` | — | 75 | AsciiString | 5/193 @0x1F788 |
| `Ceil` | `ceil` | — | 76 | AsciiString | 5/192 @0x1F780 |
| `CotDeg` | `cot₀` | — | 77 | Utf8String | 5/191 @0x1F778 |
| `CotGrad` | `cot₉` | — | 78 | Utf8String | 5/190 @0x1F770 |
| `Coth` | `coth` | — | 79 | AsciiString | 5/189 @0x1F768 |
| `CotRad` | `cotᵣ` | — | 80 | Utf8String | 5/188 @0x1F760 |
| `CscDeg` | `csc₀` | — | 81 | Utf8String | 5/187 @0x1F758 |
| `CscGrad` | `csc₉` | — | 82 | Utf8String | 5/186 @0x1F750 |
| `Csch` | `csch` | — | 83 | AsciiString | 5/185 @0x1F748 |
| `CscRad` | `cscᵣ` | — | 84 | Utf8String | 5/184 @0x1F740 |
| `CubeRoot` | `cuberoot` | — | 85 | AsciiString | 5/183 @0x1F734 |
| `Floor` | `floor` | — | 86 | AsciiString | 5/182 @0x1F72C |
| `InverseCotDeg` | `cot₀⁻¹` | — | 87 | Utf8String | 5/181 @0x1F720 |
| `InverseCotGrad` | `cot₉⁻¹` | — | 88 | Utf8String | 5/180 @0x1F714 |
| `InverseCoth` | `coth⁻¹` | — | 89 | Utf8String | 5/179 @0x1F708 |
| `InverseCotRad` | `cotᵣ⁻¹` | — | 90 | Utf8String | 5/178 @0x1F6FC |
| `InverseCscDeg` | `csc₀⁻¹` | — | 91 | Utf8String | 5/177 @0x1F6F0 |
| `InverseCscGrad` | `csc₉⁻¹` | — | 92 | Utf8String | 5/176 @0x1F6E4 |
| `InverseCsch` | `csch⁻¹` | — | 93 | Utf8String | 5/175 @0x1F6D8 |
| `InverseCscRad` | `cscᵣ⁻¹` | — | 94 | Utf8String | 5/174 @0x1F6CC |
| `InverseSecDeg` | `sec₀⁻¹` | — | 95 | Utf8String | 5/173 @0x1F6C0 |
| `InverseSecGrad` | `sec₉⁻¹` | — | 96 | Utf8String | 5/172 @0x1F6B4 |
| `InverseSech` | `sech⁻¹` | — | 97 | Utf8String | 5/171 @0x1F6A8 |
| `InverseSecRad` | `secᵣ⁻¹` | — | 98 | Utf8String | 5/170 @0x1F69C |
| `LogBaseY` | `log base` | — | 99 | AsciiString | 5/169 @0x1F690 |
| `Nand` | `NAND` | — | 100 | AsciiString | 5/168 @0x1F688 |
| `Nor` | `NOR` | — | 101 | AsciiString | 5/167 @0x1F684 |
| `ProgrammerMod` | `%` | — | 102 | AsciiString | 5/40 @0x1F2CC |
| `SecDeg` | `sec₀` | — | 103 | Utf8String | 5/166 @0x1F67C |
| `SecGrad` | `sec₉` | — | 104 | Utf8String | 5/165 @0x1F674 |
| `Sech` | `sech` | — | 105 | AsciiString | 5/164 @0x1F66C |
| `SecRad` | `secᵣ` | — | 106 | Utf8String | 5/163 @0x1F664 |
| `TwoPowX` | `2^` | — | 107 | AsciiString | 5/162 @0x1F660 |

### (b) Strings com cara de mensagem de erro (EN-US)
[O] A seleção usa palavras-chave no valor ou na chave. Ficam de fora as chaves `x:Uid`
(`Botão/Propriedade`) e rótulos como `Domain` e `Zero`. Itens com o mesmo data item compartilham o texto,
ex.: `CEngineStrings/99` e `Resources/DivideByZero` (4/695).

| recurso | valor EN-US | item | evidência (dataitem seção/item @offset) |
|---|---|---|---|
| `CEngineStrings/99` | Cannot divide by zero | 74 | 4/695 @0x1E1C4 |
| `CEngineStrings/100` | Invalid input | 1 | 4/890 @0x1ED00 |
| `CEngineStrings/101` | Result is undefined | 2 | 4/889 @0x1ECEC |
| `CEngineStrings/105` | Not enough memory | 3 | 4/888 @0x1ECD8 |
| `CEngineStrings/107` | Overflow | 4 | 4/886 @0x1ECB8 |
| `CEngineStrings/108` | Result not defined | 5 | 4/887 @0x1ECC4 |
| `CEngineStrings/118` | Result not defined | 7 | 4/887 @0x1ECC4 |
| `CEngineStrings/119` | Overflow | 8 | 4/886 @0x1ECB8 |
| `CEngineStrings/120` | Overflow | 10 | 4/886 @0x1ECB8 |
| `Resources/CalculationFailed` | Calculation failed | 275 | 4/795 @0x1E850 |
| `Resources/CannotPaste` | This expression cannot be pasted | 281 | 4/790 @0x1E7D4 |
| `Resources/CannotUseComplexInfinityInReal` | Cannot use complex infinity | 282 | 4/789 @0x1E7B8 |
| `Resources/CannotUseIInInequalitySolving` | Cannot use complex numbers in inequalities | 283 | 4/788 @0x1E78C |
| `Resources/CannotUseIInReal` | "i" and "I" cannot be used as variable names | 284 | 5/92 @0x1F41C |
| `Resources/CannotUseIndexVarInLimPoint` | x or y cannot be used in the limit point | 285 | 4/786 @0x1E728 |
| `Resources/CannotUseIndexVarInOpLimits` | x or y cannot be used in the upper or lower limits | 286 | 4/785 @0x1E6F4 |
| `Resources/CurrencyRatesUpdateFailed` | Could not update rates | 382 | 4/734 @0x1E428 |
| `Resources/Date_OutOfBoundMessage` | Date out of Bound | 401 | 5/86 @0x1F3E0 |
| `Resources/DivideByZero` | Cannot divide by zero | 436 | 4/695 @0x1E1C4 |
| `Resources/ErrorButtonOk` | OK | 486 | 4/358 @0x1C530 |
| `Resources/FactorialCannotPerformOnLargeNumber` | The factorial function has an argument that is too large to graph | 499 | 4/647 @0x1DE48 |
| `Resources/FactorialInvalidArgument` | The factorial function has an invalid argument | 500 | 4/646 @0x1DE18 |
| `Resources/FailedToRefresh` | Couldn’t get new rates. Try again later. | 501 | 4/645 @0x1DDEC |
| `Resources/Format_MaxDigitsReached` | Max digits reached. %1 | 519 | 4/631 @0x1DCF4 |
| `Resources/GE_NotSupported` | Graphing this equation is not supported | 542 | 4/613 @0x1DB5C |
| `Resources/GeneralError` | The equation could not be graphed | 541 | 4/614 @0x1DB84 |
| `Resources/InvalidEquationSyntax` | Invalid expression | 611 | 4/561 @0x1D728 |
| `Resources/InvalidNumberBase` | The base must be greater than 2 and less than 36 | 612 | 4/560 @0x1D6F4 |
| `Resources/InvalidNumberDigit` | The digit could not be resolved for the given base | 613 | 4/559 @0x1D6C0 |
| `Resources/InvalidToken` | Invalid characters in the expression | 614 | 4/558 @0x1D698 |
| `Resources/InvalidVariableNameFormat` | A variable name is invalid | 615 | 4/557 @0x1D67C |
| `Resources/InvalidVariableSpecification` | A mathematical operation requires one of its parameters to be a variable | 616 | 4/556 @0x1D630 |
| `Resources/KGFAnalysisCouldNotBePerformed` | Analysis could not be performed for the function. | 668 | 4/517 @0x1D288 |
| `Resources/KGFAnalysisNotSupported` | Analysis is not supported for this function. | 669 | 4/516 @0x1D258 |
| `Resources/KGFDomainNone` | Unable to calculate the domain for this function. | 670 | 4/515 @0x1D224 |
| `Resources/KGFMonotonicityError` | Unable to determine the monotonicity of the function. | 678 | 4/507 @0x1D0E8 |
| `Resources/KGFParityError` | Unable to determine the parity of the function. | 682 | 4/503 @0x1D048 |
| `Resources/KGFPeriodicityError` | Periodicity is not supported for this function. | 687 | 4/498 @0x1CFA0 |
| `Resources/KGFRangeNone` | Unable to calculate the range for this function. | 690 | 4/495 @0x1CF24 |
| `Resources/KGFTooComplexFeaturesError` | These features are too complex for Calculator to calculate: | 691 | 4/494 @0x1CEE8 |
| `Resources/ModuloCannotPerformOnFloat` | Modulo can only be used with whole numbers | 774 | 4/444 @0x1CB14 |
| `Resources/OutOfDomain` | Equation is out of domain | 828 | 4/413 @0x1C950 |
| `Resources/Overflow` | Overflow (the number is too large) | 830 | 4/411 @0x1C920 |
| `Resources/ShareActionErrorMessage` | Unable to share at this time. | 912 | 4/359 @0x1C534 |
| `Resources/ShareActionErrorOk` | OK | 913 | 4/358 @0x1C530 |
| `Resources/SnapshotRestoreError` | Couldn't restore this snapshot. | 930 | 4/346 @0x1C448 |

Mensagens de motor usadas pela calculadora padrão e científica [I, pelos nomes]:
- `CEngineStrings`: 99 `Cannot divide by zero`, 100 `Invalid input`, 101 `Result is undefined`,
  105 `Not enough memory`, 107/119/120 `Overflow`, 108/118 `Result not defined`;
- `Resources`: `DivideByZero`, `Overflow` (`Overflow (the number is too large)`), `CalculationFailed` e
  `Format_MaxDigitsReached` (`Max digits reached. %1`).

As demais são do gráfico (`KGF*`, `Invalid*`, `CannotUse*`), de datas, de câmbio ou de compartilhamento.

### (c) Por XBF: nomes ligados ao view model, propriedades e comandos
[O] Valores da desmontagem, tabelas e strings de cada XBF. A coluna "membros do VM" compara as strings
do XBF com os nomes de propriedades, métodos, eventos e valores de enum de
`CalculatorApp.ViewModel.winmd`, via `trabalho/winmd/CalculatorApp.ViewModel.json`. Coincidência de
string não prova uso [I], exceto quando a string é o `Path` de um `{Binding}` (lista abaixo da tabela).
Foram omitidos da coluna os nomes genéricos `Name`, `Value`, `Glyph`, `Title`, `IsEnabled`, `IsActive`,
`Clear`, `Mode`, `Items` e `AuditoryFeedback`.

| XBF | x:Class | strings | seções de nós | botões (ButtonId/CommandParameter) | `{Binding}` Path (exceto TemplateSettings.*) | ElementName | strings = membros do VM (winmd), sem genéricos |
|---|---|---|---|---|---|---|---|
| `App.xbf` | CalculatorApp.App | 424 | 94 | 0 | `DisabledBackground`, `DisabledForeground`, `HoverBackground`, `HoverForeground`, `PressBackground`, `PressForeground` | — | `DisplayValue` |
| `CommunityToolkit.WinUI.Controls.SettingsControls/SettingsCard/SettingsCard.xbf` | — | 222 | 23 | 0 | `Content`, `ContentAlignment`, `HorizontalContentAlignment` | PART_RootGrid | — |
| `CommunityToolkit.WinUI.Controls.SettingsControls/SettingsExpander/SettingsExpander.xbf` | — | 156 | 13 | 0 | `CornerRadius`, `IsExpanded`, `ItemTemplate` | — | — |
| `CommunityToolkit.WinUI.Controls.SettingsControls/Themes/Generic.xbf` | — | 2 | 1 | 0 | — | — | — |
| `GraphControl/Themes/generic.xbf` | — | 5 | 3 | 0 | — | — | — |
| `Microsoft.UI.Xaml/DensityStyles/Compact.xbf` | — | 1 | 1 | 0 | — | — | — |
| `Views/Calculator.xbf` | CalculatorApp.Calculator | 378 | 45 | 4 | `DisplayValue`, `ExpressionTokens`, `IsProgrammer` | — | `ExpressionTokens`, `DisplayValue`, `IsProgrammer` |
| `Views/CalculatorProgrammerBitFlipPanel.xbf` | CalculatorApp.CalculatorProgrammerBitFlipPanel | 240 | 7 | 64 | `Text` | BinaryOne, BinaryZero | — |
| `Views/CalculatorProgrammerDisplayPanel.xbf` | CalculatorApp.CalculatorProgrammerDisplayPanel | 54 | 2 | 4 | — | — | — |
| `Views/CalculatorProgrammerOperators.xbf` | CalculatorApp.CalculatorProgrammerOperators | 83 | 8 | 0 | `ActualHeight` | BinaryButton | — |
| `Views/CalculatorProgrammerRadixOperators.xbf` | CalculatorApp.CalculatorProgrammerRadixOperators | 271 | 9 | 32 | — | — | — |
| `Views/CalculatorScientificAngleButtons.xbf` | CalculatorApp.CalculatorScientificAngleButtons | 56 | 5 | 4 | — | — | — |
| `Views/CalculatorScientificOperators.xbf` | CalculatorApp.CalculatorScientificOperators | 460 | 3 | 60 | — | — | — |
| `Views/CalculatorStandardOperators.xbf` | CalculatorApp.CalculatorStandardOperators | 165 | 2 | 13 | — | — | — |
| `Views/DateCalculator.xbf` | CalculatorApp.DateCalculator | 255 | 34 | 0 | `DaysOffset`, `IsAddMode`, `IsDateDiffMode`, `IsDiffInDays`, `MonthsOffset`, `OffsetValues`, `StrDateDiffResult`, `StrDateDiffResultAutomationName`, `StrDateDiffResultInDays`, `StrDateResult`, `StrDateResultAutomationName`, `YearsOffset` | DaysLabel, MonthsLabel, YearsLabel | `IsDateDiffMode`, `StrDateDiffResultAutomationName`, `StrDateDiffResult`, `StrDateDiffResultInDays`, `IsDiffInDays`, `IsAddMode`, `OffsetValues`, `YearsOffset`, `MonthsOffset`, `DaysOffset`, `StrDateResultAutomationName`, `StrDateResult` |
| `Views/DelighterUnitStyles.xbf` | — | 54 | 29 | 0 | — | — | — |
| `Views/GraphingCalculator/EquationInputArea.xbf` | CalculatorApp.EquationInputArea | 229 | 34 | 0 | `EquationButtonForegroundColor.Color`, `EquationColor.Color`, `IsEquationLineDisabled`, `MathEquation` | — | — |
| `Views/GraphingCalculator/EquationStylePanelControl.xbf` | CalculatorApp.EquationStylePanelControl | 35 | 7 | 0 | `Foreground` | — | — |
| `Views/GraphingCalculator/GraphingCalculator.xbf` | CalculatorApp.GraphingCalculator | 208 | 48 | 0 | — | — | — |
| `Views/GraphingCalculator/GraphingNumPad.xbf` | CalculatorApp.GraphingNumPad | 463 | 3 | 71 | — | — | — |
| `Views/GraphingCalculator/GraphingSettings.xbf` | CalculatorApp.GraphingSettings | 83 | 13 | 0 | — | GraphThemeHeading, LineThicknessBoxHeading, UnitsHeading | — |
| `Views/GraphingCalculator/KeyGraphFeaturesPanel.xbf` | CalculatorApp.KeyGraphFeaturesPanel | 63 | 22 | 0 | — | — | — |
| `Views/HistoryList.xbf` | CalculatorApp.HistoryList | 77 | 8 | 0 | — | — | — |
| `Views/MainPage.xbf` | CalculatorApp.MainPage | 76 | 9 | 0 | — | — | — |
| `Views/Memory.xbf` | CalculatorApp.Memory | 62 | 5 | 0 | `IsMemoryEmpty`, `RowHeight` | MemoryList | `IsMemoryEmpty` |
| `Views/MemoryListItem.xbf` | CalculatorApp.MemoryListItem | 44 | 3 | 0 | — | — | — |
| `Views/NumberPad.xbf` | CalculatorApp.NumberPad | 61 | 2 | 11 | `ButtonStyle`, `IsDecimalEnabled` | ControlRoot | `IsDecimalEnabled` |
| `Views/OperatorsPanel.xbf` | CalculatorApp.OperatorsPanel | 13 | 5 | 0 | — | — | — |
| `Views/Settings.xbf` | CalculatorApp.Settings | 75 | 5 | 0 | — | — | — |
| `Views/SupplementaryResults.xbf` | CalculatorApp.SupplementaryResults | 36 | 7 | 0 | `Unit` | — | `Unit` |
| `Views/TitleBar.xbf` | CalculatorApp.TitleBar | 32 | 3 | 0 | — | — | — |
| `Views/UnitConverter.xbf` | CalculatorApp.UnitConverter | 260 | 20 | 3 | `AccessibleName`, `IsDropDownEnabled`, `Name`, `Unit1`, `Unit2`, `Units`, `Value1Active`, `Value2Active` | — | `AccessibleName`, `Value1`, `Value1Active`, `Units`, `Unit1`, `IsDropDownEnabled`, `Value2`, `Value2Active`, `Unit2`, `SupplementaryResults` |

`{Binding Path}` que coincide com uma propriedade do VM no winmd [O no XBF, I quanto ao tipo do DataContext]:
- `Views/Calculator.xbf`: `ExpressionTokens` → StandardCalculatorViewModel.ExpressionTokens (prop); `DisplayValue` → PrimaryDisplaySnapshot.DisplayValue (prop), StandardCalculatorViewModel.DisplayValue (prop); `IsProgrammer` → StandardCalculatorViewModel.IsProgrammer (prop)
- `Views/DateCalculator.xbf`: `IsDateDiffMode` → DateCalculatorViewModel.IsDateDiffMode (prop); `StrDateDiffResultAutomationName` → DateCalculatorViewModel.StrDateDiffResultAutomationName (prop); `StrDateDiffResult` → DateCalculatorViewModel.StrDateDiffResult (prop); `StrDateDiffResultInDays` → DateCalculatorViewModel.StrDateDiffResultInDays (prop); `IsDiffInDays` → DateCalculatorViewModel.IsDiffInDays (prop); `IsAddMode` → DateCalculatorViewModel.IsAddMode (prop); `OffsetValues` → DateCalculatorViewModel.OffsetValues (prop); `YearsOffset` → DateCalculatorViewModel.YearsOffset (prop); `MonthsOffset` → DateCalculatorViewModel.MonthsOffset (prop); `DaysOffset` → DateCalculatorViewModel.DaysOffset (prop); `StrDateResultAutomationName` → DateCalculatorViewModel.StrDateResultAutomationName (prop); `StrDateResult` → DateCalculatorViewModel.StrDateResult (prop)
- `Views/Memory.xbf`: `IsMemoryEmpty` → StandardCalculatorViewModel.IsMemoryEmpty (prop)
- `Views/NumberPad.xbf`: `IsDecimalEnabled` → GraphingCalculatorViewModel.IsDecimalEnabled (prop), StandardCalculatorViewModel.IsDecimalEnabled (prop), UnitConverterViewModel.IsDecimalEnabled (prop)
- `Views/SupplementaryResults.xbf`: `Unit` → SupplementaryResult.Unit (prop)
- `Views/UnitConverter.xbf`: `AccessibleName` → Unit.AccessibleName (prop); `Name` → Category.Name (prop), NavCategory.Name (prop), NavCategoryGroup.Name (prop), Unit.Name (prop), VariableViewModel.Name (prop); `Value1Active` → UnitConverterViewModel.Value1Active (prop); `Units` → UnitConverterViewModel.Units (prop); `Unit1` → UnitConverterViewModel.Unit1 (prop); `IsDropDownEnabled` → UnitConverterViewModel.IsDropDownEnabled (prop); `Value2Active` → UnitConverterViewModel.Value2Active (prop); `Unit2` → UnitConverterViewModel.Unit2 (prop)

**Botões e comandos** (`xbf-botoes.tsv`, 266 linhas) [O]:
- A ligação botão → operação está na propriedade `CalculatorButton.ButtonId`, uma propriedade da classe C#
  `CalculatorApp.Controls.CalculatorButton` (xmlns `using:CalculatorApp.Controls`). Seu valor é o nome de
  um membro de `CalculatorApp.ViewModel.Common.NumbersAndOperatorsEnum`. Exemplos de
  `Views/CalculatorStandardOperators.xbf`: `DivideButton` → `Divide` (=91 no winmd),
  `ClearButton` → `Clear` (=81), `PercentButton` → `Percent` (=118), `EqualButton` → `Equals` (=121),
  `NegateButton` → `Negate` (=80). Em `Views/NumberPad.xbf`: `Num0Button` → `Zero` (=130) … `Num9Button`.
- `FlipButtons.ButtonId` = `BINPOS0..63` (=700..763) em `CalculatorProgrammerBitFlipPanel.xbf`.
- `ButtonBase.CommandParameter`:
  - literal `local:NumbersAndOperatorsEnum` `FToE` (=119) em `FtoeButton`;
  - inteiros `0/1/2` em `DegreeButton`/`RadianButton`/`GradsButton` (`CalculatorScientificAngleButtons.xbf`);
  - `0/1/2/3` em `Qword`/`Dword`/`Word`/`ByteButton` (`CalculatorProgrammerDisplayPanel.xbf`);
  - `{StaticResource Zero}` em `MemRecall`/`MemPlus`/`MemMinus` (`Calculator.xbf`).
  O `Command` desses botões não aparece no XBF. [I] Ele vem de `x:Bind`, ver §6 item 6.
- Por XBF: Scientific 60, GraphingNumPad 71, ProgrammerRadix 32, Standard 13, NumberPad 11, BitFlip 64,
  Calculator 4, AngleButtons 4, ProgrammerDisplay 4 e UnitConverter 3.

## 8. Revalidação do parser (2026-10-22, antes da Fase 3a)

Pedido: verificar se `cis` em `CEngineStrings/23` e as 42 chaves de `CEngineStrings` pedidas pelo motor e
ausentes do PRI resultam de desalinhamento de tabela ou do mapeamento chave→índice.

### 8.1 Método
`trabalho/scripts/pri_valida.py` reimplementa, **sem importar `pri_dump.py`**, o caminho nome → item →
candidato → data item. Ele usa caminhos de código diferentes onde o formato tem redundância:
- item → entrada pela tabela de 1323 u16 do esquema (o `pri_dump.py` usa o campo `index` de cada entrada);
- nome completo descendo da raiz pelas listas de filhos do ScopeEx (o `pri_dump.py` sobe pelo campo `parent`);
- CRC32 do esquema recalculado sobre os nomes obtidos por esse caminho;
- grupos de iteminfo esparsos e esquema externo, necessários para o PRI pt-BR.

Saída em `trabalho/ptbr/validacao-pri.json`.

### 8.2 Resultados [O]
| Verificação | Resultado |
|---|---|
| tabela item→entrada vs. campo `index` das 1323 entradas | 0 divergências |
| CRC32 recalculado pelo caminho ScopeEx | `0x55A27B9B` = gravado |
| valores do validador vs. `CEngineStrings.tsv` + `Resources.tsv` | 1274/1274 chaves idênticas (EN-US/EN-GB); pt-BR 1032/1032 |
| fronteira de string: cada data item de texto começa após um NUL e termina em NUL | 1354/1355 OK. A exceção é 6/9 @0x275E4, `AsciiPath` logo após o fim de um XBF binário, cujo último byte não é NUL. É falso positivo da heurística |
| 51 valores previsíveis: `num0..9Button` Character = `0..9` e Name = `Zero..Nine`; `sin/cos/tanButton` = Sine/Cosine/Tangent; `CEngineStrings` 11 `÷`, 12 `×`, 13 `+`, 14 `-`, 22 `sin`, 24 `tan`, 25 `sinh`, 26 `cosh`, 27 `tanh`, 28 `ln`, 29 `log`, 41 `=`, 48 `(`, 49 `)`, 68 `cos₀`, 74 `cosᵣ`, 80 `cos₉`, 99 `Cannot divide by zero`; pt-BR `num0..9Button` = Zero, Um … Nove | **51/51** |
| alinhamento EN-US/PT-BR (mesmas chaves) | ver `trabalho/ptbr/LEIAME.md` §4: 0 divergências de símbolos e de placeholders |

### 8.3 Conclusões
- **`cis` é o conteúdo do recurso, não um desalinhamento [O].** Os bytes `63 69 73 00` em 0x1F8DC formam o data
  item 5/237, referenciado só pelo candidato de `CEngineStrings/23`. No bloco de dados eles aparecem entre
  `tan\0` (0x1F8D8, chave 24) e `sin\0` (0x1F8E0, chave 22). Não existe a sequência ASCII/UTF-8 `cos\0` isolada
  em nenhum ponto do PRI. Os únicos `cos` (UTF-16) ficam dentro de XBFs (`cosButton`/`Cos`, em 0x357B8 e
  0x59838). Uma tabela deslocada trocaria também os vizinhos, mas `sin`, `tan`, `sinh` e `cosh` estão corretos.
- **As 42 chaves ausentes não existem no esquema [O].** A descida pelo ScopeEx dá 108 filhos para
  `CEngineStrings`, os mesmos 108 do `pri_dump.py`. O pacote pt-BR usa o mesmo esquema (checksum idêntico) e
  também não as tem. Do lado do binário, a tabela 0x18018AF40 é um array de 152 `wstring_view` (ptr, len). O
  carregador `FUN_180111b10` percorre 0x18018AF40…0x18018B8C0 (152 × 16 bytes) e grava no mapa só as chaves cujo
  texto não é vazio. Além disso, o motor consulta as strings **pelo nome da chave**
  (`to_wstring(n)` → `unordered_map<wstring,wstring>`), e nunca pela posição na tabela. As "irregularidades" de
  índice da Fase 2 (posição 1 = `62` etc.) não têm efeito. Detalhes em
  `relatorio/02-features/a-operacoes-basicas.md` §7.
- **Defeito real encontrado e corrigido:** o `pri_dump.py` abortava (`struct.error`) em PRI de pacote de
  recursos, cuja seção `[mrm_hschemaex]` vem vazia. Agora `parse_hschema` devolve `None` para seção vazia, a
  opção `--esquema <PRI principal>` carrega o esquema externo depois de conferir a referência (versão, checksum,
  escopos, itens e nome único), e itens sem entrada no resource map do pacote de recursos deixam de ser erro. O
  PRI principal foi reprocessado e a saída ficou idêntica (comparação de 1274 chaves acima).
