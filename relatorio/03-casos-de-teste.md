# 03 — Casos de teste para execução manual

Versão 1 (2026-10-22), cobrindo só a **Fase 3a**: operações básicas e divisão por zero. Origem das
previsões: `relatorio/02-features/a-operacoes-basicas.md`, com a seção de cada caso indicada na coluna
"Base".

## Como executar

**Ambiente**
- Calculadora 11.2607.0.0, com o Windows exibindo em **Português (Brasil)**.
- Formato regional **Português (Brasil)**: vírgula decimal e ponto de milhar. As previsões usam esse formato.
- Se o formato regional for outro, anote qual é, porque ele muda os separadores (02a §5).

**Modo**
- Padrão, salvo quando a coluna "Modo" disser Científico.
- Troque o modo pelo menu ☰ antes do caso.

**Teclas**
- Clique nos botões da tela. Para dígitos, o teclado numérico também serve.
- "**C** (Limpar antes)" significa apertar C antes da sequência, porque o caso depende do estado zerado.
- `→` separa leituras intermediárias: anote o visor em cada ponto marcado.

**O que anotar em "Real"**
- O texto exato do **visor** (número grande).
- Se possível, a **linha de expressão**, que é a linha pequena acima do visor, separada por `|`.
- Se algo não acontecer (botão desabilitado, nada muda), escreva isso.

**Notação dos botões**

| Notação | Botão (nome de acessibilidade pt-BR) |
|---|---|
| `C` | Limpar |
| `CE` | Limpar entrada |
| `⌫` | Backspace |
| `±` | Positivo negativo |
| `,` | Separador decimal |
| `÷ × − +` | Dividir por, Multiplicar por, Menos, Mais |
| `=` | Igual a |
| `%` | Por cento |
| `√` | Raiz quadrada (botão `²√x`) |
| `x²` | Quadrado |
| `1/x` | Recíproco (botão `¹/x`) |

Classificação: **INFERIDO** quando alguma das previsões da linha (visor ou expressão) depende de inferência;
o detalhe vai entre parênteses. **OBSERVADO** quando tudo saiu do código lido. Os casos inferidos vêm
primeiro.

## A. Visor INFERIDO (arredondamento, formato, agrupamento, domínio)

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Linha de expressão prevista | O/I | Base | Real |
|---|---|---|---|---|---|---|---|
| 3a-18 | Padrão | **C** (Limpar antes), `1` `÷` `3` `=` | `0,3333333333333333` (16 dígitos "3") | `1 ÷ 3 =` | INFERIDO (visor e expressão) | §5, L16 | |
| 3a-19 | Padrão | **C** (Limpar antes), `2` `÷` `3` `=` | `0,6666666666666667` (15 "6" e um "7" final) | `2 ÷ 3 =` | INFERIDO (visor e expressão) | §5, L16 | |
| 3a-22 | Padrão | **C** (Limpar antes), `1` `÷` `3` `0` `0` `0` `=` | `3,333333333333333e-4` | `1 ÷ 3000 =` | INFERIDO (visor e expressão) | §5, L16 | |
| 3a-21 | Padrão | **C** (Limpar antes), `9` dezesseis vezes, `+` `1` `=` | `1,e+16` (com a vírgula antes do `e`) | `9999999999999999 + 1 =` (talvez com pontos de milhar) | INFERIDO (visor e expressão) | §5 | |
| 3a-20 | Padrão | **C** (Limpar antes), `1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7` (17 dígitos) | `1.234.567.890.123.456`. O 17º dígito (`7`) é ignorado e o visor não muda | (vazia) | INFERIDO (agrupamento); o limite de 16 dígitos é OBSERVADO | §3.1, §5 | |
| 3a-08 | Padrão | **C** (Limpar antes), `4` `±` `√` | **Entrada inválida** | `√(-4)` | INFERIDO (visor e expressão) | §3.5, §4.2 | |
| 3a-26 | Padrão | **C** (Limpar antes), `9` dezesseis vezes, depois `x²` dez vezes | 1º `x²` → `9,999999999999998e+31`; os expoentes crescem (≈ +63, +127 … +8191 no 9º); 10º `x²` → **Estouro** | (não prevista) | INFERIDO (visor) | §4.1, §4.2 | |

## B. Visor OBSERVADO, linha de expressão INFERIDA

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Linha de expressão prevista | O/I | Base | Real |
|---|---|---|---|---|---|---|---|
| 3a-01 | Padrão | **C** (Limpar antes), `7` `+` `5` `=` | `12` | `7 + 5 =` | INFERIDO (expressão); visor OBSERVADO | §3.3, §3.4 | |
| 3a-02 | Padrão | **C** (Limpar antes), `2` `+` `3` `×` → `4` `=` | no `×`: `5` → no `=`: `20` | `2 + 3 × 4 =` | INFERIDO (expressão); visor OBSERVADO | §3.3 | |
| 3a-02c | **Científico** | **C** (Limpar antes), `2` `+` `3` `×` → `4` `=` | no `×`: `3` → no `=`: `14` | `2 + 3 × 4 =` | INFERIDO (expressão e visor intermediário); visor final OBSERVADO | §3.3 | |
| 3a-03 | Padrão | **C** (Limpar antes), `9` `−` `1` `2` `=` | `-3` | `9 - 12 =` (sinal de menos como hífen, chave 14) | INFERIDO (expressão); visor OBSERVADO | §3.3, §6 | |
| 3a-04 | Padrão | **C** (Limpar antes), `8` `÷` `0` `=` | **Não é possível dividir por zero** | `8 ÷` | INFERIDO (expressão); visor OBSERVADO | §4.3 | |
| 3a-05 | Padrão | **C** (Limpar antes), `0` `÷` `0` `=` | **Resultado indefinido** | `0 ÷` | INFERIDO (expressão); visor OBSERVADO | §4.2 | |
| 3a-06 | Padrão | **C** (Limpar antes), `÷` `0` `=` | **Resultado indefinido** | `0 ÷` | INFERIDO (expressão); visor OBSERVADO | §4.2, B3 | |
| 3a-07 | Padrão | **C** (Limpar antes), `0` `1/x` | **Não é possível dividir por zero** | `1/(0)` | INFERIDO (expressão); visor OBSERVADO | §3.5, §4.3 | |
| 3a-10 | Padrão | **C** (Limpar antes), `8` `÷` `0` `=` → `CE` | no `=`: Não é possível dividir por zero → no `CE`: `0` | após `CE`: provavelmente ainda `8 ÷` | INFERIDO (expressão); visor OBSERVADO | §4.4 | |
| 3a-11 | Padrão | **C** (Limpar antes), `2` `+` `3` `=` → `=` | `5` → `8` | `2 + 3 =` → `5 + 3 =` | INFERIDO (expressão); visor OBSERVADO | §3.4 | |
| 3a-12 | Padrão | **C** (Limpar antes), `2` `+` `3` `=` → `4` `=` | `5` → `7` | `2 + 3 =` → `4 + 3 =` | INFERIDO (expressão); visor OBSERVADO | §3.4 | |
| 3a-13 | Padrão | **C** (Limpar antes), `5` `×` `=` | `25` | `5 × 5 =` | INFERIDO (expressão); visor OBSERVADO | §3.4 | |
| 3a-14 | Padrão | **C** (Limpar antes), `5` `+` `×` `3` `=` | `15` | `5 × 3 =` (o `+` foi trocado) | INFERIDO (expressão); visor OBSERVADO | §3.3 | |
| 3a-15 | Padrão | **C** (Limpar antes), `5` `0` `+` `1` `0` `%` → `=` | `5` → `55` | `50 + 5` → `50 + 5 =` | INFERIDO (expressão); visor OBSERVADO | §3.5 | |
| 3a-16 | Padrão | **C** (Limpar antes), `5` `0` `×` `1` `0` `%` → `=` | `0,1` → `5` | `50 × 0,1` → `50 × 0,1 =` | INFERIDO (expressão); visor OBSERVADO | §3.5 | |
| 3a-17 | Padrão | **C** (Limpar antes), `1` `0` `%` | `0` | `0` | INFERIDO (expressão); visor OBSERVADO | §3.5 | |
| 3a-24 | Padrão | **C** (Limpar antes), `2` `+` `3` `=` → `⌫` | `5` → `5` (⌫ não faz nada) | `2 + 3 =` (inalterada) | INFERIDO (expressão); visor OBSERVADO | §3.1, B14 | |
| 3a-27 | Padrão | **C** (Limpar antes), `9` `√` | `3` | `√(9)` | INFERIDO (expressão); visor OBSERVADO | §3.5 | |
| 3a-28 | Padrão | **C** (Limpar antes), `3` `x²` → **C**, `4` `1/x` | `9` → `0,25` | `sqr(3)` → `1/(4)` | INFERIDO (expressão); visor OBSERVADO | §3.5, §7.3 | |
| 3a-29 | Padrão | **C** (Limpar antes), `5` `+` `3` `CE` `2` `=` | `7` | `5 + 2 =` | INFERIDO (expressão); visor OBSERVADO | §3.2 | |

## C. Totalmente OBSERVADO

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Linha de expressão prevista | O/I | Base | Real |
|---|---|---|---|---|---|---|---|
| 3a-09 | Padrão | **C** (Limpar antes), `8` `÷` `0` `=` → `+` → `5` | Não é possível dividir por zero → (o `+` não muda nada) → `5` | após o `5`: vazia | OBSERVADO | §4.4 | |
| 3a-23 | Padrão | **C** (Limpar antes), `0` `0` `0` → `,` → `⌫` | `0` → `0,` → `0` | (vazia) | OBSERVADO | §3.1 | |
| 3a-25 | Padrão | **C** (Limpar antes), `0` `±` → **C**, `5` `±` | `0` → `-5` | (vazia) | OBSERVADO | §3.1 | |

## Observações

- **3a-20.** Ao ignorar o 17º dígito, a Calculadora só faz um anúncio para o Narrador ("Nº máximo de
  dígitos alcançado"). Na tela nada muda.
- **3a-26.** Os valores intermediários servem só de referência; o que interessa é em qual `x²` aparece
  "Estouro". Se demorar ou travar, anote.
- **3a-04 a 3a-10.** Se aparecer outro texto de erro, copie-o literalmente. Ele identifica qual chave de
  `CEngineStrings` foi usada: 99, 100 e 101 têm textos diferentes.

## Resultados devolvidos

(aguardando a coluna "Real")
