# 03d — Casos de teste da Fase 3d (modo programador)

Versão 1 (2026-10-23). Previsões tiradas só de `relatorio/02-features/d-programador.md` (seção na coluna "Base", prefixo
`d`) e das fases anteriores (prefixos `a`, `c`). Os valores foram calculados por `trabalho/scripts/prog3d.py`, que emula
as regras lidas no binário: truncamento, exibição com sinal, agrupamento, limites de digitação, troca de tamanho,
deslocamentos e carry. Nada foi executado antes deste arquivo. Ele é congelado por SHA-256 em `hashes-originais.txt`
**antes** de qualquer execução, e as colunas de previsão não mudam depois. Os resultados ficam em
`02-features/d-programador.md`, seção de resultados.

## Como executar

**Ambiente e estado inicial**
- Calculadora 11.2607.0.0, Windows e formato regional pt-BR (vírgula decimal, ponto de milhar), como nas fases anteriores.
- Antes de cada caso: modo **Programador**; teclado completo (não o de bits), salvo nos casos do bloco F; C; base da
  coluna "Base"; tamanho da coluna "Tam." (clicar no botão de tamanho até mostrar o pedido); nos casos de deslocamento,
  a opção da coluna "Desl." no submenu Bit-shift.
- Automação: `trabalho/automacao/rodar-casos.ps1 -Etapa Casos3d`. Os AutomationIds serão conferidos numa etapa de árvore
  UIA depois do congelamento, como na 3c.

**Notação**

| Notação | Significado |
|---|---|
| `255`, `1A3` | um botão por dígito (0–9, A–F) |
| `AND` `OR` `XOR` `NAND` `NOR` `NOT` | submenu Bit a bit (`bitwiseButton`) → `andButton`… |
| `Lsh` `Rsh` | deslocamento com a opção "Desl." já escolhida: Arit → `lshButton`/`rshButton`; Lóg → `lshLogicalButton`/`rshLogicalButton` (Rsh lógico = RshL 505); Circ → `rolButton`/`rorButton` (escritos `Rol`/`Ror`); Carry → botões "…com transporte" (escritos `RolC`/`RorC`) |
| `%` | botão Mod do Programador (`modButton`) |
| `[HEX]` `[DEC]` `[OCT]` `[BIN]` | botão da base no painel |
| `[QWORD]`… | clicar no botão de tamanho até ele mostrar esse tamanho. A automação registra o tamanho e o visor a cada clique, mas a comparação usa só a leitura indicada |
| `[bitN]` | botão do bit N no teclado de bits |
| `±` `÷` `×` `−` `+` `=` `C` | como na 3a |
| `→` | ponto de leitura intermediário |

**O que anotar**: o visor em cada leitura; na leitura final, as **linhas** do painel (H = HEX, D = DEC, O = OCT, B = BIN)
quando previstas, os **bits ligados** quando previstos e a expressão quando prevista.

**Comparação (fixada antes da execução)**
- Visor e linhas: texto exato, com os espaços de agrupamento e o `.` de milhar. Bits: o conjunto exato dos bits ligados.
- Expressão: sem espaços (L20), com a mesma regra de sufixo da 3c para linha cortada. "—" = não prevista.
- *acerto* = todas as leituras previstas conferem; *parcial* = visor, linhas e bits conferem e falha alguma expressão;
  *erro* = algum visor, linha ou conjunto de bits não confere.
- Se a árvore UIA mostrar que as linhas ou os bits não podem ser lidos, essas leituras saem da comparação. Isso é
  registrado, e o caso é avaliado pelo resto.
- Além da taxa por bloco, informo a taxa só nos casos marcados **Discr. = sim**.

**Colunas MP e Discr.** MP ("matemática pura") é o resultado esperado de um modelo ingênuo: inteiros sem limite, operandos
como digitados, sem truncamento à largura, sem limite de dígitos, valor preservado na troca de tamanho, mod de Euclides
(resto ≥ 0), ÷ exata, avaliação da esquerda para a direita (só nas linhas de precedência) e carry ligado ao número.
**Discr. = sim** quando a previsão do motor difere de MP, ou seja, quando um acerto só é possível se a regra lida no
binário estiver certa.

**Previsões gerais [O]**: erros em pt-BR: `Resultado não definido` (chave 108), `Resultado indefinido` (101),
`Não é possível dividir por zero` (99). Tokens de expressão: `AND`, `OR`, `XOR`, `NAND`, `NOR`, `Lsh`, `Rsh`, `%`,
`NOT(`, `RoL(`, `RoR(`.

## A. Bases, conversão e limites de digitação

| ID | Base | Tam. | Teclas | Visor previsto | Linhas previstas (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|
| 3d-01 | DEC | QWORD | `255` | `255` | H `FF` · D `255` · O `377` · B `1111 1111` | — | igual | não | O | d§3.1 |
| 3d-02 | DEC | QWORD | `1000` | `1.000` | H `3E8` · D `1.000` · O `1 750` · B `11 1110 1000` | — | igual | não | O | d§3.1 |
| 3d-03 | HEX | QWORD | `1A3` | `1A3` | H `1A3` · D `419` · O `643` · B `1 1010 0011` | — | igual | não | O | d§3.1 |
| 3d-04 | DEC | QWORD | `255` → `[HEX]` → `[OCT]` → `[BIN]` → `[DEC]` | `255` → `FF` → `377` → `1111 1111` → `255` | — | — | igual | não | O | d§3.2 |
| 3d-05 | HEX | QWORD | `123456789ABCDEF01` | `1234 5678 9ABC DEF0` | D `1.311.768.467.463.790.320` | — | aceita o 17º dígito | sim | O | d§3.3 |
| 3d-06 | OCT | QWORD | `1777777777777777777777` (22 díg.) | `1 777 777 777 777 777 777 777` | H `FFFF FFFF FFFF FFFF` · D `-1` | — | D `18.446.744.073.709.551.615` | sim | O | d§3.1, d§3.3 |
| 3d-07 | OCT | QWORD | `2777777777777777777777` (22 díg.) | `277 777 777 777 777 777 777` | H `2FFF FFFF FFFF FFFF` · D `3.458.764.513.820.540.927` | — | aceita o 22º dígito | sim | O | d§3.3 |
| 3d-08 | BIN | QWORD | `1` e 64 × `0` (65 díg.) | `1000` seguido de 15 grupos `0000` | H `8000 0000 0000 0000` · D `-9.223.372.036.854.775.808` | — | aceita o 65º dígito | sim | O | d§3.3 |
| 3d-09 | DEC | QWORD | `9223372036854775808` | `922.337.203.685.477.580` | — | — | `9.223.372.036.854.775.808` | sim | O | d§3.3 |
| 3d-10 | DEC | QWORD | `922337203685477580` `±` → `8` | `-922.337.203.685.477.580` → `-9.223.372.036.854.775.808` | H `8000 0000 0000 0000` | — | igual no visor | sim (H) | O | d§3.3 |
| 3d-11 | DEC | QWORD | `9223372036854775807` | `9.223.372.036.854.775.807` | H `7FFF FFFF FFFF FFFF` | — | igual | não | O | d§3.3 |
| 3d-12 | DEC | BYTE | `128` | `12` | — | — | `128` | sim | O | d§3.3 |
| 3d-13 | DEC | BYTE | `200` | `20` | — | — | `200` | sim | O | d§3.3 |
| 3d-14 | HEX | WORD | `12345` | `1234` | D `4.660` | — | aceita o 5º dígito | sim | O | d§3.3 |

## B. Tamanhos e troca de tamanho

| ID | Base | Tam. | Teclas | Visor previsto | Linhas previstas (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|
| 3d-20 | DEC | QWORD | `300` → `[BYTE]` | `300` → `44` | H `2C` | — | `300` | sim | O | d§3.2 |
| 3d-21 | DEC | QWORD | `200` → `[BYTE]` → `[QWORD]` | `200` → `-56` → `-56` | H `FFFF FFFF FFFF FFC8` · D `-56` | — | `200` / H `C8` | sim | O | d§3.2 |
| 3d-22 | DEC | QWORD | `65535` → `[WORD]` → `[QWORD]` | `65.535` → `-1` → `-1` | H `FFFF FFFF FFFF FFFF` | — | `65.535` | sim | O | d§3.2 |
| 3d-23 | DEC | QWORD | `2147483648` → `[DWORD]` | `2.147.483.648` → `-2.147.483.648` | H `8000 0000` | — | `2.147.483.648` | sim | **I** (ciclo Q→D; pelo caminho Q→B→W→D o visor seria `0`) | d§3.2, L27 |
| 3d-24 | DEC | QWORD | `4294967296` → `[DWORD]` | `4.294.967.296` → `0` | H `0` | — | `4.294.967.296` | sim | O | d§3.2 |
| 3d-25 | DEC | DWORD | `1` `±` → `[QWORD]` | `-1` → `-1` | H `FFFF FFFF FFFF FFFF` | — | H `FFFF FFFF` (`4.294.967.295`) | sim | O | d§3.2 |
| 3d-26 | HEX | QWORD | `FFFFFFFFFF` → `[DWORD]` | `FF FFFF FFFF` → `FFFF FFFF` | D `-1` | — | `FF FFFF FFFF` | sim | O | d§3.2 |

## C. Negativos, estouro, truncamento, ÷ e Mod

| ID | Base | Tam. | Teclas | Visor previsto | Linhas previstas (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|
| 3d-30 | DEC | QWORD | `1` `±` | `-1` | H `FFFF FFFF FFFF FFFF` · O `1 777 777 777 777 777 777 777` · B 16 grupos `1111` | — | igual | não | O | d§3.1 |
| 3d-31 | HEX | QWORD | `1` `±` | `FFFF FFFF FFFF FFFF` | D `-1` | — | igual | não | O | d§3.1 |
| 3d-32 | HEX | BYTE | `80` | `80` | D `-128` | — | D `128` | sim | O | d§3.1 |
| 3d-33 | DEC | QWORD | `9223372036854775807` `+` `1` `=` | `-9.223.372.036.854.775.808` | — | `9223372036854775807 + 1 =` | `9.223.372.036.854.775.808` | sim | O | d§3.1 |
| 3d-34 | DEC | DWORD | `2147483647` `+` `1` `=` | `-2.147.483.648` | — | `2147483647 + 1 =` | `2.147.483.648` | sim | O | d§3.1 |
| 3d-35 | DEC | WORD | `32767` `+` `1` `=` | `-32.768` | — | — | `32.768` | sim | O | d§3.1 |
| 3d-36 | DEC | BYTE | `127` `+` `1` `=` | `-128` | — | — | `128` | sim | O | d§3.1 |
| 3d-37 | DEC | BYTE | `100` `×` `3` `=` | `44` | — | `100 × 3 =` | `300` | sim | O | d§3.1 |
| 3d-38 | DEC | QWORD | `4294967296` `×` `4294967296` `=` | `0` | — | — | `18.446.744.073.709.551.616` | sim | O | d§3.1 |
| 3d-39 | DEC | QWORD | `4294967295` `×` `4294967295` `=` | `-8.589.934.591` | — | — | `18.446.744.065.119.617.025` | sim | O | d§3.1 |
| 3d-40 | DEC | QWORD | `7` `÷` `2` `=` | `3` | — | `7 ÷ 2 =` | `3,5` | sim | O | d§3.6 |
| 3d-41 | DEC | QWORD | `7` `±` `÷` `2` `=` | `-3` | — | `-7 ÷ 2 =` | `-3,5` | sim | O | d§3.6 |
| 3d-42 | DEC | QWORD | `7` `±` `%` `3` `=` | `-1` | — | `-7 % 3 =` | `2` (Científico 3c-16 também: 2) | sim | O | d§3.6 |
| 3d-43 | DEC | QWORD | `7` `%` `3` `±` `=` | `1` | — | `7 % -3 =` | `1` (Científico 3c-17: −2) | não (MP); sim contra o Científico | O | d§3.6 |
| 3d-44 | DEC | QWORD | `5` `%` `0` `=` | `Resultado indefinido` | — | — | indefinido (Científico 3c-19: `5`) | não (MP); sim contra o Científico | O | d§3.6 |
| 3d-45 | DEC | QWORD | `5` `÷` `0` `=` | `Não é possível dividir por zero` | — | — | igual | não | O | d§3.6, a§4 |
| 3d-46 | DEC | QWORD | `0` `÷` `0` `=` | `Resultado indefinido` | — | — | igual | não | O | d§3.6, a§4 |
| 3d-47 | DEC | QWORD | `5` `÷` `0` `=` → `[HEX]` | `Não é possível dividir por zero` → `0` | — | — | — | não | O (I: vslot 0x350 = IsInError) | d§3.2 |
| 3d-48 | DEC | QWORD | `1` `−` `2` `=` | `-1` | H `FFFF FFFF FFFF FFFF` | `1 - 2 =` | H `-1` | não | O | d§3.1 |

## D. Operações bit a bit e precedência

| ID | Base | Tam. | Teclas | Visor previsto | Linhas previstas (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|
| 3d-50 | DEC | QWORD | `12` `AND` `10` `=` | `8` | — | `12 AND 10 =` | igual | não | O | d§3.4 |
| 3d-51 | DEC | QWORD | `12` `OR` `10` `=` | `14` | — | `12 OR 10 =` | igual | não | O | d§3.4 |
| 3d-52 | DEC | QWORD | `12` `XOR` `10` `=` | `6` | — | `12 XOR 10 =` | igual | não | O | d§3.4 |
| 3d-53 | DEC | QWORD | `12` `NAND` `10` `=` | `-9` | H `FFFF FFFF FFFF FFF7` | `12 NAND 10 =` | `-9` | não | O | d§3.4 |
| 3d-54 | DEC | QWORD | `12` `NOR` `10` `=` | `-15` | — | `12 NOR 10 =` | `-15` | não | O | d§3.4 |
| 3d-55 | DEC | QWORD | `5` `NOT` | `-6` | H `FFFF FFFF FFFF FFFA` | `NOT( 5 )` | `-6` | não | O | d§3.4 |
| 3d-56 | DEC | BYTE | `5` `NOT` | `-6` | H `FA` | `NOT( 5 )` | H `FFFF…FFFA` | sim (H) | O | d§3.4 |
| 3d-57 | HEX | BYTE | `F0` `NOT` | `F` | D `15` | — | D `-241` | sim | O | d§3.4 |
| 3d-58 | DEC | QWORD | `6` `OR` `1` `AND` `2` `=` | `6` | — | `6 OR 1 AND 2 =` | `2` (esq.→dir.) | sim | O | d§3.4, c§3.11 |
| 3d-59 | DEC | QWORD | `12` `XOR` `10` `AND` `6` `=` | `14` | — | `12 XOR 10 AND 6 =` | `6` (esq.→dir.) | sim | O | d§3.4, c§3.11 |
| 3d-60 | DEC | QWORD | `1` `OR` `5` `NAND` `3` `=` | `-1` | — | `1 OR 5 NAND 3 =` | `-2` (esq.→dir.) | sim | O | d§3.4, c§3.11 |
| 3d-61 | DEC | QWORD | `5` `+` `NOT` → `=` | `-6` → `-1` | — | `5 + NOT( 5 ) =` | `-1` → `4` (NOT de um operando novo 0) | sim | O | d§3.7, a§3.5 |
| 3d-62 | HEX | QWORD | `F` `AND` `3` `=` | `3` | D `3` | `F AND 3 =` | igual | não | O | d§3.4 |

## E. Deslocamentos

| ID | Base | Tam. | Desl. | Teclas | Visor previsto | Linhas previstas (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3d-70 | DEC | QWORD | Arit | `1` `Lsh` `4` `=` | `16` | — | `1 Lsh 4 =` | igual | não | O | d§3.5 |
| 3d-71 | DEC | QWORD | Arit | `1` `Lsh` `63` `=` | `-9.223.372.036.854.775.808` | — | — | `9.223.372.036.854.775.808` | sim | O | d§3.5 |
| 3d-72 | DEC | QWORD | Arit | `1` `Lsh` `64` `=` | `Resultado não definido` | — | — | `18.446.744.073.709.551.616` | sim | O | d§3.5 |
| 3d-73 | DEC | QWORD | Arit | `7` `±` `Rsh` `1` `=` | `-4` | — | `-7 Rsh 1 =` | `-3,5` | sim | O | d§3.5 |
| 3d-74 | DEC | QWORD | Arit | `16` `±` `Rsh` `2` `=` | `-4` | — | — | `-4` | não | O | d§3.5 |
| 3d-75 | DEC | BYTE | Arit | `3` `Lsh` `7` `=` | `-128` | — | — | `384` | sim | O | d§3.5 |
| 3d-76 | DEC | BYTE | Arit | `1` `Lsh` `8` `=` | `Resultado não definido` | — | — | `256` | sim | O | d§3.5 |
| 3d-77 | HEX | BYTE | Arit | `80` `Rsh` `1` `=` | `C0` | D `-64` | — | `40` (D `64`) | sim | O | d§3.5 |
| 3d-78 | DEC | QWORD | Arit | `8` `Rsh` `64` `=` | `Resultado não definido` | — | — | `0` | sim | O | d§3.5 |
| 3d-79 | DEC | QWORD | Arit | `1` `+` `1` `Lsh` `2` `=` | `5` | — | `1 + 1 Lsh 2 =` | `8` (esq.→dir.) | sim | O | d§3.5, c§3.11 |
| 3d-80 | DEC | QWORD | Arit | `8` `Lsh` `1` `±` `=` | `Resultado não definido` | — | — | `4` | sim | O | d§3.5 |
| 3d-81 | DEC | QWORD | Lóg | `1` `±` `Rsh` `1` `=` | `9.223.372.036.854.775.807` | — | `-1 Rsh 1 =` | `-0,5` | sim | O | d§3.5 |
| 3d-82 | DEC | QWORD | Lóg | `16` `±` `Rsh` `60` `=` | `15` | — | — | `≈ -1,4·10⁻¹⁷` | sim | O | d§3.5 |
| 3d-83 | HEX | BYTE | Lóg | `80` `Rsh` `1` `=` | `40` | D `64` | — | `40` | não | O | d§3.5 |
| 3d-84 | DEC | QWORD | Lóg | `1` `Lsh` `63` `=` | `-9.223.372.036.854.775.808` | — | — | `9.223.372.036.854.775.808` | sim | O | d§3.5 |
| 3d-85 | DEC | BYTE | Lóg | `5` `Rsh` `8` `=` | `Resultado não definido` | — | — | `0` | sim | O | d§3.5 |
| 3d-86 | HEX | BYTE | Circ | `81` `Rol` → `Ror` | `3` → `81` | D `-127` | `RoR( RoL( 81 ) )` | igual no visor | sim (D) | O | d§3.5 |
| 3d-87 | DEC | QWORD | Circ | `1` `Ror` | `-9.223.372.036.854.775.808` | H `8000 0000 0000 0000` | `RoR( 1 )` | igual | não | O | d§3.5 |
| 3d-88 | DEC | BYTE | Circ | `1` `Ror` | `-128` | H `80` | — | `128` | sim | O | d§3.5 |
| 3d-89 | HEX | QWORD | Circ | `8000000000000000` `Rol` | `1` | — | — | igual | não | O | d§3.5 |
| 3d-90 | HEX | BYTE | Carry | `80` `RolC` → `RolC` → `RolC` | `0` → `1` → `2` | — | — | `1` → `2` → `4` | sim | O | d§3.5 |
| 3d-91 | HEX | BYTE | Carry | `1` `RorC` → `RorC` → `RorC` | `0` → `80` → `40` | — | — | `80` → `40` → `20` | sim | O | d§3.5 |
| 3d-92 | HEX | BYTE | Carry | `80` `RolC` → `5` `RolC` | `0` → `B` | — | — | `0` → `A` | sim | O | d§3.5 |
| 3d-93 | HEX | BYTE | Carry | `80` `RolC` → `C` `5` `RolC` | `0` → `A` | — | — | `0` → `A` | não | O | d§3.5 |

## F. Teclado de bits

Antes de cada caso deste bloco: o teclado de bits (`bitFlip`) ligado, depois de C, da base e do tamanho.

| ID | Base | Tam. | Teclas | Visor previsto | Linhas / bits previstos (final) | Expressão | MP | Discr. | O/I | Base |
|---|---|---|---|---|---|---|---|---|---|---|
| 3d-100 | DEC | QWORD | `[bit0]` → `[bit3]` | `1` → `9` | H `9` · bits {0, 3} | — | igual | não | O | d§3.7 |
| 3d-101 | DEC | QWORD | `[bit63]` | `-9.223.372.036.854.775.808` | H `8000 0000 0000 0000` · bits {63} | — | `9.223.372.036.854.775.808` | sim | O | d§3.7 |
| 3d-102 | DEC | BYTE | `[bit7]` | `-128` | H `80` · bits {7} | — | `128` | sim | O | d§3.7 |
| 3d-103 | DEC | QWORD | `5` → `[bit2]` | `5` → `1` | bits {0} | — | igual | não | O | d§3.7 |
| 3d-104 | DEC | QWORD | `5` `+` `[bit0]` → `=` | `4` → `9` | — | — | `1` → `6` (bit num operando novo) | sim | O | d§3.7 |
| 3d-105 | DEC | QWORD | `12` `[bit0]` → `4` | `13` → `4` | — | — | `13` → `134` (continua o número) | sim | O | d§3.7 |
| 3d-106 | DEC | QWORD | `1` `±` `[bit63]` | `9.223.372.036.854.775.807` | H `7FFF FFFF FFFF FFFF` | — | `-1 XOR 2^63` sem largura | sim | O | d§3.7 |
| 3d-107 | HEX | QWORD | `[bit4]` `[bit0]` | `11` | D `17` | — | igual | não | O | d§3.7 |

## Observações

- **3d-23** é o único caso cujo resultado final depende do sentido do botão de tamanho (L27). Nos outros do bloco B o
  resultado final é o mesmo nos dois sentidos (d§3.2: vale o valor com sinal da menor largura visitada). A automação
  registra o caminho percorrido.
- **3d-42/43/44** contrastam com o Científico (3c-16, 3c-17, 3c-19): a mesma conta com o mesmo botão Mod dá outro resultado
  porque o modo inteiro segue outro ramo de `DoOperation`.
- **3d-61 e 3d-104**: a unária e o bit agem sobre o acumulador logo depois de um operador (regra da 3a para unárias).
- **3d-80**: o deslocamento negativo é truncado para 2^64 − 1 antes do teste n < largura.
- **3d-92/93**: o carry é do motor. Um número novo não o apaga (3d-92), e C apaga (3d-93).
