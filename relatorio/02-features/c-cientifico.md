# 02c — Modo científico (Fase 3c)

Alvo: `CalcViewModel.dll` (SHA-256 `072cd589…d21d`), 11.2607.0.0 x64. Análise estática com REA 6.7.0 / Ghidra 12.1.4,
sessão reaberta do snapshot da Fase 1. Data: 2026-10-22.

Convenção: **[O]** OBSERVADO (pseudocódigo, assembly ou bytes, com endereço); **[I]** INFERIDO (com o raciocínio).
`motor+0xNNN` é um offset no objeto da engine (0x11a8 bytes). Nomes como `sinrat` são **rótulos** desta análise (L1).

Evidência REA: `trabalho/fase3c-evidencias.json` (22 registros, 0 unknowns). Pseudocódigo novo em
`trabalho/pseudocodigo/<endereço>.c` (34 funções, marcadas "Fase 3c" em `INDICE.tsv`). Leituras de bytes/assembly feitas
com `objdump` e `pe_va.py` sobre o binário original, gravadas em `trabalho/fase3c/l11-tabela-salto.txt` e
`trabalho/fase3c/cis-chamadores-to_wstring.txt`. Previsões numéricas: `trabalho/scripts/visor3c.py`.

## Resumo

| Pergunta | Resposta curta |
|---|---|
| Ponto de entrada | igual ao Padrão: `OnButtonPressed` 0x1800d5aa0 → `CalculatorManager::SendCommand` 0x18010d3d0 → `ProcessCommand` 0x180112db0 da engine científica (`CalculatorManager+0x18`, precedência ligada, precisão 32) [O] |
| Unárias científicas | `ProcessCommand` (faixa 0x62–0x76, 400–417, 0x144) → `SciCalcFunctions` 0x1801286f0 → wrappers 0x18012dxxx/0x18012exxx → rotinas racionais 0x18013xxxx [O] |
| Inversas (2nd) | a VM manda o código da inversa (202…); o `CalculatorManager` traduz para **INV (146) + função direta**; a engine liga `motor+0xe21` e o desliga depois da função [O] |
| Ângulo | `motor+0xf4c` = 0 DEG / 1 RAD / 2 GRAD, só gravado pelos comandos 321–323; trocar o ângulo **finaliza o número em digitação** [O] |
| sen/cos/tan | redução (mod 360 / mod 2π / mod 400), conversão para radianos com π de 41 dígitos, série de Taylor; resultado com \|y\| ≤ 10⁻³² vira **0 exato**; tan = sen/cos e **cos == 0 → "Entrada inválida"** [O] |
| Domínio trig | só `x < 10¹⁰⁰` é aceito (comparação **sem módulo**: −10¹⁰⁰ passa) [O] |
| log, ln, eˣ, 10ˣ, xʸ, ʸ√x, logᵧx | ln com x ≤ 0 → "Entrada inválida"; log = ln(x)/ln 10; eˣ = INV+ln; 10ˣ = 10^x; ʸ√x = x^(1/y); logᵧx = ln x / ln y [O] |
| n! | > 3249 ou < −1000 → "Estouro"; inteiro negativo → "Entrada inválida"; não inteiro → função gama [O] |
| mod | resto com o **sinal do divisor** (forma "floor"); `x mod 0 = x` [O no código; I no sinal do resto interno] |
| Precedência | 5 níveis (Or/Xor 0, And/Nand/Nor 1, + − 2, × ÷ Mod Lsh Rsh 3, ^ yroot logᵧx 4), **associativa à esquerda** (2^3^2 = 64), pilha de 25 [O] |
| Parênteses | até 25; `=` fecha os abertos; `(` depois de número/`)` insere × de verdade; **número depois de `)` insere × que descarta o operador pendente anterior** [O] |
| L11 | tabela 0x18011666c decodificada: é a precedência do operador novo, usada para pôr parênteses na expressão quando se troca o operador (`2 + 3 + ×` → `(2 + 3) ×`) [O] |
| "cis" (chave 23) | **nenhum caminho alcançável** o mostra: o fallback só ocorre com modo de ângulo fora de {0,1,2}, que nunca acontece [O] |

## 1. Cadeia de chamadas

```
XAML Views/CalculatorScientificOperators.xbf (botões CalculatorButton, ButtonId = membro de NumbersAndOperatorsEnum) [O, 01 §7.3]
  Trigonometria (trigButton → Trigflyout): sin/cos/tan (102–104), com "2nd" (trigShiftButton) InvSin/InvCos/InvTan (202–204),
     com "hyp" (hypShiftButton) Sinh… e sec/csc/cot (400–411)
  Funções (funcButton): Abs 413, Floor 414, Ceil 415, Rand 600, DMS 115, Degrees 324
  Painel: XPower2 111, Sqrt 110, XPowerY 97, TenPowerX 117, LogBase10 109, LogBaseE 108, Invert 114, Abs 413, Exp 127,
     Mod 95, ( 128, ) 129, Factorial 113, Pi 120, Euler 601; com "2nd" (shiftButton): Cube 112, CubeRoot 116,
     YRootX 96, TwoPowerX 412, LogBaseY 500, EPowerX 205
  Ângulo (CalculatorScientificAngleButtons.xbf): degButton/radButton/gradButton (CommandParameter 0/1/2); FtoeButton = FToE 119
 └► VM OnButtonPressed 0x1800d5aa0                                                       [O, 01 §6.3]
     ├ 321–323: grava VM+0x148; FToE chega por FtoEButtonToggled 0x1800d5520 → OnButtonPressed(119)   [O]
     ├ C/CE: IsFToEChecked = false (set_IsFToEChecked 0x1800d0c40 só muda a propriedade)  [O]
     └► CalculatorManager::SendCommand 0x18010d3d0
         ├ 202/203/204 → 146 + 102/103/104; 205 (eˣ) → 146 + 108; 206–208 → 146 + 105–107;
         │  401/403/…/411 → 146 + (n−1)                                                   [O, 01 §6.4]
         ├ 321–323 → CalculatorManager+0x9c e repassa; 119 → alterna +0x98 e repassa       [O]
         └► engine::ProcessCommand 0x180112db0 (engine científica: a=1 precedência, precisão 32)
              ├ 0x92 (146) INV: motor+0xe21 = !motor+0xe21                                 [O]
              ├ 0x141–0x143: motor+0xf4c = cmd − 0x141                                      [O]
              ├ unárias 0x62–0x76, 400–417, 0x144:
              │    token na expressão FUN_18010f200(op, INV, ângulo) → texto FUN_1801168e0  [O]
              │    domínio trig: motor+0x120 < motor+0x98 (=10¹⁰⁰) senão DisplayError(0x80000001) [O]
              │    SciCalcFunctions 0x1801286f0 (try/catch → DisplayError)                 [O, 02a §4.1]
              │    INV é desligado depois de Int/sin…ln/DMS/Degrees/sec…coth               [O]
              ├ binárias 0x56–0x61, 500–505 → precedência (§3.11) → DoOperation 0x180131140 [O]
              ├ 0x80/0x81 parênteses (§3.12), 0x79 = (§3.12), 0x7f Exp (§3.8), 0x77 F-E (§3.9)
              └ 0x78 π / 0x259 e: valor = constante global (DAT_1802053e0 / DAT_1802053d8)  [O]
```

## 2. Estruturas de dados [O]

Engine (complementa 02a §2):

| Offset | Conteúdo | Evidência |
|---|---|---|
| +0x00 | precedência ligada (Científico = 1) | 02a §2, 0x180112db0 |
| +0x90 | formato: 0 flutuante, 1 científico (F-E) | `case 0x77` |
| +0x98 | **limite trig = 10¹⁰⁰** (`pow(10, 100)` no construtor) | 0x180111bd0 (`FUN_180126760(100)`, `(10)`, `FUN_18012da60`) |
| +0x120 / +0x160 | valor atual / acumulador | 02a |
| +0x1a0 + 0x40·n / +0xe78 + 4·n | pilha de parênteses: acumulador e operador pendente salvos por `(` | `case 0x80` |
| +0x7e0 + 0x40·n / +0xedc + 4·n / +0xf40 | pilha de precedência (25); `(` empilha um **marcador 0** | `case 0x80`, binário |
| +0xe21 | INV | `case 0x92` |
| +0xe70 | profundidade de parênteses (máx. 25) | `case 0x80/0x81` |
| +0xf4c | ângulo 0/1/2; o construtor zera (+0xf48 é zerado como qword) | 0x180111bd0 linha `*(param_1+0xf48)=0` |
| +0x1c | operador do último cálculo feito (para parênteses na expressão, §3.11) | binário, linha `+0x1c = +0x18` |

Constantes globais do "ratpak" (init 0x180121ec0(base, precisão), chamado com precisão 32 ao entrar no Científico):

| Global | Valor | Como é feito |
|---|---|---|
| DAT_1802053e0 | π | `asin(1/2)·6` com precisão 9 + 32 = 41 dígitos (`FUN_180134e90`, `DAT_1802054fc` = ⌈31/log₂10⌉ − 1 = 9) |
| DAT_1802053e8 / DAT_180205498 | 2π / π/2 | π + π, π ÷ 2 |
| DAT_1802053d8 | e | `exp(1)` (`FUN_1801363d0`) |
| DAT_1802054e8 | ln 10 | `FUN_180137490(10)` |
| DAT_180205430/460/468/458 | 360 / 180 / 400 / 200 | `FUN_18012f780` |
| DAT_180205408 / DAT_180205400 | +10⁻³² / −10⁻³² ("menor valor") | `FUN_180130b50(base, −precisão)`; cópia com sinal −1 |
| DAT_180205428 / DAT_180205420 | 3249 / −1000 (limites do fatorial) | `FUN_18012f780(0xcb1)`, `(0xfffffc18)` |

- [O] As constantes π, e, ln 10 só são **recalculadas se a precisão aumentar** (`DAT_1801ec944 < base·9·precisão`); o
  limiar ±10⁻³² é refeito sempre (ramo `else` → `FUN_180124d40` e cópia de DAT_180205408). [I] Depois de usar o
  Programador (precisão 64), π fica com 73 dígitos; isso não muda nenhum valor exibido com 32 dígitos.
- Comparações racionais [O] (todas fazem a − b e olham o sinal): `FUN_180124240` a < b; `FUN_1801240e0` a ≤ b;
  `FUN_180123e20` a ≥ b; `FUN_180123f80` a > b; `FUN_180123cd0` a = b.

## 3. Regras

### 3.1 sen, cos, tan [O]

`SciCalcFunctions` 0x66/0x67/0x68 → `FUN_18012df50`/`dff0`/`e090`(x, ângulo = motor+0xf4c) → `FUN_18013df50`/`e820`/`ecd0`:

1. **DEG**: x = x mod 360 (`FUN_1801244f0`: x − int(x/360)·360, `int` = truncamento [I pelo nome]); se x > 180, x = x − 360;
   x = x / 180 · π. **GRAD**: o mesmo com 400 / 200. **RAD**: x = x mod 2π (`FUN_180124680`, 2π recalculado com precisão
   ≥ 128).
2. Série de Taylor (`FUN_18013d7c0` seno, `FUN_18013e090` cosseno) até o termo ficar abaixo de ~10⁻¹²⁸ (precisão 0x80).
3. Depois da série: `FUN_1801265d0` (corte de precisão), `FUN_180124ad0` (limita a [−1, 1]) e **se −10⁻³² ≤ y ≤ 10⁻³², y = 0
   exato** (`FUN_1801240e0(y, DAT_180205408)` e `FUN_180123e20(y, DAT_180205400)` → cópia de DAT_1802054d8 = 0).
4. tan (`FUN_18013eb50`) = sen/cos, ambos com o passo 3; **se o cosseno tem todos os dígitos zero, lança 0x80000001**
   ("Entrada inválida").
5. Antes de tudo, `ProcessCommand` exige `x < 10¹⁰⁰` (`FUN_180127d90(motor+0x120, motor+0x98)`) para sin…tanh e
   sec…coth; senão zera o valor e chama `DisplayError(0x80000001)`. A comparação é **com sinal**: −10¹⁰⁰ passa e é
   reduzido normalmente (assimetria).

Consequências:
- π tem erro ~10⁻⁴¹; cos(90°) = cos(π̃/2) ≈ 10⁻⁴¹ → **0**; tan 90° → **"Entrada inválida"**; sen 180° → **0**;
  sen π em RAD → **0** (o π da tecla é o mesmo global) [O na regra; I na ordem de grandeza do erro de π̃, que tem folga
  de ~9 ordens].
- sen 30° = sen(π̃/6) = 0,4999…(≈40 noves)… → arredondado para 32 dígitos → **0,5** [O na regra de exibição, §3.13; I no erro].
- −10¹⁰⁰ mod 360 = −280 (10¹⁰⁰ ≡ 280 mod 360) → sen(−280°) = sen 80° [O no código; aritmética feita à mão].

### 3.2 Inversas (2nd) [O]

`FUN_18012e130` (asen), `e270` (acos), `e3a0` (atan): função em radianos e depois, em DEG, `÷ 2π × 360`; em GRAD,
`÷ 2π × 400`. `asinrat` 0x180134e90: trabalha com |x|; se ||x| − 1| ≤ 10⁻³², devolve **π/2 exato** (DAT_180205498);
se |x| > 1 (além de 10⁻³²), lança 0x80000001. Logo **asen 1 (DEG) = (π/2)/(2π)·360 = 90** e **asen 2 = "Entrada
inválida"**. Texto na expressão: chaves 70–72 / 76–78 / 82–84 (`sin₀⁻¹`, `cosᵣ⁻¹`, `tan₉⁻¹`…).

### 3.3 ln, log, eˣ, 10ˣ [O]

- ln (108): `FUN_18012dcf0` → `FUN_1801378d0` → `lnrat` 0x180137490: **x ≤ 0 → 0x80000001**. Com INV (eˣ, 205): `FUN_18012dc40` →
  `FUN_180136870` (exp).
- log (109): `FUN_18012dd90` = ln(x) ÷ DAT_1802054e8 (ln 10). log 1000 = ln 1000 / ln 10 → 3 só depois do arredondamento [O na regra].
- 10ˣ (117): `pow(10, x)` (`FUN_18012da60` → powrat 0x180137b70). Expoente inteiro: caminho de potência inteira
  (`FUN_180130b50`), resultado exato [O: `FUN_18012f930` + `FUN_180130b50` em 0x1801387e0].

### 3.4 xʸ, ʸ√x, logᵧx (binários, `DoOperation` 0x180131140) [O]

- `x ^ y` (97 = 0x61): powrat(x, y). `x yroot y` (96 = 0x60): powrat(x, 1/y) (`FUN_18012de90` = 1 ÷ y).
  `x logᵧx y` (500): ln(x) ÷ ln(y).
- powrat: base 0 ou expoente 0 vão para o caminho geral; caminho geral = |x| → ln → × y → exp, com teste de base
  negativa (só denominador ímpar do expoente é aceito, 02a §4.2) [O na estrutura; I no detalhe do sinal de raiz ímpar].
  0 elevado a negativo → ln(0) → "Entrada inválida" (qualquer dos dois ramos lança 0x80000001).
- Texto: `^` (chave 17), `yroot` (16), `log base` (`LogBaseY`).

### 3.5 n! (113) [O, `FUN_18012db70` → 0x18013d030]

1. x > 3249 ou x < −1000 → 0x80000008 → **"Estouro"**.
2. Parte fracionária zero (ou < 10⁻¹²⁸): se x < 0 → 0x80000001 **"Entrada inválida"**; senão produto x·(x−1)···1 (0! = 1).
3. Não inteiro: multiplica enquanto x > 0, depois aplica `FUN_18013b1b0` ao resto em (0, 1] → [I] Γ; 0,5! = 0,5·Γ(0,5) = Γ(1,5).
- Texto: `fact` (94).

### 3.6 mod (95, binário, precedência 3) [O no código; I no sinal]

`FUN_18012e890` → `FUN_18013ad40(x, y)`:
- **y = 0 → devolve x inalterado** (`5 mod 0 = 5`).
- resto = `remnum(x·den_y, y·den_x)` sobre den_x·den_y (`FUN_1801398f0`, `FUN_180140d10`); se x e y têm sinais
  diferentes e o resto ≠ 0, resto = resto + y. [I] Assumindo que `remnum` mantém o sinal do dividendo (não lido),
  o resultado tem o sinal do divisor: −7 mod 3 = 2, 7 mod −3 = −2. 7,5 mod 2 = 1,5 (racional exato).
- Texto: `Mod` (chave 15).

### 3.7 |x| (413) [O]

`case 0x19d`: copia o valor com o sinal do numerador e do denominador = +1. Texto `abs`.

### 3.8 Exp (127 = 0x7f) [O]

- Só age **digitando** (motor+0x21) e fora do modo inteiro: chama o separador decimal (`FUN_180121900`, sem efeito se já
  existe) e liga o modo expoente (motor+0x28). Exp não finaliza o número (fica fora das faixas de finalização no topo
  de `ProcessCommand`). Fora da digitação é ignorado.
- Texto do visor durante a digitação (`FUN_180121ad0`): `[-]mantissa` + separador (se ainda não houver) + `e` + `+`/`-` +
  expoente (ou `0`). `2 exp` → `2,e+0`; `3` → `2,e+3`. ± no modo expoente troca o **sinal do expoente** (motor+0x88);
  antes do Exp troca o da mantissa (motor+0x60). Expoente com no máximo 4 dígitos (02a §3.1).

### 3.9 F-E (119 = 0x77) [O]

Alterna motor+0x90 e chama DisplayNum. Como 0x77 está na faixa que **finaliza** a digitação, `123 F-E` já formata.
Com formato científico, todo número sai em `d,ddd…e±N` com até 32 dígitos (§3.13); o 0 sai `0,e+0` [O no código, não
testado]. Na VM, C/CE desligam só a **propriedade** IsFToEChecked (0x1800d0c40) sem mandar 119; o que o C# faz com o
ToggleButton nesse momento não foi lido (L3) — por isso os casos de F-E terminam com F-E desligado.

### 3.10 π e e [O]

`case 0x78`: valor = DAT_1802053e0 (com INV, DAT_1802053e8 = 2π); `case 0x259`: DAT_1802053d8. Não geram token: a
função seguinte usa o **texto do visor** como operando (`FUN_180110560`), então a expressão mostra os 32 dígitos.

### 3.11 Precedência e troca de operador [O]

- `FUN_180112b30` e os `switch` repetidos em 0x180112db0: Or/Xor 0; And/Nand/Nor 1; + − 2; × ÷ Mod Lsh Rsh RshL 3;
  yroot ^ logᵧx 4.
- Operador novo `op` com pendente `p`: se `prec(op) ≤ prec(p)` avalia `p` (associativa à esquerda); senão empilha (acumulador, p)
  (máx. 25). Ao avaliar, `+0x1c = p`, desempilha o topo (se não for o marcador 0 de `(`) e volta ao teste (laço em
  LAB_180115d71): avalia de novo enquanto `prec(op) ≤ prec(topo)`. `=` avalia o pendente e desempilha tudo.
- powrat (0x180137b70 → 0x180137c30): separa o expoente em numerador e denominador; potência inteira exata pelo
  numerador (`FUN_1801387e0` → `FUN_180130b50`) e raiz pelo denominador [O na estrutura; I para expoente inteiro negativo
  = inverso exato].
- Exemplos: `2 × 3 + 4 × 5 =` → 6 ao apertar `+`, final 26; `2 ^ 3 ^ 2 =` → 8 ao apertar o segundo `^`, final **64**;
  `2 + 3 × 4 ^ 2 =` → 50; `7 mod 4 × 2 =` → 6.
- **L11 resolvida.** Troca de operador (operador logo após operador) no Científico com `+0x1c ≠ 0`: a tabela
  0x18011663c dá `prec(+0x1c)` e a tabela 0x18011666c dá `prec(novo)` (alvos decodificados em
  `trabalho/fase3c/l11-tabela-salto.txt`: And→1, Or/Xor→0, Lsh/Rsh/÷/×/Mod→3, +/−→2, yroot/^→4). Se
  `prec(substituído) ≤ prec(+0x1c) < prec(novo)`, zera +0x1c, remove o token do operador (`FUN_18010ff50`) e chama
  `FUN_18010f090`, que **insere `(` no início do trecho e `)` no fim** (chaves 48/49), e então acrescenta o operador
  novo. O valor não muda. Ex.: `2 + 3 +` (avalia 5, +0x1c = +) e `×` → expressão `(2 + 3) ×`; `4 =` → 20.

### 3.12 Parênteses e `=` [O]

- `(` (0x80), com profundidade < 25: se o último comando foi dígito, separador, unária ou `)`, primeiro executa um **×
  real** (`FUN_180112d90(motor, 0x5c)`, com precedência). Depois salva (acumulador, operador pendente) na pilha de
  parênteses, empilha um marcador 0 na pilha de precedência, zera acumulador e pendente; `ICalcDisplay` slot 3 = profundidade.
  - **[Correção pós-diferencial, 2026-10-23] Códigos exatos do × implícito [O]** (`trabalho/pseudocodigo/0x180112db0.c`
    l. 2024): último comando `motor+0xf48` ∈ dígitos 0x82–0x91, unárias 0x62–0x76 e 400–417, separador 0x54 ou `)` 0x81.
    **`±` (0x50) não está**, nem Degrees (0x144). Exemplo observado (dif-Pr-055, DEC BYTE): `Or 5 ± ( And + =` → −10;
    com o × implícito daria 50. Antes, "unária" ficou sem lista de códigos. A reimplementação incluiu o `±` (conjunto de "último comando unário" do histórico, 02b §4.1),
    e isso causou dif-Pr-013, dif-Pr-055 e dif-Ci-062 (`relatorio/03-diferencial-resultados.md`, B2).
  - **[Correção pós-diferencial, 2026-10-23] Número corrente zerado [O]** (l. 2092–2103): se o último comando foi um
    **operador binário** (0x56–0x61 ou 500–505), o `(` também grava 0 em `motor+0x120`, o número corrente. Por isso
    `x × ( =` dá 0 e `x ÷ ( =` dá "Não é possível dividir por zero". Depois de dígito, unária ou `)`, o número corrente
    não é zerado. O trecho já estava no pseudocódigo lido na 3c, mas não foi descrito. Causou dif-Ci-031, dif-Pr-072,
    dif-Pr-089 e dif-Pr-096 (B1).
  - **[Correção pós-diferencial, 2026-10-23] Operador salvo [O]** (l. 2067–2073 e 2306–2312): o `(` salva
    `+0x18` (operador) **só se `+0x20` = 1** (há operador pendente); senão salva 0. O `)` restaura `+0x18` com esse
    valor e faz `+0x20 = (op ≠ 0)`. Consequência: depois de `a op b =` (que deixa `+0x18` = op para o `=` repetido),
    um `(`…`)` apaga o operador da repetição, e o `=` seguinte só reexibe. "Salva (acumulador, operador pendente)",
    escrito acima, não dizia isso. Achado ao rodar a reimplementação corrigida: era a segunda causa de dif-Pr-013
    (B3), além do `±` antes de `(`.
- `)` (0x81) sem `(` aberto: só `ICalcDisplay` slot 4 (anúncio "nenhum parêntese direito adicionado"); o valor e o
  pendente não mudam.
- `)` com `(` aberto: avalia o pendente e desempilha até o marcador; restaura acumulador e operador salvos; token `)`.
- `=` (0x79): **fecha todos os parênteses abertos** (envia 0x81 enquanto profundidade > 0 e sem erro), depois o fluxo da 3a.
  `( 2 + 3 =` → 5; `2 × ( 3 + ( 4 − 1 =` → 12.
- **Dígito ou separador logo após `)`**: põe `×` como pendente e o resultado do parêntese como acumulador **sem empilhar
  nem avaliar o pendente anterior**; também zera a pilha de precedência (bloco `if (+0xf48 == 0x81)` no ramo de dígito).
  Logo `1 + ( 2 + 3 ) 4 =` → **20** (o `1 +` se perde), enquanto `1 + ( 2 + 3 ) × 4 =` → 21.

### 3.13 Formato do visor com precisão 32 [O em `NumberToString` 0x1801300f0 + `FUN_180130060`]

1. Converte para decimal e **trunca** para 34 dígitos (`FUN_180130060(n, P+2)`, que também apaga zeros à direita).
2. e = nº de dígitos inteiros. Se e > 32: científica. Se a parte fracionária passa de 32 casas: com e < −2 (|x| < 0,001)
   científica; com −2 ≤ e ≤ 0 o arredondamento vai para a casa 32 **depois da vírgula** (31 dígitos significativos se
   e = −1, 30 se e = −2).
3. Arredonda somando meia unidade (sinal do número) e, se apareceram zeros à direita, reformata (recursão).
4. Científica: `d,` + resto + `e` + sinal + expoente (`1,e+32`: o separador fica). Separador final removido; milhar só na parte
   inteira fora da científica (02a §5).

Exemplos (`trabalho/scripts/visor3c.py`): 1/3 → `0,33333333333333333333333333333333`; 2/30 →
`0,06666666666666666666666666666667`; 1/300 → `0,00333333333333333333333333333333`; 1/3000 →
`3,3333333333333333333333333333333e-4`; 10³¹ → `10.000.000.000.000.000.000.000.000.000.000`; 10³² → `1,e+32`.

## 4. Linha de expressão [O nos tokens; I na renderização, L15]

- Unária: `prefixo(` + operando + `)` (como `√( 9 )` na 3a). Prefixo de `FUN_1801168e0`(op, INV, ângulo): mapa de exceções
  por op; para sin/cos/tan há 6 variantes (normal/inversa × DEG/RAD/GRAD): `sin₀`, `cos₀`, `tan₀`, `sinᵣ`…`tan₉⁻¹`
  (chaves 67–84). Outros: `ln` (28), `e^` (88), `log` (29), `10^` (37), `fact` (94), `abs`.
- Binárias: ` Mod `, ` ^ `, ` yroot `, ` log base `. Parênteses `(` `)`. O operando é o texto do visor sem agrupamento (3a-21).
- Erro numa unária: o token já foi gravado antes do cálculo, a expressão mostra `f( x )` (como 3a-08). Erro em `=`: a
  expressão fica como antes do `=` (como 3a-04).

## 5. O texto de reserva "cis" (`CEngineStrings/23`) [O]

Pergunta: existe algum caminho que mostre `cis`?

1. `cis` só sai por `mapa[to_wstring(103 − 80)]`. Os 23 chamadores de `to_wstring` 0x180094ca0 foram listados
   (`trabalho/fase3c/cis-chamadores-to_wstring.txt`): só três calculam `código − 0x50` — 0x180116b65 (`FUN_1801168e0`,
   unárias), 0x180116d84 (`FUN_180116bf0`, binárias: só recebe binários) e 0x1800d8fbb (VM, edição de token, só para os
   códigos da tabela 0x1801894a8 = 93, 94, 92, 91, 127, 96, 95, 97). Os demais usam constantes (0x26, 0x29, 0x30, 0x31),
   `código + 99` (erros), `dígito − 0x82` ou índices da VM/conversor.
2. Em `FUN_1801168e0`, Cos tem entrada no mapa com "depende do ângulo" ligado; o fallback só é usado se o ângulo não for
   0, 1 ou 2 (ramo `param_4 != 2 → LAB_180116b14`). Os chamadores são `FUN_18010f200` (0x18010f900), com ângulo =
   motor+0xf4c ∈ {0,1,2} (zerado no construtor, gravado só por 0x141–0x143), e a VM `FUN_1800d8b90` (0x1800d8ebe), com
   ângulo = `FUN_1800d8af0`(VM+0x214), que devolve 0/1/2 ou **lança** "Invalid command type".
3. As chaves 68, 71, 74, 77, 80, 83 existem no PRI (02a §7.1). Logo, **nenhum caminho mostra `cis`** com o binário como está.
   Os casos de cosseno em DEG, RAD e GRAD (3c-01, 3c-05, 3c-57, 3c-60) conferem isso em caixa-preta. L13 fica resolvida.

## 6. Casos de borda

| # | Situação | Comportamento previsto | Base |
|---|---|---|---|
| S1 | cos 90°, sen 180°, sen π (RAD) | 0 exato (corte de 10⁻³²) | O |
| S2 | tan 90° | "Entrada inválida" (cos = 0) | O |
| S3 | sen 30°, log 1000, ʸ√ de cubo perfeito | valor redondo só depois do arredondamento a 32 dígitos | O regra / I erro |
| S4 | trig de x ≥ 10¹⁰⁰ | "Entrada inválida"; −10¹⁰⁰ é aceito | O |
| S5 | asen/acos de \|x\| > 1 | "Entrada inválida"; \|x\| = 1 → π/2 exato | O |
| S6 | ln/log de x ≤ 0 | "Entrada inválida" | O |
| S7 | n! > 3249 / < −1000 | "Estouro"; inteiro negativo → "Entrada inválida"; não inteiro → Γ | O |
| S8 | x mod 0 | x | O |
| S9 | 2^3^2 | 64 (esquerda) | O |
| S10 | `=` com parênteses abertos | fecha todos | O |
| S11 | `)` sem `(` | ignorado (só anúncio) | O |
| S12 | número logo após `)` | × implícito que descarta o operador pendente anterior | O |
| S13 | `(` logo após número | × implícito com precedência normal | O |
| S14 | trocar DEG/RAD/GRAD digitando | finaliza o número: o próximo dígito começa outro | O |
| S15 | Exp fora da digitação | ignorado | O |
| S16 | 33º dígito | ignorado | O |
| S17 | 0 com F-E | `0,e+0` | O, não testado |

## 7. Lacunas desta fase

Em `relatorio/04-lacunas.md`: L11 e L13 resolvidas; novas L24 (sinal de `remnum` no mod e detalhe de powrat com base
negativa), L25 (o que o C# faz com o ToggleButton de F-E quando C o desliga), L26 (implementação de Γ em `FUN_18013b1b0`
e erro exato das séries, Fase 3f).

## 8. Casos de teste

Em `relatorio/03c-casos-de-teste.md`, congelado por SHA-256 em `hashes-originais.txt` antes da execução (20:12:52).

## 9. Resultados da execução caixa-preta (2026-10-22)

**Ordem dos fatos.** Previsões congeladas às 20:12:52 (SHA-256 `b31e6aee…d2e1` em `hashes-originais.txt`). Só depois:
levantamento da árvore UIA do modo Científico (`trabalho/automacao/arvore-uia-3c.txt`, 20:14:21); sonda de como fechar o
submenu Trigonometria (`sonda-3c.txt`); uma 1ª tentativa de teste abortada pelo preparo (o botão C some quando aparece CE, o
script passou a apertar o que estiver visível); teste com 3c-01 e 3c-59 (20:15:31, sobrescrito); execução completa
20:15:50–20:20:33. SHA-256 instalados de `CalculatorApp.exe`, `CalculatorApp.dll` e `CalcViewModel.dll` iguais aos de
`./binarios` (`trabalho/automacao/log-execucao-3c.txt`).

**Execução.** `trabalho/automacao/rodar-casos.ps1 -Etapa Casos3c` (UI Automation, PowerShell 5.1). Antes de cada caso:
modo Científica, submenu fechado, 2nd e 2nd do submenu desligados, F-E desligado, CE/C até o visor dar `0`, ângulo do caso.
Funções trigonométricas pelo submenu `Trigflyout` (fecha sozinho depois da função); ʸ√x, logᵧx e eˣ com `shiftButton`
ligado só durante o clique.
- Visor: `NormalOutput` (UIA RawView), sem transcrição. Resultados: `relatorio/resultados-reais-3c.txt`.
- Linha de expressão: lida das capturas `trabalho/automacao/capturas/3c-*.png`, montadas em folhas de faixas para leitura,
  em `trabalho/automacao/transcricao-capturas-3c.tsv`. **58 das 89 leituras foram transcritas manualmente** (o OCR do Windows
  não lê os subscritos ₀/ᵣ/₉ nem `^`/`×`); as 31 restantes o OCR leu igual. Os subscritos, pequenos na captura, foram
  conferidos com o texto do Narrador (`graus`/`radianos`/`grados`, `inversos`), e as 89 transcrições batem com ele.

**Critério** (fixado no arquivo congelado e implementado em `trabalho/automacao/comparar-3c.py`, que confere o hash).
O script foi validado com um teste negativo numa cópia dos resultados (um visor errado → *erro*; uma expressão
truncada → *parcial*; último dígito de 3c-55 trocado → *quase*).

| ID | Bloco | Classe | Divergências | Origem da expressão por leitura |
|---|---|---|---|---|
| 3c-01 | A | acerto | — | L1:manual |
| 3c-02 | A | acerto | — | L1:manual |
| 3c-03 | A | acerto | — | L1:manual |
| 3c-04 | A | acerto | — | L1:manual |
| 3c-05 | A | acerto | — | L1:manual |
| 3c-06 | A | acerto | — | L1:manual |
| 3c-07 | A | acerto | — | L1:manual |
| 3c-08 | A | acerto | — | L1:ocr L2:manual |
| 3c-09 | A | acerto | — | L1:ocr |
| 3c-10 | A | acerto | — | L1:ocr |
| 3c-11 | A | acerto | — | L1:ocr |
| 3c-12 | A | acerto | — | L1:manual |
| 3c-13 | A | acerto | — | L1:manual |
| 3c-14 | A | acerto | — | L1:manual |
| 3c-15 | A | acerto | — | L1:manual |
| 3c-16 | A | acerto | — | L1:ocr |
| 3c-17 | A | acerto | — | L1:ocr |
| 3c-18 | A | acerto | — | L1:ocr |
| 3c-19 | A | acerto | — | L1:manual |
| 3c-20 | A | acerto | — | L1:manual |
| 3c-21 | A | acerto | — | L1:manual |
| 3c-22 | A | acerto | — | L1:manual |
| 3c-23 | A | acerto | — | L1:manual |
| 3c-24 | A | acerto | — | L1:manual |
| 3c-25 | A | acerto | — | L1:manual |
| 3c-26 | A | acerto | — | L1:ocr |
| 3c-27 | A | acerto | — | L1:manual |
| 3c-28 | A | acerto | — | L1:ocr L2:ocr L3:ocr |
| 3c-29 | A | acerto | — | L1:ocr L2:ocr |
| 3c-30 | A | acerto | — | L1:ocr L2:ocr L3:ocr |
| 3c-31 | A | acerto | — | L1:ocr |
| 3c-32 | A | acerto | — | L1:manual |
| 3c-33 | A | acerto | — | L1:manual |
| 3c-34 | A | acerto | — | L1:manual |
| 3c-35 | A | acerto | — | L1:manual |
| 3c-36 | A | acerto | — | L1:ocr L2:ocr |
| 3c-37 | A | acerto | — | L1:manual L2:manual |
| 3c-38 | A | acerto | — | L1:manual L2:manual |
| 3c-39 | A | acerto | — | L1:manual |
| 3c-40 | A | acerto | — | L1:manual |
| 3c-41 | A | acerto | — | L1:manual L2:manual |
| 3c-42 | A | acerto | — | L1:ocr L2:manual |
| 3c-43 | A | acerto | — | L1:manual |
| 3c-44 | A | acerto | — | L1:manual |
| 3c-45 | A | acerto | — | L1:manual |
| 3c-46 | A | acerto | — | L1:ocr L2:manual L3:manual |
| 3c-47 | A | acerto | — | L1:manual |
| 3c-50 | B | acerto | — | L1:manual |
| 3c-51 | B | acerto | — | L1:manual |
| 3c-52 | B | acerto | — | L1:manual |
| 3c-53 | B | acerto | — | L1:manual |
| 3c-54 | B | acerto | — | L1:manual |
| 3c-55 | B | acerto | — | L1:manual |
| 3c-56 | B | acerto | — | L1:manual |
| 3c-57 | B | acerto | — | L1:manual |
| 3c-58 | B | acerto | — | L1:manual |
| 3c-59 | B | acerto | — | L1:manual |
| 3c-60 | B | acerto | — | L1:manual |
| 3c-61 | B | acerto | — | L1:manual |
| 3c-62 | B | acerto | — | L1:ocr L2:manual |
| 3c-63 | B | acerto | — | L1:ocr L2:ocr L3:ocr |
| 3c-64 | B | acerto | — | L1:ocr |
| 3c-65 | B | acerto | — | L1:manual |
| 3c-66 | B | acerto | — | L1:manual |
| 3c-67 | B | acerto | — | L1:manual |
| 3c-68 | B | acerto | — | L1:ocr |
| 3c-69 | B | acerto | — | L1:ocr |
| 3c-70 | B | acerto | — | L1:manual |
| 3c-71 | B | acerto | — | L1:manual |
| 3c-72 | B | acerto | — | L1:ocr |
| 3c-73 | B | acerto | — | L1:ocr |
| 3c-74 | B | acerto | — | L1:ocr |
| 3c-75 | B | acerto | — | L1:manual |

**Taxa de acerto por bloco.**

| Bloco | Casos | Acerto | Quase | Parcial | Erro | Taxa (acerto/casos) |
|---|---:|---:|---:|---:|---:|---:|
| A | 47 | 47 | 0 | 0 | 0 | 100% |
| B | 26 | 26 | 0 | 0 | 0 | 100% |
| Total | 73 | 73 | 0 | 0 | 0 | 100% |

Todas as 89 leituras de visor conferem exatamente, inclusive os 26 valores de 32 dígitos do bloco B (nenhum *quase*), e
todas as 64 expressões previstas conferem (sem espaços).

**Inferências confirmadas.**
- c§3.1: corte de |y| ≤ 10⁻³² (cos 90° = 0, sen 180° = 0, sen π RAD = 0) e tan 90° = "Entrada inválida"; erro do π e das
  séries menor que meia unidade na 32ª casa em todos os 26 casos do bloco B (valores redondos saíram redondos).
- c§3.1 (5): domínio trig assimétrico — `1 exp 100 sin` dá erro e `-1 exp 100 sin` dá sen(−280°) com os 32 dígitos previstos.
- c§3.6 / L24: o mod com negativos tem o sinal do divisor (−7 mod 3 = 2; 7 mod −3 = −2), e `5 mod 0 = 5`. Confirma o
  comportamento, não a leitura de `remnum` (L24 continua aberta quanto ao código).
- c§3.4: 2^−1 = 0,5 exato; −8 ʸ√ 3 = −2.
- c§3.5 / L26: 0,5! = Γ(1,5) com 32 dígitos corretos.
- c§3.11 (L11): `2 + 3 + ×` → `(2 + 3) ×`; 2^3^2 = 64.
- c§3.12: `=` fecha parênteses; × implícito antes de `(` com precedência; **× implícito depois de `)` descarta o `1 +`
  (3c-46 = 20, expressão `1 + (2 + 3) × 4 =` — a expressão mostra o `1 +`, o valor não o usa)**; `)` sem `(` é ignorado.
- c§1 / S14: trocar DEG→RAD durante a digitação finaliza o número (3c-09 = `2`, não `12`).
- c§3.13: regra de exibição com 31/30 significativos para e = −1/−2 e científica abaixo de 0,001.
- c§5 / L13: `cos₀`, `cosᵣ`, `cos₉` e `cosᵣ⁻¹` aparecem; `cis` não aparece em nenhuma leitura.

**Observações fora da taxa (não previstas).**
- 3c-30: depois de `123 =`, F-E **não** apaga a expressão `123 =`. Explicação [O, 0x180112db0 `case 0x79`]: sem operador
  pendente, o `=` só reexibe e não zera motor+0xe22, então o próximo comando não passa por `FUN_180112c40` (a§3.6). Em 3a-24
  havia operador pendente.
- Na sonda (fora dos casos), com o ângulo deixado em RAD pela etapa de árvore, `5 cos` mostrou
  `0,28366218546322626446663917151356`, que é cos 5 arredondado a 32 dígitos (…1355|73 → …1356), coerente com c§3.1/§3.13.


## 10. Auditoria pós-execução (2026-10-23)

### 10.1 Ordem das etapas em relação ao congelamento (20:12:52)

Fontes: (a) transcrição da sessão da 3c (`~/.claude/projects/-home-art-projetos-calc-re/caa2e3f2-….jsonl`, carimbos UTC
convertidos para −03:00), que guarda cada comando enviado e a saída; (b) carimbos gravados pelo próprio script nos
arquivos (`arvore-uia-3c.txt` linha 1, cabeçalhos de `log-execucao-3c.txt` e `resultados-reais-3c.txt`, `FIM` em
`saida-casos3c.txt`); (c) mtime dos arquivos. O `log-execucao-3c.txt` só tem o início (20:15:50) e as leituras dos casos,
sem horário por caso. Os horários por caso vêm do mtime das capturas `capturas/3c-*.png` (3c-01 a 3c-75, de 20:15:5x a 20:20:32).
[O em todos os itens]

| Horário | Etapa | O que leu da Calculadora |
|---|---|---|
| 20:05:04 | `visor3c.py` gera os valores do bloco B | nada (só Python no Linux) |
| 20:07:46 | `which powershell.exe` | nada (só localiza o executável) |
| 20:12:26 | `03c-casos-de-teste.md` gravado | — |
| **20:12:51–20:12:52** | **SHA-256 anexado a `hashes-originais.txt` (`date` devolveu 20:12:52)** | — |
| 20:14:20–20:14:31 | **Arvore3c** (cabeçalho interno 20:14:21) | Nome, padrões e estado de toggle de 7 botões; o rótulo do ângulo antes de cada um de 4 cliques (DEG→RAD→GRAD→DEG→**RAD**); a árvore UIA com o submenu aberto (visor `A exibição é 0`); visibilidade de botões com 2nd; visor final `0`. **Nenhum valor calculado.** Deixou o ângulo em RAD. |
| 20:14:58–20:15:03 | **Sonda3c** | `C`, `5` → visor `5`; estado do submenu e do toggle; visor `5` depois do Toggle e do Esc; depois `cos` (em RAD, herdado da Arvore3c) → visor **`0,28366218546322626446663917151356`** e expressão (Name UIA) `Expression é radianos do cosseno (5)`. **É um valor de cálculo**, lido 2 min 11 s **depois** do congelamento. |
| 20:15:15–20:15:19 | Casos3c com filtro `CASOS3C=3c-01,3c-59` (1ª tentativa) | abortou no preparo: `estado inicial: visor '0,2836…'` (o resto da sonda). Nenhum caso executado. |
| 20:15:30–20:15:41 | Casos3c com filtro `3c-01,3c-59` (piloto, cabeçalho 20:15:31) | 3c-01 → `0`, 3c-59 → `30` (mais Name UIA). Arquivo sobrescrito pela execução completa; os valores são iguais aos dela. |
| 20:15:48 → 20:15:50–20:20:33 | **Casos3c** completo | todos os casos |
| 20:16:51 | `comparar-3c.py` escrito (previsões copiadas do congelado, com conferência do hash) | — |
| 20:17:06 | `04-lacunas.md` editado durante a execução | — (ver nota abaixo) |
| 20:20:57–20:22:26 | folhas de capturas, transcrição, teste negativo, seção 9 | — |

**Conclusão.** Antes de 20:12:52 nenhum comando da sessão da 3c executou nem leu a Calculadora: o primeiro
`powershell.exe -File rodar-casos.ps1` é o das 20:14:19. A única leitura de valor calculado fora dos casos é a da Sonda3c
(cos 5 rad), feita depois do congelamento e que não é entrada de nenhum caso do 03c. **Nenhum caso precisa ser
reclassificado por causa das etapas da 3c.**

**Leituras de fases anteriores (antes de 20:12:52).** Também conferi as execuções da 3a (18:49–18:57) e da 3b (19:28–19:40):
- **3c-47** (`2 + 3 ) × 4 =` → `14`, expressão `2 + 3 × 4 =`): o mesmo cálculo, no **Científico**, já tinha sido executado e
  lido em 3a-02c (18:55:51, `14` | `2 + 3 × 4 =`) e em 3b-02c. O único elemento novo do 3c-47 é o `)` sem `(` ser ignorado.
  **Reclassificado**: continua *acerto*, mas **não independente**: o valor e a expressão eram conhecidos antes do
  congelamento. Sem ele, o bloco A fica 46/46 casos independentes.
- O formato `1,e+N` (3c-25) e a científica abaixo de 0,001 (3c-35) seguem regras vistas na 3a (3a-21 `1,e+16`, 3a-22
  `3,333…e-4`, no Padrão, com precisão 16). Essas regras foram previstas e confirmadas na 3a (02a §5). Na 3c o cálculo e a
  precisão são outros, então esses casos não foram reclassificados.
- As sondas da 3a (18:53–18:54) leram `sqr(9) + 1,` e `sqr(sqr(9)) +` no Padrão. Nenhum caso da 3c usa esses valores.

**Nota de procedimento.** A edição das 20:17:06 escreveu em L13 "conferido em caixa-preta nos casos de cosseno da 3c"
quando a execução ainda estava em curso, antes de haver resultado. Às 20:22:26, depois dos resultados, o texto foi trocado
pelo que vale hoje ("confirmado em caixa-preta: 3c-01, 3c-05, 3c-51, 3c-57, 3c-60"). As previsões não foram tocadas.
O hash do 03c continua `b31e6aee…d2e1`.

### 10.2 Como as previsões de 32 dígitos do bloco B foram obtidas

Origem: `trabalho/scripts/visor3c.py` (20:05), que é o que o 03c cita. A auditoria está em
`trabalho/scripts/auditoria3c_b.py`, com a saída em `trabalho/fase3c/auditoria-bloco-b.txt`. [O, pelo código do script]

Cada previsão tem duas camadas:
1. **Valor**: **biblioteca de alta precisão**. É o `decimal` do Python com 90 dígitos e valores matematicamente exatos:
   π por Machin; sen, eˣ e atan por séries escritas no script sobre `Decimal`, levadas até 10⁻⁸⁸; cos = sen(π/2 − x);
   asen por atan; ln e √ pelos métodos do `Decimal`. **O algoritmo do motor não foi emulado**: não entram o π de 41 dígitos
   de `asin(1/2)·6`, a redução mod 360/2π com esse π, a série até ~10⁻¹²⁸, o `FUN_1801265d0` nem a Γ de `FUN_18013b1b0`.
2. **Formato do visor**: **emulação do código do motor**, `NumberToString` 0x1801300f0 lido no binário (c§3.13). O código
   trunca para 34 dígitos e arredonda meia unidade para cima na 32ª posição (ou na 32ª casa decimal quando −2 ≤ e ≤ 0),
   escolhe a notação científica e põe os separadores.
3. **Decisões de domínio e de fluxo**: **leitura do binário**. São elas: −10¹⁰⁰ é aceito e reduzido (3c-62), F-E (3c-63)
   e o texto da expressão.

| ID | Cálculo | Como o valor de 32 dígitos foi obtido | Margem* | Discrimina o motor? |
|---|---|---|---:|---|
| 3c-50 | sen 30° | Decimal: série do seno em 30·π/180 | 0,500 | não |
| 3c-51 | cos 60° | Decimal: sen(π/2 − 60·π/180) | 0,500 | não |
| 3c-52 | sen 45° | Decimal: série do seno | 0,404 | não |
| 3c-53 | tan 45° | Decimal: sen/cos | 0,500 | não |
| 3c-54 | sen −30° | Decimal: −sen 30° (no script, sinal aplicado ao valor de 3c-50) | 0,500 | não |
| 3c-55 | sen 1 rad | Decimal: série do seno | 0,400 | não (o 32º dígito arredondado a 0 some: regra de formato) |
| 3c-56 | tan 1 rad | Decimal: sen/cos | 0,102 | não |
| 3c-57 | cos 1 grad | Decimal: sen(π/2 − π/200) | 0,283 | não |
| 3c-58 | sen 100 grad | Decimal: série do seno em π/2 | 0,500 | não |
| 3c-59 | asen 0,5 (DEG) | Decimal: atan(x/√(1−x²))·180/π | 0,500 | não |
| 3c-60 | acos 0,5 (RAD) | Decimal: π/2 − asen | 0,176 | não |
| 3c-61 | atan 1 (GRAD) | Decimal: atan(1)·200/π | 0,500 | não |
| 3c-62 | sen(−10¹⁰⁰ °) | Decimal: sen(−280°). A redução 10¹⁰⁰ ≡ 280 (mod 360) foi feita à mão; a aceitação de −10¹⁰⁰ vem do binário | 0,199 | não no valor (o motor dá o exato); o par 3c-08/3c-62 discrimina o **domínio** (ver abaixo) |
| 3c-63 | π, F-E | Decimal: Machin | 0,471 | não no valor; o `e+0` é regra de formato |
| 3c-64 | e | Decimal: série de exp(1) | 0,125 | não |
| 3c-65 | e¹ | Decimal: série de exp(1) | 0,125 | não |
| 3c-66 | e⁻¹⁰ | Decimal: série de exp(−10) | 0,110 | não no valor; a científica com 32 significativos é regra de formato |
| 3c-67 | ln 10 | `Decimal.ln` | 0,142 | não |
| 3c-68 | log 2 | `Decimal.ln(2)/ln(10)` | 0,197 | não |
| 3c-69 | log 1000 | `Decimal.ln(1000)/ln(10)` | 0,500 | não |
| 3c-70 | 10^0,5 | `Decimal.sqrt(10)` (o motor usa powrat, que não foi emulado) | 0,315 | não |
| 3c-71 | 2^0,5 | `Decimal.sqrt(2)` | 0,481 | não |
| 3c-72 | 27 ʸ√ 3 | **constante 3 escrita à mão** (valor exato, nada calculado) | 0,500 | não |
| 3c-73 | −8 ʸ√ 3 | **constante −2 escrita à mão** | 0,500 | não pelo critério abaixo: o motor dá a raiz real exata. Separa o motor de um `pow` ingênuo via exp/ln, que daria erro |
| 3c-74 | 8 logᵧ 2 | `Decimal.ln(8)/ln(2)` | 0,500 | não |
| 3c-75 | 0,5! | **fórmula fechada** Γ(1,5) = √π/2 (a Γ do motor não foi emulada) | 0,241 | não |

\* Margem = distância dos dígitos seguintes do valor exato até a fronteira de arredondamento, em unidades da última posição
exibida (0,5 = o mais longe possível, como em valores redondos). Um erro do motor só muda o visor se passar da margem.

**Resultado da auditoria.**
- Nos 26 casos, a previsão é **o valor matematicamente exato arredondado** na posição da regra do visor. O
  `auditoria3c_b.py` confere que o arredondamento correto (meio para par) do valor exato dá o mesmo texto que a regra do
  motor (truncar para 34 e somar meia unidade) em 26/26.
- **Nenhum caso do bloco B discrimina o motor**, no sentido pedido: em nenhum deles o motor se afasta do valor exato e a
  análise previu esse afastamento. A menor margem é 0,102 unidade (3c-56). A ordem de grandeza estimada para o erro do motor,
  ~10⁻⁴¹ por causa do π de 41 dígitos, fica muito abaixo disso [I]. Os casos foram escolhidos (ou caíram) longe das fronteiras.
- O 26/26 do bloco B **confirma** a regra de exibição (c§3.13), a escolha de função e unidade de ângulo (sen × cos, DEG/RAD/GRAD,
  inversas), as decisões de domínio e que o erro do motor é menor que a margem de cada caso. **Não confirma** o algoritmo
  numérico (π de 41 dígitos, séries, powrat, Γ). Uma calculadora qualquer que arredonde corretamente para 32 dígitos e use a
  mesma regra de formato daria os mesmos 26 visores. Por isso, na §9, "erro do π e das séries menor que meia unidade" deve ser
  lido como "menor que a margem de cada caso (≥ 0,10 unidade)". "0,5! = Γ(1,5) com 32 dígitos corretos" confirma o valor e
  não a implementação de `FUN_18013b1b0`. L26 continua aberta.
- **Casos da 3c que discriminam o motor** (todos no bloco A). O motor se afasta do resultado matemático e a análise previu:
  3c-08 (sen 10¹⁰⁰ ° existe e vale sen 280° ≈ −0,985; o motor dá "Entrada inválida"); 3c-14 (3250! é finito; o motor dá
  "Estouro"); 3c-38 (2^3^2 = 512 na convenção matemática; o motor dá 64); 3c-46 (1 + 5 × 4 = 21; o motor dá 20); 3c-19
  (5 mod 0 é indefinido; o motor dá 5).
  Os casos abaixo discriminam o motor de outras implementações, mas sem afastamento do valor matemático: 3c-16/17 (mod com o
  sinal do divisor; `fmod` daria −1/1); 3c-01/03/04 (cos 90°, sen π, sen 180° = 0 exato, igual à matemática graças ao corte de
  10⁻³²; sem o corte o π̃ de 41 dígitos deixaria um resíduo de ~10⁻⁴¹ [I]); 3c-36 e 3c-09 (regras de entrada); 3c-33/34/35
  (formato).
- **Para a Fase 3f**: um caso que discrimine o algoritmo precisa de uma margem menor que o erro previsto, ou de um resultado que
  exponha esse erro. Exemplo, a decidir na 3f: `π − 3,1415926535897932384626433832795 =`. Com o π de 41 dígitos o resultado
  mostra os dígitos 33–41 de π e depois o erro do π do motor. Com π exato, mostraria os dígitos 33+ de π sem parar.
