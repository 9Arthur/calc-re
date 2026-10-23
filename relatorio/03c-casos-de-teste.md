# 03c — Casos de teste da Fase 3c (modo científico)

Versão 1 (2026-10-22). Previsões tiradas só de `relatorio/02-features/c-cientifico.md` (seção na coluna "Base", prefixo `c`)
e de `a-operacoes-basicas.md` (prefixo `a`). Os valores de 32 dígitos foram calculados por `trabalho/scripts/visor3c.py`
(valor matemático com 80 dígitos + regra de exibição de c§3.13). Este arquivo é congelado por SHA-256 em
`hashes-originais.txt` **antes** de qualquer execução; as colunas de previsão não mudam depois. Resultados e comparação
ficam em `02-features/c-cientifico.md`, seção de resultados.

## Como executar

**Ambiente e estado inicial**
- Calculadora 11.2607.0.0 com Windows e formato regional pt-BR (vírgula decimal, ponto de milhar), como nas fases anteriores.
- Antes de cada caso: modo **Científica**; "2nd" (Função inversa) desligado; F-E desligado; C; depois o ângulo da coluna
  "Ângulo" (clicar no botão DEG/RAD/GRAD até mostrar o modo pedido).
- Automação: `trabalho/automacao/rodar-casos.ps1 -Etapa Casos3c`.

**Notação**

| Notação | Botão (Name pt-BR / AutomationId) |
|---|---|
| `sin` `cos` `tan` | submenu Trigonometria (`trigButton`) → `sinButton`/`cosButton`/`tanButton` |
| `sin⁻¹` `cos⁻¹` `tan⁻¹` | submenu Trigonometria com o "2nd" do submenu ligado (`trigShiftButton`) → `invsinButton`… |
| `x^y` `10^x` `log` `ln` `n!` `mod` `exp` `\|x\|` `(` `)` `π` `e` | `powerButton`, `powerOf10Button`, `logBase10Button`, `logBaseEButton`, `factorialButton`, `modButton`, `expButton`, `absButton`, `openParenthesisButton`, `closeParenthesisButton`, `piButton`, `eulerButton` |
| `ʸ√x` `logᵧx` `eˣ` | com "2nd" (`shiftButton`) ligado: `ySquareRootButton`, `logBaseY`, `powerOfEButton`; o 2nd é desligado logo depois |
| `F-E` | `ftoeButton` (alternar) |
| `[DEG→RAD]` | um clique no botão de ângulo que mostra DEG |
| `±` `÷` `×` `−` `+` `=` `,` | como na 3a |
| `→` | ponto de leitura intermediário |

**O que anotar**: visor e linha de expressão em cada leitura.

**Comparação (fixada antes da execução)**
- Visor: exato.
- Expressão: sem espaços (L20). Se a linha estiver cortada na tela (seta de rolagem), o texto visível tem de ser um
  **sufixo** do previsto (a tela mostra o fim, 3a-26). "—" = não prevista (fora da comparação).
- **Bloco A**: *acerto* = todas as leituras conferem; *parcial* = visores conferem e falha alguma expressão; *erro* = algum visor não confere.
- **Bloco B**: as mesmas classes, e mais *quase* = o visor só difere no **último dígito exibido** (por ±1, ou pelo
  arredondamento que apaga/cria um zero final). O último dígito depende do motor numérico (erro das séries, de π e do
  corte de precisão), que só será lido na Fase 3f. A taxa do bloco B conta só *acerto*; *quase* é informado à parte.

**Previsões gerais [O]**: erros em pt-BR: `Entrada inválida` (chave 100), `Estouro` (107). Os símbolos da expressão ficam
em inglês/símbolo (L17): `sin₀`, `cosᵣ`, `tan₉`, `sin₀⁻¹`, `fact`, `ln`, `log`, `e^`, `10^`, `abs`, `Mod`, `^`, `yroot`,
`log base`.

## A. O resultado não depende de arredondamento de função transcendental (valores exatos, erros, formato)

| ID | Ângulo | Teclas exatas, em ordem | Visor previsto | Expressão prevista | O/I | Base |
|---|---|---|---|---|---|---|
| 3c-01 | DEG | `90` `cos` | `0` | `cos₀( 90 )` | O (corte de 10⁻³²; folga ~10⁻⁴¹) | c§3.1 |
| 3c-02 | DEG | `90` `tan` | `Entrada inválida` | `tan₀( 90 )` | O | c§3.1 (4), a§4 |
| 3c-03 | RAD | `π` `sin` | `0` | `sinᵣ( 3,1415926535897932384626433832795 )` | O | c§3.1, c§3.10 |
| 3c-04 | DEG | `180` `sin` | `0` | `sin₀( 180 )` | O | c§3.1 |
| 3c-05 | RAD | `0` `cos` | `1` | `cosᵣ( 0 )` | O (e: não aparece `cis`) | c§3.1, c§5 |
| 3c-06 | DEG | `1` `sin⁻¹` | `90` | `sin₀⁻¹( 1 )` | O (π/2 por constante) | c§3.2 |
| 3c-07 | DEG | `2` `sin⁻¹` | `Entrada inválida` | `sin₀⁻¹( 2 )` | O | c§3.2 |
| 3c-08 | DEG | `1` `exp` `100` → `sin` | `1,e+100` → `Entrada inválida` | — → `sin₀( 1,e+100 )` | O | c§3.1 (5), c§3.8 |
| 3c-09 | DEG | `1` `[DEG→RAD]` `2` | `2` | — | O (a troca de ângulo finaliza o número; sem ela seria `12`) | c§1, c S14 |
| 3c-10 | DEG | `5` `n!` | `120` | `fact( 5 )` | O | c§3.5 |
| 3c-11 | DEG | `0` `n!` | `1` | `fact( 0 )` | O | c§3.5 |
| 3c-12 | DEG | `20` `n!` | `2.432.902.008.176.640.000` | `fact( 20 )` | O | c§3.5 |
| 3c-13 | DEG | `1` `±` `n!` | `Entrada inválida` | `fact( -1 )` | O | c§3.5 |
| 3c-14 | DEG | `3250` `n!` | `Estouro` | `fact( 3250 )` | O | c§3.5 |
| 3c-15 | DEG | `7` `mod` `3` `=` | `1` | `7 Mod 3 =` | O | c§3.6 |
| 3c-16 | DEG | `7` `±` `mod` `3` `=` | `2` | `-7 Mod 3 =` | I (sinal do resto de `remnum`) | c§3.6 |
| 3c-17 | DEG | `7` `mod` `3` `±` `=` | `-2` | `7 Mod -3 =` | I (idem) | c§3.6 |
| 3c-18 | DEG | `7` `,` `5` `mod` `2` `=` | `1,5` | `7,5 Mod 2 =` | O | c§3.6 |
| 3c-19 | DEG | `5` `mod` `0` `=` | `5` | `5 Mod 0 =` | O | c§3.6 |
| 3c-20 | DEG | `2` `x^y` `10` `=` | `1.024` | `2 ^ 10 =` | O | c§3.4 |
| 3c-21 | DEG | `2` `x^y` `1` `±` `=` | `0,5` | `2 ^ -1 =` | I (expoente inteiro negativo = inverso exato) | c§3.4 |
| 3c-22 | DEG | `0` `x^y` `1` `±` `=` | `Entrada inválida` | `0 ^` | O (visor) / I (expressão, como 3a-04) | c§3.4, c§4 |
| 3c-23 | DEG | `3` `10^x` | `1.000` | `10^( 3 )` | O | c§3.3 |
| 3c-24 | DEG | `31` `10^x` | `10.000.000.000.000.000.000.000.000.000.000` | `10^( 31 )` | O | c§3.3, c§3.13 |
| 3c-25 | DEG | `32` `10^x` | `1,e+32` | `10^( 32 )` | O | c§3.13 |
| 3c-26 | DEG | `0` `log` | `Entrada inválida` | `log( 0 )` | O | c§3.3 |
| 3c-27 | DEG | `1` `±` `ln` | `Entrada inválida` | `ln( -1 )` | O | c§3.3 |
| 3c-28 | DEG | `2` `exp` → `3` → `=` | `2,e+0` → `2,e+3` → `2.000` | — → — → `2000 =` | O (visor) / I (expressão sem agrupamento, como 3a-21) | c§3.8 |
| 3c-29 | DEG | `1` `exp` `4` `±` → `=` | `1,e-4` → `0,0001` | — → `0,0001 =` | O / I (expressão) | c§3.8 |
| 3c-30 | DEG | `123` `=` → `F-E` → `F-E` | `123` → `1,23e+2` → `123` | — | O | c§3.9 |
| 3c-31 | DEG | `5` `±` `\|x\|` | `5` | `abs( -5 )` | O | c§3.7 |
| 3c-32 | DEG | `1` `÷` `3` `=` | `0,33333333333333333333333333333333` | `1 ÷ 3 =` | O | c§3.13 |
| 3c-33 | DEG | `2` `÷` `30` `=` | `0,06666666666666666666666666666667` | `2 ÷ 30 =` | O (31 significativos, e = −1) | c§3.13 |
| 3c-34 | DEG | `1` `÷` `300` `=` | `0,00333333333333333333333333333333` | `1 ÷ 300 =` | O (30 significativos, e = −2) | c§3.13 |
| 3c-35 | DEG | `1` `÷` `3000` `=` | `3,3333333333333333333333333333333e-4` | `1 ÷ 3000 =` | O | c§3.13 |
| 3c-36 | DEG | `12345678901234567890123456789012` → `3` | `12.345.678.901.234.567.890.123.456.789.012` → igual (33º ignorado) | — | O | a§3.1, c S16 |
| 3c-37 | DEG | `2` `×` `3` `+` → `4` `×` `5` `=` | `6` → `26` | `2 × 3 +` → `2 × 3 + 4 × 5 =` | O | c§3.11 |
| 3c-38 | DEG | `2` `x^y` `3` `x^y` → `2` `=` | `8` → `64` | `2 ^ 3 ^` → `2 ^ 3 ^ 2 =` | O | c§3.11 |
| 3c-39 | DEG | `2` `+` `3` `×` `4` `x^y` `2` `=` | `50` | `2 + 3 × 4 ^ 2 =` | O | c§3.11 |
| 3c-40 | DEG | `7` `mod` `4` `×` `2` `=` | `6` | `7 Mod 4 × 2 =` | O | c§3.11 |
| 3c-41 | DEG | `2` `+` `3` `+` `×` → `4` `=` | `5` → `20` | `( 2 + 3 ) ×` → `( 2 + 3 ) × 4 =` | O (L11) | c§3.11 |
| 3c-42 | DEG | `(` `2` `+` `3` `)` → `×` `4` `=` | `5` → `20` | `( 2 + 3 )` → `( 2 + 3 ) × 4 =` | O (visor) / I (expressão) | c§3.12 |
| 3c-43 | DEG | `(` `2` `+` `3` `=` | `5` | `( 2 + 3 ) =` | O / I | c§3.12 |
| 3c-44 | DEG | `2` `×` `(` `3` `+` `(` `4` `−` `1` `=` | `12` | `2 × ( 3 + ( 4 - 1 ) ) =` | O / I | c§3.12 |
| 3c-45 | DEG | `2` `(` `3` `+` `4` `)` `=` | `14` | `2 × ( 3 + 4 ) =` | O / I | c§3.12 |
| 3c-46 | DEG | `1` `+` `(` `2` `+` `3` `)` → `4` → `=` | `5` → `4` → `20` | — → — → `1 + ( 2 + 3 ) × 4 =` | O (visor) / I (expressão) | c§3.12 (× após `)`) |
| 3c-47 | DEG | `2` `+` `3` `)` `×` `4` `=` | `14` | `2 + 3 × 4 =` | O / I | c§3.12 (`)` sem `(`) |

## B. O resultado depende dos últimos dígitos de uma função transcendental

Previsão de 32 dígitos significativos (o motor exibe no máximo 32; zeros finais somem). **O último dígito exibido depende
do motor numérico (Fase 3f).** A coluna "33–42" traz os dígitos seguintes do valor matemático, para medir a distância à
fronteira de arredondamento.

| ID | Ângulo | Teclas exatas, em ordem | Visor previsto | 33–42 | Expressão prevista | Base |
|---|---|---|---|---|---|---|
| 3c-50 | DEG | `30` `sin` | `0,5` | 0000000000 | `sin₀( 30 )` | c§3.1 |
| 3c-51 | DEG | `60` `cos` | `0,5` | 0000000000 | `cos₀( 60 )` | c§3.1 |
| 3c-52 | DEG | `45` `sin` | `0,70710678118654752440084436210485` | 9039284835 | `sin₀( 45 )` | c§3.1 |
| 3c-53 | DEG | `45` `tan` | `1` | 0000000000 | `tan₀( 45 )` | c§3.1 |
| 3c-54 | DEG | `30` `±` `sin` | `-0,5` | 0000000000 | `sin₀( -30 )` | c§3.1 |
| 3c-55 | RAD | `1` `sin` | `0,8414709848078965066525023216303` | 8999622563 | `sinᵣ( 1 )` | c§3.1 (32º dígito arredonda para 0 e some) |
| 3c-56 | RAD | `1` `tan` | `1,5574077246549022305069748074584` | 6017308725 | `tanᵣ( 1 )` | c§3.1 |
| 3c-57 | GRAD | `1` `cos` | `0,99987663248166059863890712773125` | 2174499277 | `cos₉( 1 )` | c§3.1, c§5 |
| 3c-58 | GRAD | `100` `sin` | `1` | 0000000000 | `sin₉( 100 )` | c§3.1 |
| 3c-59 | DEG | `0` `,` `5` `sin⁻¹` | `30` | 0000000000 | `sin₀⁻¹( 0,5 )` | c§3.2 |
| 3c-60 | RAD | `0` `,` `5` `cos⁻¹` | `1,0471975511965977461542144610932` | 6762806572 | `cosᵣ⁻¹( 0,5 )` | c§3.2, c§5 |
| 3c-61 | GRAD | `1` `tan⁻¹` | `50` | 0000000000 | `tan₉⁻¹( 1 )` | c§3.2 |
| 3c-62 | DEG | `1` `±` `exp` `100` → `sin` | `-1,e+100` → `0,98480775301220805936674302458952` | 3013670643 | — → `sin₀( -1,e+100 )` | c§3.1 (5): −10¹⁰⁰ passa; sen(−280°) |
| 3c-63 | DEG | `π` → `F-E` → `F-E` | `3,1415926535897932384626433832795` → `3,1415926535897932384626433832795e+0` → `3,1415926535897932384626433832795` | 0288419716 | — | c§3.9, c§3.10 |
| 3c-64 | DEG | `e` | `2,7182818284590452353602874713527` | 6249775724 | — | c§3.10 |
| 3c-65 | DEG | `1` `eˣ` | `2,7182818284590452353602874713527` | 6249775724 | `e^( 1 )` | c§3.3 |
| 3c-66 | DEG | `10` `±` `eˣ` | `4,5399929762484851535591515560551e-5` | 6102379180 | `e^( -10 )` | c§3.3, c§3.13 |
| 3c-67 | DEG | `10` `ln` | `2,3025850929940456840179914546844` | 6420760110 | `ln( 10 )` | c§3.3 |
| 3c-68 | DEG | `2` `log` | `0,30102999566398119521373889472449` | 3026768189 | `log( 2 )` | c§3.3 |
| 3c-69 | DEG | `1000` `log` | `3` | 0000000000 | `log( 1000 )` | c§3.3 |
| 3c-70 | DEG | `0` `,` `5` `10^x` | `3,1622776601683793319988935444327` | 1853371955 | `10^( 0,5 )` | c§3.3, c§3.4 |
| 3c-71 | DEG | `2` `x^y` `0` `,` `5` `=` | `1,4142135623730950488016887242097` | 9807856967 | `2 ^ 0,5 =` | c§3.4 |
| 3c-72 | DEG | `27` `ʸ√x` `3` `=` | `3` | 0000000000 | `27 yroot 3 =` | c§3.4 |
| 3c-73 | DEG | `8` `±` `ʸ√x` `3` `=` | `-2` | 0000000000 | `-8 yroot 3 =` | c§3.4 (I: raiz ímpar de negativo aceita) |
| 3c-74 | DEG | `8` `logᵧx` `2` `=` | `3` | 0000000000 | `8 log base 2 =` | c§3.4 |
| 3c-75 | DEG | `0` `,` `5` `n!` | `0,88622692545275801364908374167057` | 2591398774 | `fact( 0,5 )` | c§3.5 (I: Γ) |

## Observações

- **"cis"**: c§5 conclui que não há caminho que o mostre. Os casos com cosseno nos três modos (3c-01 `cos₀`, 3c-05
  `cosᵣ`, 3c-57 `cos₉`, 3c-60 `cosᵣ⁻¹`) conferem a expressão; `cis` em qualquer um deles derruba a conclusão.
- **3c-09**: se a troca de ângulo não finalizasse o número, o visor mostraria `12`.
- **3c-46**: o `1 +` é descartado pelo × implícito depois de `)`; com × explícito (`1 + ( 2 + 3 ) × 4 =`) o resultado seria 21.
- **3c-62**: a comparação do domínio trig é com sinal (c§3.1): `1 exp 100 sin` dá erro (3c-08) e `-1 exp 100 sin` não.
- **Bloco B, valores redondos** (3c-50, 51, 53, 54, 58, 59, 61, 69, 72, 73, 74): o motor chega perto do valor exato (erro
  esperado de ~10⁻⁴⁰) e o arredondamento a 32 dígitos o torna redondo. Se o erro real for maior que 5·10⁻³³, o visor
  mostrará `0,49999…` ou `2,9999…`.
- **3c-30 e 3c-63** terminam com F-E desligado de propósito (c§3.9, L25).
