# Teste diferencial fora da amostra — primeira passada (2026-10-23)

Casos: `relatorio/03-diferencial-casos.json` (semente **20261023**, `trabalho/diferencial/gerar_casos.py`), SHA-256
`980bdf30b5ec2702ca2508bb996b7d9414c71b068813d32f5fb417d2ec024d6f` gravado em `hashes-originais.txt` às 10:27:30,
antes de qualquer execução (`trabalho/diferencial/congelamento.txt`). Real: `rodar-casos.ps1 -Etapa Diferencial`,
10:27:46–10:55:27, só `NormalOutput` e `plusButton.IsEnabled` pelo UIA (sem capturas nem transcrição) →
`relatorio/resultados-reais-diferencial.jsonl`. Reimplementação: árvore `reimpl/calculadora` com hash
`100ee57a…` (conferido pelo executor), 10:55:34 → `trabalho/diferencial/reimpl-saida.json`. Comparação:
`trabalho/diferencial/comparar.py` → `comparacao.json`/`comparacao.txt`. Nada foi corrigido.

## Taxa por modo (critério pré-registrado: visor idêntico E estado de erro igual)

| Modo | Acertos | Taxa | Casos invalidados pela automação | Taxa nos válidos |
|---|---:|---:|---:|---:|
| Padrão | 100/100 | 100% | 0 | 100% |
| Científico | 58/100 | 58% | 39 (27 sem leitura + 12 contaminados) | 58/61 = 95% |
| Programador | 87/100 | 87% | 0 | 87% |
| Total | 245/300 | 81,7% | 39 | 245/261 = 93,9% |

## Divergências classificadas (55)

| Classe | Casos | Nº |
|---|---|---:|
| Lacuna de documentação | Pr-020, 024, 028, 045, 047, 069, 070, 100 (A); Ci-031, Pr-072, 089, 096 (B1); Ci-037, Ci-061 (C) | 14 |
| Bug da reimplementação | Pr-013, Pr-055 (B2) | 2 |
| Desvio do motor numérico (3f) | — | 0 |
| Problema da automação | Ci-062…100: 27 sem leitura + 12 contaminados (066, 067, 070, 075, 076, 077, 083, 084, 086, 087, 092, 098) | 39 |

**A — visor em BIN preenchido com zeros à esquerda [O].** Real `0010`, reimpl `10`; em erro, real
`0Resultado indefinido`. O 02d §3.1 diz que o preenchimento vale para "a linha BIN do painel (não o visor)", e a reimpl
seguiu o documento. No binário, `SetPrimaryDisplay` 0x1800d35b0 → `FUN_1800d2ee0` → `FUN_1800d98a0` quando vslot 0x4e8
≠ 0 e vslot 0x428 == 8 (`NumberBase.BinBase` = 8 no winmd) [O]; os nomes IsProgrammer/CurrentRadixType dos slots [I].
Não há teste de erro: 19 caracteres ≠ espaço → 1 zero. Nenhum caso da 3d tinha visor BIN fora de múltiplo de 4.
Evidence `ev_5d2db40d…`, `ev_aebc66a9…`; `trabalho/pseudocodigo/0x1800d2ee0.c`.

**B1 — `(` logo após operador binário zera o número corrente [O].** `x × ( =` → 0; `x ÷ ( =` → divisão por zero.
`trabalho/pseudocodigo/0x180112db0.c` linhas 2092–2103: se `motor+0xf48` ∈ 0x56–0x61 ∪ 500–505, grava 0 em
`motor+0x120`. O 02c §3.12 só diz "zera acumulador e pendente". A reimpl mantém o valor (`motor.py` `_abre`).

**B2 — `±` antes de `(` não gera o × implícito [O].** Linha 2024: o × só ocorre se o último comando ∈ dígitos
0x82–0x91, unárias 0x62–0x76 e 400–417, 0x54 ou 0x81; `±` = 0x50 não está. O 02c §1 define as unárias sem 0x50, mas a
reimpl incluiu `UNARIOS_H3` (que tem 80, conjunto do histórico, 02b §4.1) em `motor.py:460`. Classificado como bug da
reimplementação; o §3.12 ("unária") não enumera os códigos, o que contribuiu.

**C — botões desabilitados em erro no Científico [O, caixa-preta].** A automação registrou `trigButton`, `expButton`,
`piButton`, `(`, `)`, `×`, `−`, `+`, `,`, MS, MC desabilitados em erro. L19 só documenta o Padrão e a reimpl só modela o
Padrão; em Ci-037 e Ci-061 ela pressiona botões que na tela não respondem. Também afeta o valor de Ci-084 e Ci-086
(contados em automação por estarem contaminados).

**Automação.** Em Ci-061, o F-E foi acionado em erro (o botão estava habilitado). A VM troca botão não numérico por C em
erro (02a §4.4), então 119 não chegou ao motor e o ToggleButton ficou marcado [O pelo visor final `-9` sem F-E].
O `Preparar3c` do caso seguinte desligou o botão e mandou 119, ligando o F-E no motor [I: o log do preparo se perdeu no
`throw`]. Daí em diante o C não desliga o F-E do motor (L25) e a verificação do preparo só via o visor: 27 casos
falharam no preparo (`0,e+0`) e 12 rodaram com F-E ligado. Em Ci-083 o submenu Funções não abriu em erro.

L31: nenhuma divergência cai nas decisões listadas. Motor numérico: os valores de 32 dígitos coincidiram em todos os
casos não contaminados e, a menos do formato F-E, também em Ci-087 e Ci-092.

## Segunda passada — Ci-062 a Ci-100 (preparo verificado), 2026-10-23

**O que mudou só na automação** (`rodar-casos.ps1` sha256 após a correção registrado em
`trabalho/diferencial/segunda-passada.txt`). Antes de cada caso, `Verificar-Preparo` confere pelo UIA:
- o modo (`Header`);
- o visor exatamente `0`, porque com o motor em F-E o visor zerado é `0,e+0`;
- o toggle `ftoeButton` desligado;
- o ângulo do caso;
- o 2nd desligado.

Se a verificação falha, a automação reinicia a Calculadora e verifica de novo. Se falhar outra vez, o caso é abortado
como "preparo inválido". A reimplementação continuou congelada: o hash conferido foi `100ee57a…` e a saída é idêntica
à da primeira passada (`trabalho/diferencial/reimpl-saida-p2.json`).

**Tentativa 1** (11:21:32–11:21:33): os 39 casos deram "CoreWindow nao encontrada" antes de qualquer tecla. A janela
estava sem conteúdo XAML na árvore UIA (provavelmente minimizada), e um defeito do script fez a exceção da verificação
escapar do `try`, sem reinício. O arquivo foi movido para `trabalho/diferencial/tentativa1-p2-corewindow*`. Correção:
`Focar` na janela e exceção da verificação tratada como falha.

**Tentativa 2** (11:22:08–11:27:08) → `relatorio/resultados-reais-diferencial-p2.jsonl`. Houve 2 reinícios, ambos
pela verificação (visor `0,e+0`):
- em Ci-062: o motor ainda estava contaminado desde a primeira passada;
- em Ci-089: o Ci-088 acionou F-E em erro.

O segundo caso reproduz o mecanismo descrito acima: depois de um F-E em erro, o preparo seguinte encontra o motor em F-E
[O, log da tentativa 2]. Nenhum preparo inválido.

| Científico | Acertos | Taxa |
|---|---:|---:|
| Segunda passada (Ci-062…100, todos válidos) | 34/39 | 87% |
| Válidos das duas passadas (Ci-001…061 da 1ª + Ci-062…100 da 2ª) | 92/100 | 92% |

Divergências da segunda passada (5):

| Caso | Real | Reimpl | Classe |
|---|---|---|---|
| Ci-062 `8 ± ( … ) =` | `-0,2857…` | `2,2857…` | bug da reimplementação (B2: ± antes de `(`) |
| Ci-080 | `0` | `0,e+0` | lacuna de documentação (C: botões desabilitados em erro; F-E em erro não chega ao motor) |
| Ci-084 | `1` | `-1` | lacuna de documentação (C) |
| Ci-086 | `0` | `3,1415…` | lacuna de documentação (C) |
| Ci-088 | `0` | `0,e+0` | lacuna de documentação (C) |

Em Ci-080 a automação registrou "submenu de funcButton nao abriu" ao tentar Floor em erro. Fica como observação [I:
em erro o submenu não abre ou não mostra o botão]. A divergência do caso já se explica pelo grupo C.

## Etapa 2 — documentos e reimplementação corrigidos (2026-10-23)

**Documentos.**
- 02c §3.12: códigos exatos do × implícito (sem `±`), zeragem do número corrente após operador binário e operador
  salvo só com pendente (B3).
- 02d §3.1: o visor em BIN também é preenchido. A frase "não o visor" está registrada como generalização sem
  verificação.
- 04-lacunas L19: conjunto completo de botões do `ErrorLayout` por painel e a contradição do F-E.

**B3 (nova, [O]).** Ao rodar a reimplementação com as quatro correções, dif-Pr-013 ainda falhava. A segunda causa: o
`(` salva o operador só se `+0x20` = 1 (l. 2067–2073) e o `)` restaura `+0x20 = (op ≠ 0)` (l. 2306–2312). A
reimplementação guardava o operador do `=` repetido (AND), e o `=` final repetia a conta. Na primeira passada a
classificação de dif-Pr-013 (só B2) estava **incompleta**.

**Reimplementação** (árvore `2a2df4fe…`, não congelada; o congelado era `100ee57a…`):
- testes congelados 3a–3d: 215/215;
- mutações: todas detectadas;
- diferencial 1: 300/300. A referência real é a 1ª passada para Pd, Pr e Ci-001…061 e a 2ª para Ci-062…100
  (`trabalho/diferencial/comparacao-corrigida-p{1,2}.json`).

Isso mede só a reprodução **dentro da amostra**, já que as correções saíram desses casos.

## Etapa 3 — diferencial 2, primeira passada (2026-10-23)

**Casos.** `relatorio/03-diferencial2-casos.json`, **semente 20261024**, mesmo gerador e mesmas regras: a semente
20261023 regenera o diferencial 1 idêntico. São 300 casos (100 por modo) e nenhuma sequência repete o diferencial 1.
SHA-256 `8df85a473e5c12bd8a4d0ed500aa30a6431e2ae3b39363cf38d0b2ae415e4826` em `hashes-originais.txt` às **11:54:59**,
antes de qualquer execução. A reimplementação congelada é a árvore `2a2df4fe…`, conferida pelo executor
(`trabalho/diferencial/congelamento2.txt`).

**Execução.**
- Real: `DIFVERIFICAR=1`, preparo verificado, das 11:55:04 às 12:27:47, em
  `relatorio/resultados-reais-diferencial2.jsonl`. Nenhum preparo inválido e nenhum reinício.
- Reimplementação: 12:27:53, em `trabalho/diferencial/reimpl-saida-dif2.json`.
- Comparação: `trabalho/diferencial/comparacao-dif2.{json,txt}`. Nada foi corrigido.

| Modo | Acertos | Taxa | Casos com falha da automação | Taxa sem esses casos |
|---|---:|---:|---:|---:|
| Padrão | 98/100 | 98% | 0 | 98% |
| Científico | 96/100 | 96% | 3 (Ci-010, 097, 098) | 96/97 = 99% |
| Programador | 99/100 | 99% | 0 | 99% |
| Total | 293/300 | 97,7% | 3 | 293/297 = 98,7% |

**Divergências classificadas (7).**

| Caso | Real | Reimpl | Classe | Evidência |
|---|---|---|---|---|
| Pd-005 `2 = 1/x % … − ± 175 × =` | `30.621,5001` | `30.625` | lacuna de documentação (D1) | o % deu 0,01 = 0,5 × 2/100 |
| Pd-087 `⌫ 7 = 3 MS 3 % =` | `0,21` | `0` | lacuna de documentação (D1) | 3 × 7/100 |
| Ci-010 `) − sin eˣ + MC 8 ( ( = =` | `127` | `504` | lacuna de documentação (D2) | a automação não abriu o submenu do sin, mas o valor não depende disso: sin(0)=0 e eˣ usa o acumulador 0 nos dois caminhos; a reimpl dá 504 com e sem sin |
| Pr-078 `= 5 NOR 7 NOT − NOR 6512 ROL = =` | `4` | `3` | lacuna de documentação (D2) | |
| Ci-028 `8 × + − 68 cos F-E 3 ( C =` | `0` | `0,e+0` | lacuna de documentação (D3, L25) | |
| Ci-097 | `1,4645…` | `−88,535…` | problema da automação | "toggle trigShiftButton ausente": cos⁻¹ não foi pressionado; sem ele a reimpl dá `1,4645918875615232630201425272638`, igual ao real |
| Ci-098 | `8.103,0839…` | `1` | problema da automação | "toggle hypShiftButton ausente": tanh não foi pressionado; sem ele a reimpl dá `8.103,0839275753840077099966894328`, igual ao real |

Nenhuma divergência é bug da reimplementação nem desvio do motor numérico.

- **D1 — percentual depois de `x =` sem operador [O caixa-preta; origem não localizada].** Com `x =` e depois `%`
  sem operador pendente, a base do percentual é x: o acumulador `+0x160` vale x.
  - A leitura estática prevê 0, como a reimplementação: o C grava acumulador = 0 e `+0xe22` = 1 (l. 1325, 1366); o `=`
    só copia o atual para o acumulador se `+0xe22` = 0 (l. 1556–1557); sem operador (`+0x18` = 0) só chama
    `DisplayNum` (l. 1625); o % sem × ou ÷ usa `+0x160` (`SciCalcFunctions` l. 1052–1059).
  - Para dar o resultado real, `+0xe22` teria de estar em 0 nesse `=`, ou outra camada grava o acumulador.
    `SendCommand` (0x18010d3d0) não trata C/= de modo especial. [I] Fica para investigação.
- **D2 — `=` repetido depois de desempilhar a precedência [O].** No laço que avalia o que restou na pilha
  (l. 1764–1786), cada operação desempilhada grava `+0xe0` = número corrente (l. 1768), deixa `+0x18` = operador
  desempilhado e zera `+0xe22`. Por isso o `=` seguinte repete a **última operação desempilhada** com o operando
  dela:
  - Ci-010: −1 + 64 = 63; o segundo `=` faz 63 + 64 = 127.
  - Pr-078: 5 NOR 3; o segundo `=` faz …F8 NOR 3 = 4.

  O 02a §3.4 (passo 5) e o 02c §3.11 não dizem isso. A reimplementação repete o pendente com o último operando
  digitado.
- **D3 — C com F-E ligado desliga o F-E também no motor [O caixa-preta].** Em Ci-028 o F-E foi ligado sem erro, e
  depois do C o visor voltou a `0`. [I] O C põe `IsFToEChecked` = false (0x1800d0c40). O ToggleButton, que estava
  marcado, desmarca e dispara `FtoEButtonToggled` → 119 (C#, L3).
  - Na contaminação da primeira passada do diferencial 1, o botão já estava desmarcado e o C não teve efeito, o que é
    coerente com essa inferência.
  - A reimplementação segue o que estava documentado: o C muda só a propriedade (L25).
