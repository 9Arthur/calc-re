# 02a — Operações básicas e divisão por zero (Fase 3a)

Alvo: `CalcViewModel.dll` (SHA-256 `072cd589…d21d`), 11.2607.0.0 x64. Análise só estática (REA 6.7.0 /
Ghidra 12.1.4). Nada foi executado. Data: 2026-10-22.

Convenção: **[O]** OBSERVADO, lido de pseudocódigo/assembly/bytes, com endereço; **[I]** INFERIDO, com o
raciocínio indicado. Os nomes de função como `ProcessCommand` são **rótulos** desta análise (não há PDB, L1).
`motor+0xNNN` é um offset no objeto da engine de 0x11a8 bytes.

**Atualizado em 2026-10-22 com a Fase 4 (execução caixa-preta):** os resultados reais e a comparação com as
previsões estão na §11. As correções que eles motivaram estão marcadas com **[Fase 4]** nas §3.1, §3.3, §3.6 e §4.4.
As previsões originais continuam congeladas em `relatorio/03-casos-de-teste.md` (SHA-256 em `hashes-originais.txt`).

Evidência REA: `trabalho/fase3a-evidencias.json` (35 registros, 0 unknowns). Pseudocódigo salvo em
`trabalho/pseudocodigo/<endereço>.c`, com o Evidence ID na 1ª linha e indexado em `INDICE.tsv`.

## Resumo

| Pergunta | Resposta curta |
|---|---|
| Ponto de entrada | `CalculatorButton.ButtonId` → `StandardCalculatorViewModel::OnButtonPressed` 0x1800d5aa0 → `CalculatorManager::SendCommand` 0x18010d3d0 → `engine::ProcessCommand` 0x180112db0 [O] |
| Representação | valores racionais de precisão arbitrária (par numerador/denominador). Exibição limitada a 16 dígitos no modo Padrão e 32 no Científico [O] |
| Ordem de avaliação | modo Padrão avalia na hora (2 + 3 × 4 = 20). Modo Científico usa precedência com pilha de 25 níveis [O] |
| Divisão por zero | `divrat` 0x180133a60 lança `0x80000000` (x÷0) ou `0x80000002` (0÷0). O `catch` de `DoOperation` chama `DisplayError` 0x18012b640, que exibe `CEngineStrings/99` "Cannot divide by zero" / "Não é possível dividir por zero" ou `/101` "Result is undefined" / "Resultado indefinido" [O] |
| Texto de erro | chave = `to_wstring((código & 0xFFFF) + 99)`, buscada **por nome** num `unordered_map<wstring,wstring>` global [O] |
| Depois do erro | o motor ignora tudo, exceto C (CE vira C). O VM manda C antes de dígitos e do separador decimal e descarta o resto [O] |

## 1. Cadeia de chamadas

```
CalculatorButton (XAML, C#)  ButtonId = Add/Subtract/Multiply/Divide/Equals/Zero…Nine/…        [O XBF, 01 §7.3]
 └► ICommand ButtonPressed → StandardCalculatorViewModel::OnButtonPressed 0x1800d5aa0           [O, 01 §6.3]
     ├ se IsInError: SendCommand(Clear 81) e só segue para 0–9, Decimal, A–F, BINPOS             [O, 01 §6.3]
     └► CalculatorManager::SendCommand 0x18010d3d0 (VM+0x178)                                    [O, 01 §6.4]
         └► engine::ProcessCommand 0x180112db0 (engine atual = CalculatorManager+0x10)           [O]
              ├ dígitos/decimal/⌫/±(digitando) → objeto de entrada em motor+0x28                 [O §3.1]
              ├ + − × ÷ → acumulador/pilha; DoOperation 0x180131140 (try/catch)                  [O §3.3]
              ├ =      → DoOperation (repetição com motor+0xe0)                                  [O §3.4]
              ├ √ x² 1/x % ± → SciCalcFunctions 0x1801286f0 (try/catch)                          [O §3.5]
              ├ DisplayNum 0x18012bb70 → NumberToString 0x1801300f0 → agrupamento 0x18012c350    [O §5]
              │     └► ICalcDisplay slot0 SetPrimaryDisplay(texto, false) / slot1 SetIsInError    [O]
              └ erro: catch → DisplayError 0x18012b640 → slot0(texto, true), slot1(true),
                      motor+0xe20 = 1                                                              [O §4]
 ◄── CalculatorDisplay → VM 0x1800d35b0: DisplayValue + IsInError → PropertyChanged → XAML       [O, 01 §6.5]
```

`SendCommand` repassa os códigos de 3a sem tradução (só 200/201/209, 321–323, 119 e as inversas são
tratados à parte, 01 §6.4) [O]. Os botões do modo Padrão e seus `ButtonId` estão em
`Views/CalculatorStandardOperators.xbf` e `Views/NumberPad.xbf` [O]:

| Botão (Name EN-US / PT-BR) | `ButtonId` | código | Tratado em |
|---|---|---:|---|
| Zero … Nine / Zero … Nove | `Zero..Nine` | 130–139 | entrada (§3.1) |
| Decimal separator / Separador decimal | `Decimal` | 84 | entrada |
| Backspace / Backspace | `Backspace` | 83 | entrada |
| Clear entry / Limpar entrada | `ClearEntry` | 82 | §3.2 |
| Clear / Limpar | `Clear` | 81 | §3.2 |
| Positive negative / Positivo negativo | `Negate` | 80 | §3.1 / §3.5 |
| Plus, Minus, Multiply by, Divide by / Mais, Menos, Multiplicar por, Dividir por | `Add`,`Subtract`,`Multiply`,`Divide` | 93, 94, 92, 91 | §3.3 |
| Equals / Igual a | `Equals` | 121 | §3.4 |
| Percent / Por cento | `Percent` | 118 | §3.5 |
| Square root / Raiz quadrada | `Sqrt` | 110 | §3.5 |
| Square / Quadrado | `XPower2` | 111 | §3.5 |
| Reciprocal / Recíproco | `Invert` | 114 | §3.5 |

## 2. Estruturas de dados (engine) [O, salvo indicação]

| Offset | Conteúdo | Evidência |
|---|---|---|
| +0x00 | `bool` precedência (construtor `a`; Padrão 0, Científico/Programador 1) | testado antes de avaliar o operador pendente: `if (prec(novo) <= prec(pendente) \|\| *motor == 0)` em 0x180112db0 |
| +0x01 | `bool` modo inteiro (construtor `b`; só Programador) | ramos `param_1[1]` em `DoOperation`, `NumberToString` 0x180116f90 e `SetMaxDigits` 0x18012d820 |
| +0x18 | operador binário pendente (código; 0 = nenhum) | gravado em `LAB_18011622f` e no ramo "troca de operador"; zerado por C |
| +0x1c | operador anterior (usado na precedência) | |
| +0x20 | `bool` "há operador pendente para avaliar" | 1 após operador binário, 0 após `=` |
| +0x21 | `bool` "digitando um número" | 1 ao digitar ou após CE; 0 quando o número é finalizado (0x180121d50 converte o texto para racional) |
| +0x28… | objeto de entrada: +0x28 expoente-em-edição, +0x29 tem separador, +0x30 posição do separador, +0x40 texto da mantissa (`wstring`), +0x88 sinal, +0x68 texto do expoente, +0xb0 sinal do expoente [I nos papéis exatos] | `FUN_180121670` (dígito), `0x180121900` (decimal), `0x1801219b0` (⌫), `0x180112bc0` (CE) |
| +0x90 | formato de número 0 = flutuante, 1 = científico (alternado por FToE 119) | `case 0x77` em 0x180112db0 |
| +0xe0 | último operando direito (para `=` repetido) | `case 0x79` |
| +0x120 | **valor atual** (racional, 0x40 bytes = 2 × {sinal, expoente, vetor de dígitos}) | `FUN_18010db40` copia 0x40 bytes |
| +0x160 | **acumulador** (operando esquerdo) | |
| +0x7e0 / +0xedc / +0xf40 | pilha de precedência: 25 valores de 0x40 bytes, 25 operadores e profundidade | limite `< 0x19` |
| +0xe20 | `bool` **em erro** | gravado por `DisplayError`; limpo por CE/C (`0x180112bc0`) |
| +0xe21 | `bool` INV | `case 0x92` |
| +0xe22 | `bool` "operando novo": 1 após operador binário ou C, 0 após `=` | controla o `=` repetido (§3.4) |
| +0xe24 / +0xe28 / +0xe2c | base (10) / precisão / máximo de dígitos de entrada | precisão = 16 (Padrão, 0x18010d0e0), 32 (Científico, 0x18010d1f0), 64 (Programador, 0x18010d300); +0xe2c = +0xe28 em base 10 fora do modo inteiro (`SetMaxDigits` 0x18012d820) |
| +0xe48 | texto do visor (`wstring`) | `DisplayNum` 0x18012bb70 |
| +0xe68 / +0xf48 | comando atual / último comando | início de 0x180112db0 |
| +0xe70 | parênteses abertos | `case 0x79` fecha todos antes do `=` |
| +0xf70 | coletor de histórico/expressão | `FUN_18010ec10` (binário), `0x18010f200` (unário), `0x18010eae0` (operando) |
| +0x11a0 / +0x11a2 | separador decimal / de milhar | regex em 0x18012be50, agrupamento em 0x18012c350 |

Representação numérica [O nos campos, I nos nomes]: cada valor é um par (numerador, denominador), cada um
`{int sinal; int nº de dígitos; int expoente; vetor<uint32> dígitos}`. `divrat` 0x180133a60 testa o zero
percorrendo `dígitos[0..n)`. O detalhamento fica para a Fase 3f.

## 3. Regras por comando

### 3.1 Entrada de número [O]
- Dígito `d` (130 + d): só é aceito se `d < base` (`iVar22 - 0x82 < motor+0xe24`); se não, é ignorado.
  `FUN_180121670`:
  - **zero à esquerda não entra**: com o buffer vazio, o dígito 0 não é acrescentado (`if (len != 0 || d != 0)`);
  - **limite**: comprimento máximo = `maxDígitos + 1 − (sem separador ? 1 : 0)`, mais 1 se o texto começa com
    `0`. Ou seja, 16 dígitos significativos no Padrão e 32 no Científico, sem contar o `0.` inicial;
  - **no limite**: retorna 0. `ProcessCommand` restaura o último comando, chama `ICalcDisplay` slot 5
    (`MaxDigitsReached` → anúncio `Format_MaxDigitsReached` "Max digits reached. %1" / "Nº máximo de dígitos
    alcançado. %1") e não muda o visor;
  - expoente (modo `Exp`, Científico): no máximo 4 dígitos.
- Separador decimal (84), `0x180121900`: ignorado se já existe separador ou se está no expoente. Com o buffer
  vazio, grava `0` antes. Logo, "." ⇒ `0.`.
- Dígito ou separador logo após `)` (só Científico): insere `×` implícito (`motor+0x18 = 0x5c`).
- ⌫ (83): só atua digitando (+0x21). Remove o último caractere e, se o que sobra é `"0"` (compara com
  `L"0"` em 0x1801880a8), remove esse também. Fora da digitação, por exemplo após `=`, **é ignorado** pelo
  motor (`goto LAB_180113e62`) e o visor não muda. **[Fase 4]** Mesmo assim, ⌫ logo após `=` **apaga a linha de
  expressão**: antes do despacho, todo comando que chega com +0xe22 == 0 passa por `FUN_180112c40` (§3.6) [O].
- ± (80) digitando, em base 10: alterna o sinal do texto (+0x88), ou o sinal do expoente se estiver nele. Com o
  buffer vazio ("0"), só zera o sinal, então **"0 ±" continua 0**.

### 3.2 CE e C [O]
- **CE (82)** → `FUN_180112bc0`: esvazia o buffer, liga "digitando", **limpa o erro** (+0xe20 = 0) e mostra 0.
  Não mexe no acumulador nem no operador pendente: `5 + 3 CE 2 =` ⇒ 7.
- **C (81)**: acumulador = 0; zera operador pendente e anterior, último comando, pilha de precedência, parênteses
  (`ICalcDisplay` slot 3 com 0) e expressão (`FUN_18010fc30` com texto vazio); +0xe22 = 1. Depois **cai no
  caso CE** (não há `break`).

### 3.3 Operadores binarios + − × ÷ [O]
Ao receber o operador `op`:
1. Se o último comando **também** foi um operador binário: só **troca** o operador pendente e o token da
   expressão (`5 + × 3 =` ⇒ 15).
2. Senão:
   - se há operador pendente (+0x20): calcula `prec(op)` com `FUN_180112b30` (Or/Xor 0, And/Nand/Nor 1,
     + − 2, × ÷ Mod Lsh Rsh 3, ^ yroot logy 4). **No modo Padrão (+0x00 = 0) avalia sempre na hora**:
     `atual = DoOperation(pendente, atual, acumulador)`. No Científico, se `prec(op) > prec(pendente)`,
     empilha o par (acumulador, pendente), com no máximo 25 níveis;
   - depois: slot 6 (anúncio do operador), `acumulador = atual`, `pendente = op`, token ` op ` na expressão,
     +0x20 = 1, +0xe22 = 1.
- **[Fase 4] Linha de expressão no modo Padrão ao encadear operadores [O, 0x180112db0, bloco após `DoOperation`
  com a condição `motor+0xe20 == 0 && (DisplayNum(), *motor == 0)`].** Quando há operador pendente e chega outro
  binário, além de avaliar, o motor executa um **`=` implícito** na expressão:
  1. acrescenta o token `=` (chave `41`, `FUN_180094ca0(…, 0x29)` → `FUN_18010fd90`);
  2. chama `ICalcDisplay` slot 2 (`*(motor+0xf80) + 0x10`) com os tokens e comandos do coletor (+0x1000 / +0x1010);
  3. `FUN_18010fb30` finaliza o coletor: passa tokens e comandos ao objeto em coletor+0 (slot 1) e o resultado ao
     slot 7 de coletor+0x10. Depois esvazia os dois vetores. [I] É o registro de um item de **histórico**;
  4. `FUN_180110560` recria o operando a partir do **texto do visor** (`motor+0xe48`): dígito c → c + 0x52, separador
     → 0x54, `e` → 0x7f, `-` → 0x50, gerando um `COpndCommand`;
  5. em `LAB_18011622f`, o token do novo operador é acrescentado.

  Efeito: `2 + 3 ×` mostra **`5 ×`**, e `4 =` mostra **`5 × 4 =`**. A expressão `2 + 3 × 4 =` prevista em 3a-02 só
  acontece no Científico (`*motor == 1`, sem esse bloco). Consequência [I] para a Fase 3b: no Padrão, `2 + 3 × 4 =`
  deve gerar **dois** itens de histórico (`2 + 3 =` → 5 e `5 × 4 =` → 20).
- `DoOperation` 0x180131140 (`lhs` = acumulador, `rhs` = atual): + `FUN_180126c10` (addrat 0x180133d10),
  − `FUN_180126d50(lhs, rhs)` = lhs − rhs, × `FUN_180126e90` (mulrat 0x180133990),
  ÷ `FUN_180126fd0` (divrat 0x180133a60, precisão 0x80).

### 3.4 Igual (121) [O]
1. Fecha todos os parênteses abertos (envia `)` enquanto +0xe70 > 0 e não há erro).
2. Se +0xe22 == 0, ou seja, o `=` anterior foi o último comando de efeito: `acumulador = atual`.
3. Se não há operador pendente: só reexibe.
4. Senão, se +0xe22 == 0 (**`=` repetido**): `atual = motor+0xe0` (último rhs). Se +0xe22 == 1: `motor+0xe0 = atual`
   (guarda o rhs). Depois `atual = DoOperation(pendente, atual, acumulador)`, `acumulador = atual` e +0xe22 = 0.
5. Científico: desempilha e avalia o que restou na pilha de precedência.
6. Sem erro: acrescenta ` = ` (chave `41`) à expressão e notifica o histórico (Fase 3b).

Consequências:
- `2 + 3 = =` ⇒ 5, 8;
- `2 + 3 = 4 =` ⇒ 7 (4 + 3);
- `5 × =` ⇒ 25 (o rhs salvo é o próprio 5);
- `5 =` ⇒ 5.

O operador pendente (+0x18) **não** é zerado pelo `=`; só C o zera.

### 3.5 Unárias do modo Padrão: SciCalcFunctions 0x1801286f0 [O]
Antes de aplicar a unária: se o último comando foi operador binário, `atual = acumulador` (`5 + √` usa 5).

| Comando | Cálculo | Texto na expressão (chave) |
|---|---|---|
| √ 110 | `pow(x, 1/2)` (`FUN_18012de90`(2) = 1/2; `FUN_18012da60` = powrat 0x180137b70) | `√` (`30`, por `to_wstring(110−80)`) |
| x² 111 | `pow(x, 2)` | `sqr` (`91`, do mapa §7.3) |
| 1/x 114 | `1 ÷ x` (`FUN_180127b20` → divrat) | `1/` (`95`) |
| ± 80 (fora da digitação) | `−x` | `negate` (`97`) |
| % 118 | se o pendente é × ou ÷: `x/100`; senão: `x × (acumulador/100)` | nenhum token unário; o resultado entra como operando |

Formato do token unário [O no código, I na renderização final]: prefixo + `(` (chave `48`) + operando +
`)` (chave `49`), por exemplo `√(9)` e, aninhado, `sqr(√(9))`. **[Fase 4]** Na tela aparece `√( 9 )` e
`sqr( sqr( 9 ) )`, com afastamento visível dentro dos parênteses. Os valores das chaves 48/49/91 no PRI são `(`, `)` e `sqr`,
sem espaços [O, `trabalho/pri/CEngineStrings.tsv`]. Logo, o espaçamento vem da renderização (VM/XAML, L15) e não do
motor. Os símbolos do motor (`sqr`, `÷`, `×`, `1/`, `√`) aparecem **em inglês/símbolo** no Windows pt-BR. Já o
Narrador (Name UIA) usa "quadrado (" (L17).

### 3.6 Comandos depois de `=`: limpeza da linha de expressão [O] **[Fase 4]**
- No início de `ProcessCommand` 0x180112db0: `if (motor[0xe22] == 0) FUN_180112c40(motor);`. Isso vale para
  **qualquer** comando, antes do teste de erro e do despacho.
- `FUN_180112c40` cria dois vetores vazios (`vector<pair<wstring,int>>` e `vector<shared_ptr<IExpressionCommand>>`)
  e chama `ICalcDisplay` slot 2 (`+0x10`), isto é, `SetExpressionDisplay` com conteúdo vazio
  (`trabalho/pseudocodigo/0x180112c40.c`). Só a **exibição** é limpa: o coletor +0xf70 não é tocado.
- +0xe22 fica 0 depois de `=` (§3.4). Por isso o comando seguinte, seja ⌫, dígito ou `=`, começa com a linha
  vazia. Os que geram tokens a repõem: `= =` mostra `5 + 3 =` (3a-11), e `4 =` mostra `4 + 3 =` (3a-12). O ⌫
  não gera tokens, e a linha fica vazia (3a-24).

## 4. Erros e divisão por zero

### 4.1 Mecanismo [O]
1. As rotinas aritméticas lançam um código `DWORD` com `_CxxThrowException(&código, &ThrowInfo 0x1801d06a0)`.
2. `ProcessCommand` **não** tem bloco try: o FuncInfo4 (FH4) dele em RVA 0x1cabbc tem flags 0x28, isto é,
   UnwindMap + EHs, sem TryBlockMap. Os blocos try ficam em:
   - `DoOperation` 0x180131140: FuncInfo4 0x1cdaec, flags 0x38, TryBlockMap 0x1cdbe2. O handler é o funclet
     **0x18016831f**, referenciado em RVA 0x1cdbf2;
   - `SciCalcFunctions` 0x1801286f0: FuncInfo4 0x1ccebc, TryBlockMap 0x1cd060. O handler é o funclet
     **0x180167c8d**, referenciado em RVA 0x1cd070.

   Os dois funclets fazem só `DisplayError(motor, código)` e devolvem uma cópia de um operando.
3. **`DisplayError` 0x18012b640**:
   - `texto = mapa[to_wstring((u16)código + 99)]`;
   - `ICalcDisplay` slot 0 (`SetPrimaryDisplay(texto, true)`) e slot 1 (`SetIsInError(true)`);
   - **motor+0xe20 = 1**;
   - `FUN_18010fc30(texto)`, que só age com texto vazio. Portanto a linha de expressão **não** é limpa
     pelo erro.
4. `DisplayNum` 0x18012bb70: em base 10, depois de formatar, chama `FUN_18012be50(motor, texto, …,
   precisão, 10)`. Se o texto não casa com `[+-]?(\d*)[sep]?(\d*)(?:e[+-]?(\d*))?$`, se o expoente tem
   **5 ou mais dígitos** ou se (dígitos inteiros sem zeros à esquerda + fracionários) > precisão, chama
   `DisplayError(0x80000008)` (Overflow).

### 4.2 Códigos observados → chave → texto
| Código | Onde é lançado [O] | Chave | EN-US | PT-BR |
|---|---|---|---|---|
| 0x80000000 | divrat: divisor zero com dividendo ≠ 0 (0x180133a60) | 99 | Cannot divide by zero | Não é possível dividir por zero |
| 0x80000001 | `ProcessCommand` (domínio de unárias científicas, 0x180112db0); powrat de base negativa com expoente de denominador par e de 0 com expoente negativo (0x1801387e0) | 100 | Invalid input | Entrada inválida |
| 0x80000002 | divrat: 0 ÷ 0 | 101 | Result is undefined | Resultado indefinido |
| 0x80000007 | falha de `calloc` (0x1801387e0, 0x180137c30) | 106 | **chave ausente → texto vazio** [O §7.1] | — |
| 0x80000008 | `DisplayNum` (estouro de expoente) | 107 | Overflow | Estouro |
| 0x80000009 | Lsh/RshL no modo inteiro, deslocamento ≥ largura (`DoOperation`, Fase 3d) | 108 | Result not defined | Resultado não definido |

As chaves 105 (Not enough memory), 118, 119 e 120 existem no PRI, mas nenhum lançamento de código 6, 19,
20 ou 21 foi encontrado nas funções lidas (L14).

### 4.3 Divisão por zero passo a passo (`8 ÷ 0 =`, modo Padrão) [O]
1. `8`: o buffer recebe `8`. `÷`: finaliza o número (atual = 8). Como não há pendente, faz acumulador = 8,
   pendente = ÷ (91), expressão `8 ÷ `, +0xe22 = 1.
2. `0`: com o buffer vazio, o dígito 0 não é gravado e o buffer continua vazio (o valor é 0).
3. `=`: finaliza (atual = 0). Com +0xe22 = 1, faz `motor+0xe0 = 0` e chama `DoOperation(91, 0, 8)`:
   `divrat(8, 0)` multiplica cruzado e o denominador vira 0, então lança `0x80000000`.
4. O catch (funclet 0x18016831f) chama `DisplayError(0x80000000)` → chave `"99"` → "Cannot divide by zero"
   (EN-US) / "Não é possível dividir por zero" (pt-BR) → visor + `IsInError = true`, motor+0xe20 = 1.
5. Volta ao `=`: como há erro, não acrescenta `=` à expressão e não registra histórico. [I] A linha de
   expressão continua `8 ÷`: o token do operando `0` foi criado internamente, mas `SetExpressionDisplay`
   (slot 2) só é chamado no ramo sem erro.

`0 ÷ 0 =` segue o mesmo caminho e divrat lança `0x80000002`: "Result is undefined" / "Resultado indefinido".
`1/x` com x = 0 calcula `1 ÷ 0` e dá "Cannot divide by zero" (catch 0x180167c8d).

### 4.4 Estado de erro [O]
- Motor: com +0xe20 ligado, só C (81) passa. CE (82) é convertido em C. O resto é descartado e o "último
  comando" é restaurado (`LAB_180113e6c`).
- VM (`OnButtonPressed`, 01 §6.3): com `IsInError`, envia C e depois o dígito/separador. Outros botões são
  descartados. Consequência: depois do erro, `5` mostra 5 como um cálculo novo, e `+` não faz nada.
- **[Fase 4] Detalhe da VM [O, 0x1800d5aa0 + bytes]:** com `IsInError` (vtable +0x350), a VM chama
  `ProcessCommand(motor, 0x51)` **diretamente** (C). Só continua se o botão estiver na tabela 0x180189538..0x180189564
  (0x82–0x8b = 0–9 e 0x54 = separador) ou, fora da faixa 700–763, na tabela 0x1801894c8..0x1801894e0 (0x8c–0x91 =
  A–F). **CE (0x52) não está em nenhuma das duas:** CE em erro executa só o C. O C limpa a expressão
  (`FUN_18010fc30` com texto vazio → `ICalcDisplay` slot 2 vazio, §3.2). Logo, `8 ÷ 0 = CE` deixa o visor `0` e a
  **expressão vazia** (3a-10). A previsão "provavelmente ainda `8 ÷`" contrariava esses fatos já observados.
- **[Fase 4] Botões desabilitados em erro [O, caixa-preta, UIA `IsEnabled`]:** `%`, `1/x`, `x²`, `√`, `÷`, `×`,
  `−`, `+`, `,`, `±`, `M+`, `M−` e `MS`. MC, MR e M▾ já estavam desabilitados antes do erro (memória vazia). Continuam
  ativos: dígitos, CE, C, ⌫, `=`, Navegação, Histórico e Sobrepor. Por isso, em 3a-09, o `+` nem chega à VM. A
  vinculação `IsEnabled` ↔ erro não foi localizada (XAML/C# em `CalculatorApp.dll`, L3/L19). Note que o separador
  `,` fica **desabilitado na tela**, embora a VM o aceite em erro: só o teclado chegaria a esse caminho [I, não testado].

## 5. Formatação do visor [O no código; I nos exemplos numéricos]
`DisplayNum` 0x18012bb70 → `FUN_180116f90` → `NumberToString` 0x1801300f0(número, formato = motor+0x90,
base, precisão), depois agrupamento `FUN_18012c350` e então `ICalcDisplay` slot 0. Regras lidas de
0x1801300f0:
- arredonda para `precisão` dígitos significativos, somando meia unidade na última casa (`FUN_1801393b0`);
- **notação científica** quando a posição da vírgula passa da precisão (|x| ≥ 10^16 no Padrão) ou quando
  faltariam casas (|x| < 10⁻³ com mais de `precisão` casas fracionárias). Formato `d.ddd` + `e` + `+`/`-` +
  expoente;
- o separador decimal no fim do texto é removido. Na notação científica ele fica antes do `e`, então
  `1.e+16` mantém o ponto;
- sinal `-` só se houver dígitos;
- agrupamento de milhar em base 10 pelo separador `motor+0x11a2` e pela regra `motor+0xe30` (`FUN_18012ca00`);
- [I] Os separadores vêm de `sDecimal`/`sThousand`/`sGrouping` (`EngineResourceProvider`, 01 §6.8), ou seja,
  das **configurações regionais do Windows**, e não do idioma do app. Com formato pt-BR: `0,333…` e
  `1.234.567`.

## 6. Linha de expressão (resumo) [O nos tokens; I na renderização]
- Binário: tokens ` `, `op`, ` ` (`FUN_18010ec10`), com `op = mapa[to_wstring(código − 80)]`: ÷ `11`,
  × `12`, + `13`, − `14`.
- Unário: §3.5. Igual: ` = ` (`41`). Percentual: entra o número resultante.
- A VM monta o texto a partir dos tokens (`ICalcDisplay` slot 2 → 0x1800d3d30), e essa montagem não foi lida
  (L15).

## 7. `CEngineStrings`: como o motor usa as chaves

### 7.1 Carga e consulta [O]
- Carga (construtor de `CalculatorManager` → `FUN_180111b10`): percorre os 152 `wstring_view` de
  0x18018af40…0x18018b8c0 e chama `IResourceProvider` slot 1 (`EngineResourceProvider::GetCEngineString` →
  `ResourceLoader("CEngineStrings").GetString`). **Só grava no mapa se o texto não for vazio.**
- Consulta: `FUN_1800e5a40` = `operator[]` de um `unordered_map<wstring,wstring>` **global**
  (0x180206678, hash FNV-1a 64 em UTF-16). A chave é **o texto do id** (`to_wstring(n)` 0x180094ca0, ou um
  nome como `SecDeg`). **Uma chave ausente insere um nó com valor vazio e devolve `""`.**
- Portanto, a ordem e as "irregularidades" de índice da tabela 0x18018af40 (posição 1 = `62`, a falta de
  `36`/`98`/`110`, `10` repetido) **não afetam** o texto exibido. A tabela é só a lista do que carregar
  (resolve a dúvida de mapeamento chave→índice da L13).
- As 42 chaves pedidas que não existem no PRI ficam fora do mapa. Se forem consultadas, saem vazias. Entre as de
  erro: 102, 103, 104 e 106 (códigos 3, 4, 5, 7), além de 109 e 111–117.

### 7.2 Regra do texto por comando [O]
- Binários (`FUN_180116bf0`): procura o comando num mapa de exceções (§7.3). Se não acha, usa
  `to_wstring(código − 80)`.
- Unários (`FUN_1801168e0`): mapa de exceções com variantes normal/inversa e grau/radiano/grado (flag +0xf8
  "depende do ângulo"). Se a entrada não existe ou está vazia, usa `to_wstring(código − 80)`.

### 7.3 Mapa de exceções (inicializador estático 0x1800061d0 → `FUN_1801177e0`) [O]
| Comando | normal | inversa | radianos (n/inv) | grados (n/inv) |
|---|---|---|---|---|
| 98 (Int) | (fallback `18` "Int") | `66` frac | | |
| Sin 102 | `67` | `70` | `73`/`76` | `79`/`82` |
| **Cos 103** | **`68` cos₀** | `71` | `74`/`77` | `80`/`83` |
| Tan 104 | `69` | `72` | `75`/`78` | `81`/`84` |
| Sinh/Cosh/Tanh 105–107 | fallback `25`/`26`/`27` | `85`/`86`/`87` | | |
| LogBaseE 108 | fallback `28` ln | `88` e^ | | |
| XPower2 111 | `91` sqr | | | |
| Cube 112 | `92` cube | | | |
| Factorial 113 | `94` fact | | | |
| Invert 114 | `95` 1/ | | | |
| DMS 115 / Degrees 324 | fallback `35` dms / `96` | `96` degrees | | |
| Negate 80 | `97` negate | | | |
| Sec/Csc/Cot 400–404, Sech/Csch/Coth 406–410 | `SecDeg`… / `Sech`… | `InverseSecDeg`… | `SecRad`… | `SecGrad`… |
| TwoPowX 412, LogBaseY, Abs 413, Floor 414, Ceil 415, Nand 501, Nor 502 | nomes homônimos | | | |
| RshL 505 / RolC 416 / RorC 417 | `10` / `19` / `20` | | | |
| CubeRoot 116 | `CubeRoot` | | | |
| Mod 95 | `15` Mod (Programador: `ProgrammerMod`) | | | |

- **`cis` (`CEngineStrings/23`)**: `23 = 103 − 80` é a chave de fallback do **Cos**. Como Cos tem entradas
  próprias e não vazias no mapa (`68`, `74`, `80`), o fallback **não é usado** em `FUN_1801168e0` [O]. Fica
  [I] que `cis` não aparece na expressão de cosseno pelo caminho normal. Outros caminhos que montam texto de
  comando, como a restauração de snapshot e o histórico recarregado, ficam para a Fase 3c (L13).
- √ (110) **não** está no mapa e usa o fallback `30` = `√`.

## 8. Casos de borda (lista consolidada)
| # | Situação | Comportamento previsto | Base |
|---|---|---|---|
| B1 | x ÷ 0, x ≠ 0 | "Cannot divide by zero" / "Não é possível dividir por zero" | O |
| B2 | 0 ÷ 0 | "Result is undefined" / "Resultado indefinido" | O |
| B3 | `÷ 0 =` logo após C | 0 ÷ 0, então B2 | O |
| B4 | 1/x com 0 | B1 | O |
| B5 | √ de negativo | "Invalid input" / "Entrada inválida" | O (código) + I (papel de `FUN_1801379f0` = "é par") |
| B6 | depois de erro: operador, ⌫, ±, % | nada muda | O |
| B7 | depois de erro: dígito | começa do zero com o dígito | O |
| B8 | depois de erro: CE | visor 0, erro limpo | O |
| B9 | `=` repetido | repete o último operador com o último rhs | O |
| B10 | operador duas vezes | o último substitui o anterior | O |
| B11 | `a op =` | a op a | O |
| B12 | 17º dígito (Padrão) | ignorado + anúncio "Nº máximo de dígitos alcançado" (narrador) | O |
| B13 | zeros à esquerda | "000" mostra 0 | O |
| B14 | ⌫ após resultado | visor inalterado; **a linha de expressão é apagada** [Fase 4, §3.6] | O |
| B15 | ± em 0 sendo digitado | continua 0 | O |
| B16 | resultado com expoente de 5 dígitos | "Overflow" / "Estouro" | O (regra) + I (alcance) |
| B17 | erro com código sem chave no PRI (ex.: 0x80000007) | visor vazio em estado de erro | O (mecanismo); não reproduzível manualmente |
| B18 | Padrão sem precedência | `2 + 3 × 4 =` dá 20 (Científico: 14) | O |
| B19 | pilha de precedência cheia (> 25 níveis, Científico) | o empilhamento é ignorado (contador volta a 24 e é incrementado para 25), e o acumulador e o operador pendentes anteriores se perdem | O no código; efeito visível não verificado |

## 9. Casos de teste candidatos (para a Fase 4)
Modo **Padrão**, começando sempre com **C**. Os textos de erro valem para o Windows em português (Brasil);
entre parênteses, o EN-US. Separadores no formato regional pt-BR (`,` decimal e `.` milhar). Anote o que o
seu Windows mostrar, inclusive a linha de expressão.

| ID | Teclas | Visor previsto | Expressão prevista [I] | Base |
|---|---|---|---|---|
| 3a-01 | `7 + 5 =` | `12` | `7 + 5 =` | O |
| 3a-02 | `2 + 3 × 4 =` | `20` (visor mostra `5` ao apertar `×`) | `2 + 3 × 4 =` | O (sem precedência no Padrão) |
| 3a-03 | `9 − 12 =` | `-3` | `9 - 12 =` | O |
| 3a-04 | `8 ÷ 0 =` | **Não é possível dividir por zero** (Cannot divide by zero) | `8 ÷` | O / I (expressão) |
| 3a-05 | `0 ÷ 0 =` | **Resultado indefinido** (Result is undefined) | `0 ÷` | O |
| 3a-06 | `C ÷ 0 =` | **Resultado indefinido** | `0 ÷` | O |
| 3a-07 | `0` `1/x` | **Não é possível dividir por zero** | `1/(0)` | O |
| 3a-08 | `4 ± √` | **Entrada inválida** (Invalid input) | `√(-4)` | I |
| 3a-09 | após 3a-04: `+` e depois `5` | `+` não muda nada; `5` mostra `5` | (limpa) | O |
| 3a-10 | após 3a-04: `CE` | `0` | | O |
| 3a-11 | `2 + 3 = =` | `5`, depois `8` | `5 + 3 =` | O |
| 3a-12 | `2 + 3 = 4 =` | `7` | `4 + 3 =` | O |
| 3a-13 | `5 × =` | `25` | `5 × 5 =` | O |
| 3a-14 | `5 + × 3 =` | `15` | `5 × 3 =` | O |
| 3a-15 | `50 + 10 %` e depois `=` | `5`, depois `55` | `50 + 5`, depois `50 + 5 =` | O |
| 3a-16 | `50 × 10 %` e depois `=` | `0,1`, depois `5` | `50 × 0,1 =` | O |
| 3a-17 | `10 %` (logo após C) | `0` | | O |
| 3a-18 | `1 ÷ 3 =` | `0,3333333333333333` (16 dígitos 3) | | I (arredondamento, L16) |
| 3a-19 | `2 ÷ 3 =` | `0,6666666666666667` | | I |
| 3a-20 | digitar `12345678901234567` | `1.234.567.890.123.456` (o 17º dígito é ignorado) | | O (limite) / I (agrupamento) |
| 3a-21 | `9999999999999999 + 1 =` | `1,e+16` | | I (formato científico) |
| 3a-22 | `1 ÷ 3000 =` | `3,333333333333333e-4` | | I |
| 3a-23 | `0 0 0 ,` e depois `⌫` | `0`, `0,`, depois `0` | | O |
| 3a-24 | `2 + 3 =` e depois `⌫` | continua `5` | | O |
| 3a-25 | `0 ±` / `5 ±` | `0` / `-5` | | O |
| 3a-26 | `9999999999999999` e `x²` 10 vezes | da 1ª à 9ª, expoentes crescentes até ~e+8191; na **10ª: Estouro** (Overflow) | | I |
| 3a-27 | `9 √` | `3` | `√(9)` | O / I |
| 3a-28 | `3 x²` / `4 1/x` | `9` / `0,25` | `sqr(3)` / `1/(4)` | O / I |
| 3a-29 | `5 + 3 CE 2 =` | `7` | | O |

Os casos marcados com I são os que mais interessam: confirmam ou derrubam as inferências de §5, §6 e §7.

## 10. Lacunas desta fase
Registradas em `relatorio/04-lacunas.md`: L19 e L20 (novas na Fase 4; L15, L16 e L17 atualizadas), L13 (atualizada), L10 (parcialmente resolvida), L11 (atualizada),
L14–L18 (novas).

## 11. Resultados da Fase 4 (execução caixa-preta, 2026-10-22)

**Execução.** `trabalho/automacao/rodar-casos.ps1` (UI Automation, PowerShell 5.1, sem instalação) na Calculadora
instalada 11.2607.0.0 x64, com Windows, cultura e UI em pt-BR. Os SHA-256 de `CalculatorApp.exe`,
`CalculatorApp.dll` e `CalcViewModel.dll` instalados são **idênticos** aos de `./binarios`
(`trabalho/automacao/log-execucao.txt`).
- **Visor:** texto do filho bruto `NormalOutput` de `CalculatorResults`.
- **Expressão:** transcrita das capturas `trabalho/automacao/capturas/*.png`. O UIA só expõe o texto do Narrador
  (L20).
- **Resultados:** `relatorio/resultados-reais.txt`.

**Critério.**
- *Acerto*: todas as leituras previstas conferem (visor exato; expressão igual, ignorando espaços, L20).
- *Parcial*: o visor confere e alguma leitura de expressão não.
- *Erro*: o visor não confere.

| ID | Bloco | Previsto (resumo) | Real | Classe |
|---|---|---|---|---|
| 3a-18 | A | `0,3333333333333333` \| `1 ÷ 3 =` | igual | acerto |
| 3a-19 | A | `0,6666666666666667` \| `2 ÷ 3 =` | igual | acerto |
| 3a-22 | A | `3,333333333333333e-4` \| `1 ÷ 3000 =` | igual | acerto |
| 3a-21 | A | `1,e+16` \| `9999999999999999 + 1 =` ("talvez com pontos") | igual, sem pontos de milhar | acerto |
| 3a-20 | A | `1.234.567.890.123.456`, 17º ignorado \| vazia | igual | acerto |
| 3a-08 | A | Entrada inválida \| `√(-4)` | Entrada inválida \| `√( -4 )` | acerto |
| 3a-26 | A | 1º `9,999999999999998e+31`; expoentes +63…+8191 no 9º; 10º Estouro | igual em todos os 10 pontos | acerto |
| 3a-01 | B | `12` \| `7 + 5 =` | igual | acerto |
| 3a-02 | B | `5` → `20` \| `2 + 3 × 4 =` | `5` \| `5 ×` → `20` \| `5 × 4 =` | **parcial** (D1) |
| 3a-02c | B | `3` → `14` \| `2 + 3 × 4 =` | igual (intermediária `2 + 3 ×`) | acerto |
| 3a-03 | B | `-3` \| `9 - 12 =` | igual | acerto |
| 3a-04 | B | Não é possível dividir por zero \| `8 ÷` | igual | acerto |
| 3a-05 | B | Resultado indefinido \| `0 ÷` | igual | acerto |
| 3a-06 | B | Resultado indefinido \| `0 ÷` | igual | acerto |
| 3a-07 | B | Não é possível dividir por zero \| `1/(0)` | igual (`1/( 0 )`) | acerto |
| 3a-10 | B | erro → `0` \| após CE "provavelmente ainda `8 ÷`" | erro → `0` \| após CE **vazia** | **parcial** (D2) |
| 3a-11 | B | `5` → `8` \| `2 + 3 =` → `5 + 3 =` | igual | acerto |
| 3a-12 | B | `5` → `7` \| `2 + 3 =` → `4 + 3 =` | igual | acerto |
| 3a-13 | B | `25` \| `5 × 5 =` | igual | acerto |
| 3a-14 | B | `15` \| `5 × 3 =` | igual | acerto |
| 3a-15 | B | `5` → `55` \| `50 + 5` → `50 + 5 =` | igual | acerto |
| 3a-16 | B | `0,1` → `5` \| `50 × 0,1` → `50 × 0,1 =` | igual | acerto |
| 3a-17 | B | `0` \| `0` | igual | acerto |
| 3a-24 | B | `5` → `5` \| `2 + 3 =` (inalterada) | `5` → `5` \| após ⌫ **vazia** | **parcial** (D3) |
| 3a-27 | B | `3` \| `√(9)` | igual (`√( 9 )`) | acerto |
| 3a-28 | B | `9` → `0,25` \| `sqr(3)` → `1/(4)` | igual (`sqr( 3 )`, `1/( 4 )`) | acerto |
| 3a-29 | B | `7` \| `5 + 2 =` | igual | acerto |
| 3a-09 | C | erro → `+` sem efeito → `5` \| vazia | igual (`+` desabilitado na UI) | acerto |
| 3a-23 | C | `0` → `0,` → `0` \| vazia | igual | acerto |
| 3a-25 | C | `0` → `-5` \| vazia | igual | acerto |

**Taxa de acerto por bloco.**

| Bloco | Casos | Acerto | Parcial | Erro | Taxa |
|---|---:|---:|---:|---:|---:|
| A (visor INFERIDO) | 7 | 7 | 0 | 0 | 100% |
| B (visor O, expressão I) | 20 | 17 | 3 | 0 | 85% |
| C (tudo O) | 3 | 3 | 0 | 0 | 100% |
| **Total** | 30 | 27 | 3 | 0 | 90% |

Todas as 54 leituras de visor (finais e intermediárias) conferiram. As três falhas estão na linha de expressão, a parte marcada [I] no bloco B.

**Divergências explicadas no binário** (todas [O], com evidência nas seções indicadas):
- **D1, 3a-02:** no Padrão, encadear um operador faz um `=` implícito na expressão, que é finalizada e reiniciada
  a partir do resultado (§3.3, bloco [Fase 4]). Causa da previsão errada: a análise da 3a leu a avaliação
  (`DoOperation`), mas não o bloco de expressão e histórico sob `*motor == 0`.
- **D2, 3a-10:** em erro, a VM troca qualquer botão não numérico por C, e o C limpa a expressão (§4.4, bloco
  [Fase 4]). Os fatos já estavam observados (§3.2, §4.4). A previsão os combinou mal.
- **D3, 3a-24:** após `=`, todo comando passa por `FUN_180112c40`, que apaga a exibição da expressão (§3.6). A
  §3.1 tratava só do visor.

**Checagem cruzada com os resultados manuais.**
- 3a-18, 3a-19, 3a-21, 3a-22, 3a-20 e 3a-01 são idênticos aos da automação.
- 3a-26: visor e estado dos botões em erro iguais. **Diverge** a expressão: o manual tem 8 `sqr(`, a automação 10.
  O Name UIA tem 10 "quadrado (" e a captura mostra a linha **cortada à esquerda** com seta de rolagem. [I] O manual
  transcreveu só a parte visível. Não afeta a previsão, que não incluía a expressão.

**Inferências confirmadas pela execução.**
- §5: arredondamento para 16 dígitos e notação científica `1,e+16` / `e-4` (L16).
- §5: separadores pela cultura pt-BR.
- §3.1: limite de 16 dígitos.
- §4.1: Estouro no 10º `x²`, ou seja, expoente de 5 dígitos.
- §7.1 / L17: símbolos do motor em inglês no Windows pt-BR.
