# 02d — Modo programador (Fase 3d)

Alvo: `CalcViewModel.dll` (SHA-256 `072cd589…d21d`), 11.2607.0.0 x64. Análise estática com REA 6.7.0 / Ghidra 12.1.4,
sessão reaberta do snapshot da Fase 1. Data: 2026-10-23.

Convenção: **[O]** OBSERVADO (pseudocódigo, assembly ou bytes, com endereço); **[I]** INFERIDO (com o raciocínio).
`motor+0xNNN` é um offset no objeto da engine (0x11a8 bytes). Os nomes de funções são **rótulos** desta análise (L1).

Evidência REA: `trabalho/fase3d-evidencias.json`. Funções novas lidas: `FUN_18012d140` (troca de base/tamanho),
`FUN_18012d520` (bit), `FUN_180111fe0` (máscaras e limites), `FUN_180116e10` (valor numa base), `FUN_1800d9b20` (painel da VM),
`FUN_1800d8a40` (`SwitchProgrammerModeBase`), `FUN_1800db070` (`set_ValueBitLength`), as rotinas de bits do ratpak
(0x18013a460 lsh, 0x18013a6b0 rsh, 0x18013a900 and/or/xor, 0x18013ab80 rem, 0x180123a00 int) e os embrulhos 0x180127xxx.
Também foram relidos `DoOperation` 0x180131140, `SciCalcFunctions` 0x1801286f0, `ProcessCommand` 0x180112db0, `DisplayNum`
0x18012bb70, `FUN_18012b790` (truncamento), `NumberToString` inteiro 0x180116f90, o agrupamento 0x18012c350 e a entrada de
dígitos 0x180121670. Previsões numéricas: `trabalho/scripts/prog3d.py`.

## Resumo

| Pergunta | Resposta curta |
|---|---|
| Ponto de entrada | `OnButtonPressed` 0x1800d5aa0 → `SendCommand` 0x18010d3d0 → `ProcessCommand` 0x180112db0 da engine de programador (`CalculatorManager+0x28`; precedência ligada, **modo inteiro** `motor+0x01 = 1`, precisão 64) [O, 01 §6.6] |
| Base | comandos 313–316 (HEX, DEC, OCT, BIN) → `FUN_18012d140(motor, 0..3, −1)` → `motor+0xe24` = 16/10/8/2 [O] |
| Tamanho | comandos 317–320 (QWORD, DWORD, WORD, BYTE) → `FUN_18012d140(motor, −1, 0..3)` → `motor+0xf50` = 0..3, `motor+0xf54` = 64/32/16/8 [O] |
| Representação | depois de cada `DisplayNum`, o valor atual fica como **inteiro sem sinal truncado à largura** (`FUN_18012b790`: parte inteira; negativo → complemento de dois; AND máscara) [O] |
| Exibição | DEC mostra **com sinal** (bit w−1 ligado → valor − 2^w); HEX/OCT/BIN mostram os bits sem sinal [O, 0x180116f90] |
| Agrupamento | HEX e BIN em grupos de 4, OCT em grupos de 3, separador **espaço**; DEC com o milhar do idioma [O, 0x18012c350, 0x18017cb14 = 0x20] |
| Troca de tamanho | se o bit de sinal está ligado **na largura antiga**, o valor vira negativo; depois é truncado na largura nova → estreitar corta bits altos, alargar **estende o sinal** [O] |
| Limites de digitação | HEX w/4, BIN w, OCT ⌊w/3⌋ (+1 dígito se o 1º for `1` e w mod 3 = 1, ou se for < `4` e w mod 3 = 2), DEC: o texto não pode passar de 2^(w−1)−1 (2^(w−1) se negativo) [O, 0x180121670 + 0x180111fe0] |
| AND OR XOR NAND NOR NOT | ratpak 0x18013a900 (0/1/2 = and/or/xor) sobre a parte inteira; NOT = XOR máscara; NAND/NOR = NOT(AND/OR) [O] |
| Deslocamentos | Lsh/Rsh/RshL binários; **n ≥ largura → "Resultado não definido"**; Rsh estende o sinal; RshL não; Rol/Ror/RolC/RorC são **unários de 1 bit**; RolC/RorC usam um carry em `motor+0xf68` que só C zera [O] |
| ÷ e Mod | sobre magnitudes; quociente **truncado** com sinal pelo XOR dos sinais; resto com o **sinal do dividendo**; `x Mod 0` → "Resultado indefinido" (no Científico dá x) [O] |
| Estouro | não há erro de estouro: o resultado é truncado à largura (2^63−1 + 1 = −2^63) [O] |
| Teclado de bits | BINPOS n (700+n) → `FUN_18012d520`: se n < largura, valor XOR 2^n; logo depois de um operador binário age sobre o **acumulador** [O] |

## 1. Cadeia de chamadas

```
XAML (CalculatorProgrammerRadixOperators.xbf, …DisplayPanel.xbf, …BitFlipPanel.xbf, …Operators.xbf)  [O, XBF]
  Bases: hexButton / decimalButton / octButton / binaryButton (RadixButton, atalhos F5/F6/F7/F8) → VM SwitchProgrammerModeBase
  Tamanho: QwordButton/DwordButton/WordButton/ByteButton (CommandParameter 0..3; só QWORD visível no início; atalhos
           F2/F3/F4/F12) → C# BitLengthButtonPressed (CalculatorApp.dll, .NET Native, não lido, L27) → VM set_ValueBitLength
  Bit a bit (bitwiseButton → BitwiseFlyout): And 86, Or 87, Not 101, Nand 501, Nor 502, Xor 88
  Deslocamento (bitShiftButton → BitShiftFlyout, 4 opções): aritmético Lsh 89 / Rsh 90; lógico Lsh 89 / RshL 505;
           circular Rol 99 / Ror 100; com carry RolC 416 / RorC 417 (os pares não usados ficam Collapsed)
  Teclado de bits (bitFlip): Bit0..Bit63 → BINPOS0..63 (700..763)
 └► VM
     ├ SwitchProgrammerModeBase 0x1800d8a40: se em erro (vslot 0x350, [I] IsInError) manda Clear (0x51) antes;
     │  depois 313/314/315/316 a ProcessCommand                                                    [O]
     ├ set_ValueBitLength 0x1800db070: grava VM+0x2c4 e dispara um comando pelo vslot 0x470 [O; I: é o 317–320]
     ├ OnButtonPressed 0x1800d5aa0 → SendCommand 0x18010d3d0 (repassa os códigos acima sem tradução) [O, 01 §6.3–6.4]
     └ painel HEX/DEC/OCT/BIN: FUN_1800d9b20 → para 16, 10, 8 e 2: FUN_180116e10(motor, base, agrupar) → setters
       HexDisplayValue (0x1800d01f0), DecimalDisplayValue (0x1800d0150), OctalDisplayValue (0x1800d0300),
       BinaryDisplayValue (0x1800d03b0); BinaryDigits = bits do texto binário sem agrupamento            [O]
 └► engine::ProcessCommand 0x180112db0 (engine +0x28)
     ├ início: 313–320, 700–763 e operadores **finalizam** o número em digitação (texto → racional → DisplayNum)
     │  ± em base 10 não finaliza (troca o sinal do texto); em outras bases finaliza e nega              [O]
     ├ dígito 0x82+d: aceito só se d < base; limite em FUN_180121670                                  [O]
     ├ 0x139–0x13c → FUN_18012d140(base) + FUN_180110180 (refaz a expressão na base nova)            [O]
     ├ 0x13d–0x140 → FUN_18012d140(tamanho)                                                           [O]
     ├ 700–763 → FUN_18012d520 (bit)                                                                  [O]
     ├ unárias 0x63 Rol, 0x64 Ror, 0x65 Not, 0x1a0 RolC, 0x1a1 RorC → SciCalcFunctions 0x1801286f0     [O]
     └ binárias 0x56 And, 0x57 Or, 0x58 Xor, 0x59 Lsh, 0x5a Rsh, 0x5b ÷, 0x5f Mod, 0x1f5 Nand, 0x1f6 Nor,
       0x1f9 RshL (+ − × como antes) → precedência (02c §3.11) → DoOperation 0x180131140               [O]
     DisplayNum 0x18012bb70: no modo inteiro trunca o valor (FUN_18012b790) **e grava de volta** em motor+0x120,
       formata (0x180116f90), agrupa (0x18012c350) e manda ao visor                                  [O]
```

## 2. Estruturas de dados [O]

| Offset | Conteúdo | Evidência |
|---|---|---|
| +0x01 | modo inteiro (1 no Programador) | ctor 0x180111bd0 (`b`), testes em DoOperation/SciCalcFunctions/DisplayNum |
| +0xe24 | base 16/10/8/2 | `FUN_18012d140` |
| +0xe28 / +0xe2c | precisão (64) / máximo de dígitos na base atual | `FUN_18012d820`: base ≠ 10 → `largura / bits_por_dígito`; base 10 → `len(limite) − 1` |
| +0xf50 / +0xf54 | tamanho 0..3 / largura 64, 32, 16, 8 | `FUN_18012d140`, ctor (começa em 0 = QWORD) |
| +0xf68 | **carry** de RolC/RorC (64 bits) | `SciCalcFunctions` 0x1a0/0x1a1; zerado em `case 0x51` (C) de ProcessCommand |
| +0x1020 + 0x40·i | máscara do tamanho i: QWORD `DAT_1802053c0`, DWORD `…3c8`, WORD `…3d0`, BYTE `…3b8` | `FUN_180111fe0` |
| +0x1120 + 0x20·i | texto-limite em decimal = int(máscara / 2) → `9223372036854775807`, `2147483647`, `32767`, `127` | `FUN_180111fe0` (divrat por 2, intrat, NumberToString base 10) |
| +0x40 / +0x50 / +0x60 | texto em digitação / comprimento / sinal (`±` em base 10) | `FUN_180121670` (offsets relativos a +0x28), case 0x50 |

[I] Os valores das máscaras são 2^w − 1. Para `DAT_1802053c8`, isso é observado: `FUN_18012fd50` (racional → uint64) usa essa
máscara para separar as metades de 32 bits. Para as outras três, o valor vem da ordem e do uso, porque o init não foi lido.

## 3. Regras

### 3.1 Representação, truncamento e exibição [O]

- `FUN_18012b790(v)` (chamada por `DisplayNum` e por `NumberToString` no modo inteiro): `x = int(v)` (intrat 0x180123a00:
  subtrai a parte fracionária, ou seja, **trunca em direção a zero** [I pelo resto com sinal do dividendo, confirmado em
  caixa-preta na 3c]); se x < 0: `x = (|x| − 1) XOR máscara`; depois `x AND máscara`. Resultado: x mod 2^w.
- `DisplayNum` grava esse valor de volta em `motor+0x120`. Daí em diante, os operandos são sempre não negativos e menores que 2^w.
- `NumberToString` inteiro (0x180116f90): em **base 10**, se o bit w−1 está ligado, mostra −(2^w − x). Nas outras bases mostra
  x como está. Os dígitos vêm da tabela `0123456789ABCDEF…` (0x18018c410), em **maiúsculas**.
- Agrupamento (0x18012c350): base 2 e 16 → vetor {4, 0}, ou seja, grupos de 4 repetidos; base 8 → grupos de 3; o separador é
  `DAT_18017cb14` = U+0020 (espaço). Base 10 → `FUN_18012ca00` com o agrupamento do idioma (pt-BR: `.` a cada 3).
- **Correção pós-execução [O, 0x1800d98a0]**: a linha BIN do **painel** (não o visor) passa ainda por `FUN_1800d98a0` na
  VM, que conta os dígitos sem espaços e acrescenta zeros à esquerda até um múltiplo de 4 (`11 1110 1000` →
  `0011 1110 1000`); o valor `0` fica como está. A chamada aparecia em `FUN_1800d9b20` e não foi lida antes do
  congelamento (divergências 3d-02/03, §7).
- **[Correção pós-diferencial, 2026-10-23] O visor em BIN também é preenchido [O].** A afirmação acima de que o
  preenchimento é só do painel, "**(não o visor)**", foi uma **generalização sem verificação**. Ninguém procurou os
  outros chamadores de `FUN_1800d98a0`, e nenhum caso da 3d tinha visor BIN com quantidade de dígitos fora de múltiplo
  de 4 (3d-04 `1111 1111`, 3d-08 com 65 dígitos), então o oráculo não podia desmentir. Os chamadores são dois
  (Evidence `ev_aebc66a9…`): `FUN_1800d9b20` (painel) e **`FUN_1800d2ee0`**, chamada por `SetPrimaryDisplay`
  0x1800d35b0 com o texto do visor (Evidence `ev_5d2db40d…`, `trabalho/pseudocodigo/0x1800d2ee0.c`). Ela preenche
  quando o vslot 0x4e8 ≠ 0 e o vslot 0x428 devolve 8 (= `NumberBase.BinBase` no winmd) [O]; que esses slots sejam
  IsProgrammer e CurrentRadixType é [I]. Depois troca os dígitos pelos nativos do idioma.
  - **Sem teste de erro [O]:** a mensagem também é preenchida. "Resultado indefinido" tem 19 caracteres ≠ espaço, então
    ganha 1 zero: `0Resultado indefinido` (dif-Pr-070). As linhas do painel não mostram isso porque ficam vazias em erro
    (L29).
  - Visor em BIN observado: `0010`, `0001 1010`, `0111` (dif-Pr-020, 024, 047 e outros; `relatorio/03-diferencial-resultados.md`, A).
- Não existe estouro no Programador: `DisplayNum` só testa estouro em base 10 com mais de 64 dígitos, o que um inteiro de
  64 bits nunca atinge.

### 3.2 Base e tamanho: `FUN_18012d140(motor, base, tamanho)` [O]

1. No modo inteiro: se o bit `largura_atual − 1` de `motor+0x120` está ligado, o valor vira **−((x XOR máscara) + 1)**.
   O teste usa a largura antiga, porque +0xf54 ainda não mudou.
2. Grava a base (0→16, 1→10, 2→8, 3→2) e/ou o tamanho (0→64, 1→32, 2→16, 3→8).
3. `FUN_18012d820` recalcula o máximo de dígitos, `ratpak_init(base, …)` e `DisplayNum`, que trunca na largura nova.

Consequências: estreitar mantém os bits baixos (300 → BYTE = 44; 200 → BYTE = −56). Alargar preserva o valor **com sinal**:
BYTE −56 (C8) → QWORD = −56 (`FFFF FFFF FFFF FFC8`), não 200. Numa sequência de trocas, o resultado é o valor com sinal dos
bits da **menor largura visitada**.

- **Caminho na UI [I, L27]**: só um dos quatro botões de tamanho fica visível (QWORD no início; os outros nascem
  `Collapsed`), e cada um tem `CommandParameter` = o próprio índice 0..3. A hipótese é que o clique leva ao **próximo**
  tamanho: QWORD→DWORD→WORD→BYTE→QWORD. O handler C# `CalculatorProgrammerDisplayPanel.BitLengthButtonPressed`
  (`CalculatorApp.dll`, .NET Native) não foi lido. Os casos 3d-20…26 foram escolhidos para dar o mesmo resultado final nos
  dois sentidos do ciclo, exceto o **3d-23**, que discrimina o sentido.
- Troca de base: a mesma função, então o valor não muda, só a forma de exibir. `SwitchProgrammerModeBase` manda Clear antes
  se a VM estiver em erro, então trocar a base depois de um erro **zera** a calculadora [O no código; I em vslot 0x350 = IsInError].

### 3.3 Limites de digitação (`FUN_180121670`, modo inteiro) [O]

| Base | Dígitos livres (e2c) | Dígito extra no limite |
|---|---|---|
| 16 | w/4 (16, 8, 4, 2) | nunca |
| 2 | w (64, 32, 16, 8) | nunca |
| 8 | ⌊w/3⌋ (21, 10, 5, 2) | mais 1 se w mod 3 = 1 e o 1º dígito é `1` (QWORD, WORD), ou w mod 3 = 2 e o 1º dígito < `4` (DWORD, BYTE) |
| 10 | len(limite) − 1 (18, 9, 4, 2) | mais 1 se o texto não passar do limite (`9223372036854775807`…); com sinal negativo o último dígito pode passar 1 do limite (permite −2^(w−1)) |

Um dígito recusado não muda nada e só gera o anúncio "máximo de dígitos" (ICalcDisplay slot 5). Zeros à esquerda não entram.

### 3.4 Operações bit a bit [O]

- AND/OR/XOR: `FUN_1801274d0/127610/127760` → `0x18013a900(x, y, 0/1/2)`, que aplica `intrat` aos dois lados e opera
  palavra a palavra (`0x18013aa50`).
- NOT (0x65, unário): no modo inteiro, `FUN_180127bf0(x, máscara)` = **x XOR máscara**. (Fora do modo inteiro e em base 10,
  seria −(int(x)+1).)
- NAND (0x1f5) = (x AND y) XOR máscara; NOR (0x1f6) = (x OR y) XOR máscara (`DoOperation`).
- Precedência (02c §3.11): Or/Xor 0 < And/Nand/Nor 1 < + − 2 < × ÷ Mod Lsh Rsh RshL 3. Assim `6 OR 1 AND 2` = 6 e
  `1 OR 5 NAND 3` = −1.
- Texto da expressão (`FUN_180116bf0` com `motor[1]`): `AND`, `OR`, `XOR`, `NAND`, `NOR`, `Lsh`, `Rsh` (também para RshL,
  pela entrada 0x1f9 → chave `10`), e **`%` para Mod** (`ProgrammerMod`, o nome alternativo usado no modo inteiro). Unárias:
  `NOT(`, `RoL(`, `RoR(` (RolC/RorC também usam as chaves 19/20).

### 3.5 Deslocamentos [O]

| Operação | Código | Implementação |
|---|---|---|
| Lsh (aritmético e lógico) | 89 | `DoOperation 0x59`: se **n ≥ w** lança 0x80000009 ("Resultado não definido"); senão lsh = x·2^n (0x18013a460); a truncagem vem do DisplayNum |
| Rsh (aritmético) | 90 | mesmo teste; r = x/2^n (0x18013a6b0); se o bit w−1 de x está ligado: r = int(r) OR ((máscara/2^n) XOR máscara), ou seja, **estende o sinal** |
| RshL (lógico) | 505 | mesmo teste; r = x/2^n, sem extensão |
| Rol | 99 | unário: msb = bit w−1; r = (x·2) OR msb |
| Ror | 100 | unário: lsb = bit 0; r = (lsb << (w−1)) OR (x >> 1) |
| RolC | 416 | unário: r = (x·2) OR carry; carry = msb antigo |
| RorC | 417 | unário: r = (carry << (w−1)) OR (x >> 1); carry = lsb antigo |

- O carry (`motor+0xf68`) é estado do **motor**, não do número: sobrevive a um número novo e só é zerado pelo C.
- O deslocamento n é o operando direito já truncado. Um n negativo, digitado como `1 ±`, vira 2^64 − 1 ≥ w e dá
  "Resultado não definido".

### 3.6 ÷ e Mod no modo inteiro (`DoOperation` 0x5b / 0x5f) [O]

1. Para cada operando com o bit w−1 ligado: magnitude = (x XOR máscara) + 1, e o sinal é guardado.
2. ÷: divrat das magnitudes. Se os sinais diferem, o resultado é −int(q), senão fica q, que o DisplayNum trunca. Logo o
   quociente é **truncado** (−7 ÷ 2 = −3). Divisor 0: "Não é possível dividir por zero"; 0 ÷ 0: "Resultado indefinido" (divrat, 02a §4).
3. Mod: rem das magnitudes (0x18013ab80). **Divisor 0 lança 0x80000002 → "Resultado indefinido"** (no Científico, `5 mod 0 = 5`).
   Se o dividendo era negativo, o resto é negado. Logo o sinal é o **do dividendo**: −7 % 3 = −1, 7 % −3 = 1 (no Científico,
   2 e −2).

### 3.7 Teclado de bits (`FUN_18012d520`) [O]

- `pos < largura`: valor = int(valor) XOR 2^pos (2^pos por powrat(2, pos)); senão nada. Depois vem `DisplayNum`.
- Antes disso, em ProcessCommand: se o último comando foi um operador binário (0x56–0x61 ou 500–505), **atual = acumulador**,
  a mesma regra das unárias (02a §3.5). O operador pendente não é apagado. Então `5 + [bit0] =` → atual = 5 XOR 1 = 4 → 5 + 4 = **9**.
- Um dígito depois do bit começa um número novo (bloco de dígito com `motor+0x21 = 0`: comprimento zerado).
- O painel de bits da VM (`BinaryDigits`) lê o texto binário sem agrupamento, do bit 0 em diante.

## 4. Casos de borda

| # | Situação | Comportamento previsto | Base |
|---|---|---|---|
| P1 | 2^63−1 + 1 (QWORD) | −9.223.372.036.854.775.808 (sem erro) | O |
| P2 | digitar o 17º dígito HEX / 65º BIN | ignorado | O |
| P3 | OCT QWORD com 22 dígitos | aceito só se começar por `1` | O |
| P4 | DEC QWORD `…5808` | recusado se positivo, aceito se negativo | O |
| P5 | estreitar | bits baixos | O |
| P6 | alargar | estende o sinal | O |
| P7 | Lsh/Rsh/RshL por n ≥ largura | "Resultado não definido" | O |
| P8 | Rsh de negativo | arredonda para baixo (−7 Rsh 1 = −4); ÷2 trunca (−7 ÷ 2 = −3) | O |
| P9 | x Mod 0 | "Resultado indefinido" | O |
| P10 | Mod com negativos | sinal do dividendo | O |
| P11 | carry de RolC/RorC | persiste entre números; C zera | O |
| P12 | bit ou unária logo depois de operador | age sobre o acumulador | O |
| P13 | trocar a base em erro | Clear | O (I no vslot) |
| P14 | ciclo do botão de tamanho | Q→D→W→B→Q | **I** (L27) |

## 5. Lacunas desta fase

Novas em `04-lacunas.md`: L27 (handler C# do botão de tamanho, a opção de deslocamento selecionada no início e a reação dos
botões a uma opção nova: só o XAML foi lido), L28 (vslot 0x350 da VM = IsInError e vslot 0x470 = comando de tamanho, por
inferência).

## 6. Casos de teste

Em `relatorio/03d-casos-de-teste.md`, congelado por SHA-256 em `hashes-originais.txt` antes da execução.

## 7. Resultados da execução caixa-preta (2026-10-23)

**Ordem dos fatos** (horário local; mtime dos arquivos, carimbos internos do script e transcrição desta sessão):

| Horário | Etapa | O que leu da Calculadora |
|---|---|---|
| 01:20:12 | `prog3d.py` (previsões) | nada |
| 01:22:20 | `d-programador.md` §1–6 gravado | — |
| 01:24:18 | `03d-casos-de-teste.md` gravado | — |
| **01:24:49** | **SHA-256 `e24abc00…4955` anexado a `hashes-originais.txt`** | — |
| 01:25:24–01:25:33 | Arvore3d, 1ª tentativa: Alt+3 abriu "Representação gráfica" e a etapa abortou | só o Header |
| 01:25:39–01:25:48 | Arvore3d (Alt+4): árvore UIA do Programador, submenus | visor `0`, nomes e IDs |
| 01:26:07–01:26:18 | Arvore3d com o teclado de bits e 4 cliques no botão de tamanho | visor `0`; botão visível QWORD→DWORD→WORD→BYTE→QWORD |
| 01:28:36–01:28:42 | piloto (CASOS3D=3d-01) | 3d-01 (sobrescrito pela execução completa; valores iguais) |
| 01:28:48–01:37:36 | **Casos3d completo** (execução 1) | todos os casos |
| 01:38:11–01:38:20 | **3d-93 refeito** (execução 2), ver abaixo | só 3d-93 |

Antes de 01:24:49 nada foi executado no Windows nesta fase. SHA-256 instalados de `CalculatorApp.exe`, `CalculatorApp.dll` e
`CalcViewModel.dll` iguais aos de `./binarios` (`trabalho/automacao/log-execucao-3d-execucao1.txt`).

**Execução.** `trabalho/automacao/rodar-casos.ps1 -Etapa Casos3d` (UI Automation). Antes de cada caso: Programador (Alt+4),
submenus fechados, teclado completo, C até o visor dar `0`, base (SelectionItem no RadioButton), tamanho (cliques até o
botão visível ser o pedido), opção de deslocamento no submenu Bit-shift (verificando o Name dos botões que aparecem).
- Visor: `NormalOutput`. Linhas: `ContentPresenter` de `hexButton`/`decimalButton`/`octolButton`/`binaryButton`. Bits:
  ToggleState de `Bit0`…`Bit63`. Tudo por UIA, sem transcrição. Resultados: `relatorio/resultados-reais-3d.txt`.
- Expressão: das capturas `capturas/3d-*-final.png`, montadas em folhas. **19 das 26 expressões previstas foram transcritas
  manualmente** (o OCR junta tokens e lê `10` como `IO`), e as outras 7 o OCR leu igual (`transcricao-capturas-3d.tsv`).
- Desvios de execução, registrados aqui:
  1. Bloco F: com o teclado de bits ligado, C, dígitos e operadores saem da árvore. A automação alterna para o teclado
     completo para apertá-los e volta (passos `KB:FULL`/`KB:BITS` em `rodar-casos.ps1`). O 03d dizia "teclado de bits
     ligado" sem prever essa alternância.
  2. **3d-93, execução 1**: depois de `RolC` o botão visível era CE, então o passo `C` não foi executado ("botao
     clearButton ausente" no log) e o visor final deu `B`. A conta não foi a especificada, então a execução foi
     invalidada. A automação passou a apertar CE antes quando o C não está visível (como o preparo já fazia). Na
     **execução 2** (01:38:13) deu `0` → `A`, como previsto. As duas execuções estão guardadas
     (`resultados-reais-3d-execucao1/2.txt`, `log-execucao-3d-execucao1/2.txt`).
  3. O registro do caminho de cliques no botão de tamanho saiu vazio (a lista não foi preenchida). O sentido do ciclo está
     na Arvore3d (01:26) e é coerente com o resultado do 3d-23.

**Critério** fixado no 03d e implementado em `trabalho/automacao/comparar-3d.py`, que confere o hash. Teste negativo numa
cópia (visor de 3d-90 trocado, bit 3 de 3d-100 apagado, `=` tirado da expressão de 3d-50): *erro*, *erro*, *parcial*.

| ID | Bloco | Discr. | Classe | Divergências | Origem da expressão |
|---|---|---|---|---|---|
| 3d-01 | A | não | acerto | — | — |
| 3d-02 | A | não | erro | linha B '0011 1110 1000' (prevista '11 1110 1000') | — |
| 3d-03 | A | não | erro | linha B '0001 1010 0011' (prevista '1 1010 0011') | — |
| 3d-04 | A | não | acerto | — | — |
| 3d-05 | A | sim | acerto | — | — |
| 3d-06 | A | sim | acerto | — | — |
| 3d-07 | A | sim | acerto | — | — |
| 3d-08 | A | sim | acerto | — | — |
| 3d-09 | A | sim | acerto | — | — |
| 3d-10 | A | sim | acerto | — | — |
| 3d-11 | A | não | acerto | — | — |
| 3d-12 | A | sim | acerto | — | — |
| 3d-13 | A | sim | acerto | — | — |
| 3d-14 | A | sim | acerto | — | — |
| 3d-20 | B | sim | acerto | — | — |
| 3d-21 | B | sim | acerto | — | — |
| 3d-22 | B | sim | acerto | — | — |
| 3d-23 | B | sim | acerto | — | — |
| 3d-24 | B | sim | acerto | — | — |
| 3d-25 | B | sim | acerto | — | — |
| 3d-26 | B | sim | acerto | — | — |
| 3d-30 | C | não | acerto | — | — |
| 3d-31 | C | não | acerto | — | — |
| 3d-32 | C | sim | acerto | — | — |
| 3d-33 | C | sim | acerto | — | ocr |
| 3d-34 | C | sim | acerto | — | ocr |
| 3d-35 | C | sim | acerto | — | — |
| 3d-36 | C | sim | acerto | — | — |
| 3d-37 | C | sim | acerto | — | manual |
| 3d-38 | C | sim | acerto | — | — |
| 3d-39 | C | sim | acerto | — | — |
| 3d-40 | C | sim | acerto | — | manual |
| 3d-41 | C | sim | acerto | — | manual |
| 3d-42 | C | sim | acerto | — | manual |
| 3d-43 | C | não | acerto | — | manual |
| 3d-44 | C | não | acerto | — | — |
| 3d-45 | C | não | acerto | — | — |
| 3d-46 | C | não | acerto | — | — |
| 3d-47 | C | não | acerto | — | — |
| 3d-48 | C | não | acerto | — | manual |
| 3d-50 | D | não | acerto | — | manual |
| 3d-51 | D | não | acerto | — | manual |
| 3d-52 | D | não | acerto | — | manual |
| 3d-53 | D | não | acerto | — | manual |
| 3d-54 | D | não | acerto | — | manual |
| 3d-55 | D | não | acerto | — | ocr |
| 3d-56 | D | sim | acerto | — | ocr |
| 3d-57 | D | sim | acerto | — | — |
| 3d-58 | D | sim | acerto | — | manual |
| 3d-59 | D | sim | acerto | — | manual |
| 3d-60 | D | sim | acerto | — | manual |
| 3d-61 | D | sim | acerto | — | ocr |
| 3d-62 | D | não | acerto | — | ocr |
| 3d-70 | E | não | acerto | — | manual |
| 3d-71 | E | sim | acerto | — | — |
| 3d-72 | E | sim | acerto | — | — |
| 3d-73 | E | sim | acerto | — | manual |
| 3d-74 | E | não | acerto | — | — |
| 3d-75 | E | sim | acerto | — | — |
| 3d-76 | E | sim | acerto | — | — |
| 3d-77 | E | sim | acerto | — | — |
| 3d-78 | E | sim | acerto | — | — |
| 3d-79 | E | sim | acerto | — | ocr |
| 3d-80 | E | sim | acerto | — | — |
| 3d-81 | E | sim | acerto | — | manual |
| 3d-82 | E | sim | acerto | — | — |
| 3d-83 | E | não | acerto | — | — |
| 3d-84 | E | sim | acerto | — | — |
| 3d-85 | E | sim | acerto | — | — |
| 3d-86 | E | sim | acerto | — | manual |
| 3d-87 | E | não | acerto | — | manual |
| 3d-88 | E | sim | acerto | — | — |
| 3d-89 | E | não | acerto | — | — |
| 3d-90 | E | sim | acerto | — | — |
| 3d-91 | E | sim | acerto | — | — |
| 3d-92 | E | sim | acerto | — | — |
| 3d-93 | E | não | acerto | — | — |
| 3d-100 | F | não | acerto | — | — |
| 3d-101 | F | sim | acerto | — | — |
| 3d-102 | F | sim | acerto | — | — |
| 3d-103 | F | não | acerto | — | — |
| 3d-104 | F | sim | acerto | — | — |
| 3d-105 | F | sim | acerto | — | — |
| 3d-106 | F | sim | acerto | — | — |
| 3d-107 | F | não | acerto | — | — |

**Taxa de acerto por bloco.**

| Bloco | Casos | Acerto | Parcial | Erro | Taxa (acerto/casos) |
|---|---:|---:|---:|---:|---:|
| A | 14 | 12 | 0 | 2 | 86% |
| B | 7 | 7 | 0 | 0 | 100% |
| C | 19 | 19 | 0 | 0 | 100% |
| D | 13 | 13 | 0 | 0 | 100% |
| E | 24 | 24 | 0 | 0 | 100% |
| F | 8 | 8 | 0 | 0 | 100% |
| Total | 85 | 83 | 0 | 2 | 98% |
| Discr. | 56 | 56 | 0 | 0 | 100% |

**Divergências e investigação.**
- **3d-02 e 3d-03 (linha BIN do painel)**: veio `0011 1110 1000` e `0001 1010 0011` (zeros à esquerda até um múltiplo de 4). O
  visor e as outras linhas conferem. Causa no binário [O]: `FUN_1800d9b20` (painel da VM) passa o texto binário por
  `FUN_1800d98a0`, que, se o texto não é `"0"` (`DAT_1801880a8`), conta os caracteres ≠ espaço (`FUN_180141940(…, 0x20)`)
  e acrescenta `(4 − n mod 4) mod 4` zeros (`FUN_1800468a0(…, 0x30, k)`) antes de copiar. A previsão errou por não ler
  essa chamada, já presente no pseudocódigo usado. O motor está certo, e a camada VM acrescenta o preenchimento. Os outros
  casos com linha B prevista (3d-01, 3d-30) tinham múltiplo de 4 dígitos e por isso passaram. §3.1 corrigida (com marca).

**Inferências confirmadas.**
- d§3.2 / L27: o botão de tamanho cicla QWORD→DWORD→WORD→BYTE→QWORD (Arvore3d), e o 3d-23 deu −2.147.483.648 (pelo
  caminho inverso daria 0). A troca **estende o sinal** ao alargar (3d-21, 3d-22, 3d-25).
- d§3.2 / L28: trocar a base em erro zera a calculadora (3d-47), coerente com vslot 0x350 = IsInError.
- d§3.6: Mod com o sinal do dividendo e `x Mod 0` = "Resultado indefinido", diferente do Científico (3c-16/17/19). Isso
  confirma também o sentido de `remnum` (L24) por um segundo caminho.
- d§3.5: carry do motor persiste entre números (3d-92) e C o zera (3d-93).
- d§3.3: todos os limites de digitação (HEX 16, BIN 64, OCT 22 só com `1`, DEC com sinal, BYTE `12`/`20`).

**Casos discriminantes (MP ≠ motor).** 56 dos 85 casos foram marcados **Discr. = sim** no 03d **antes** da execução. Os 56
deram *acerto*. Nenhum dos dois erros está entre eles: os dois são de formatação da VM em casos sem discriminação.
