# 03b — Casos de teste da Fase 3b (histórico e memória)

Versão 1 (2026-10-22). Previsões tiradas só de `relatorio/02-features/b-historico-memoria.md` (seção na coluna "Base",
com prefixo `b`) e de `a-operacoes-basicas.md` (prefixo `a`). Este arquivo é congelado por SHA-256 em
`hashes-originais.txt` **antes** da execução, e as colunas de previsão não mudam depois. Os resultados e a comparação
ficam em `02-features/b-historico-memoria.md`, seção de resultados.

## Como executar

**Ambiente e estado inicial**
- Calculadora 11.2607.0.0 com Windows e formato regional em pt-BR (vírgula decimal, ponto de milhar), como na Fase 4.
- **Antes de cada caso**, comece de um estado conhecido:
  1. memória vazia (MC, se estiver habilitado);
  2. histórico vazio nos modos Padrão **e** Científico ("Limpar todo o histórico" no submenu de histórico de cada modo);
  3. modo da coluna "Modo";
  4. C.
- A automação (`trabalho/automacao/rodar-casos.ps1 -Etapa Casos3b`) faz isso sozinha.

**Notação** (além da de `03-casos-de-teste.md`)

| Notação | Botão / ação (nome pt-BR) |
|---|---|
| `MS` | Armazenamento de memória |
| `MR` | Rechamada de memória |
| `M+` / `M−` | Adição de memória / Subtração de memória |
| `MC` | Limpar toda a memória |
| `LH` | abrir o submenu de histórico e clicar em "Limpar todo o histórico" |
| `[Alt+1]` / `[Alt+2]` | trocar para Padrão / Científica (atalho do teclado) |
| `→` | ponto de leitura intermediário |

**O que anotar em cada leitura**
- visor;
- linha de expressão;
- **histórico**: os itens do submenu de histórico, de cima para baixo. Nas tabelas, cada item é `[expressão | resultado]`, e `;` separa os itens. Se estiver vazio,
  anote o texto mostrado;
- **memória**: os valores do submenu de memória, de cima para baixo. Se M▾ estiver desabilitado, anote "vazia, M▾
  desabilitado";
- quando a coluna pedir, o estado (habilitado/desabilitado) de MC, MR, M+, M−, MS e M▾.

**Comparação**
- O visor e os valores da memória são comparados exatamente.
- Expressões (linha e histórico) são comparadas **ignorando espaços**, pelo mesmo motivo da L20.
- O texto bruto que o motor grava para o histórico tem espaçamento próprio (02b §4.2): por exemplo `"7   +   5 ="` e
  `"√( 9 )"`. Ele é previsto na coluna "Observações", mas fica fora da taxa.

**Classificação**
- **A**: alguma previsão depende de inferência além da ligação VM → tela. O detalhe vai entre parênteses.
- **B** (histórico) e **C** (memória): motor e VM lidos [O]. Só a exibição da lista pela ligação XAML/C# é [I] (L3),
  e isso vale para todos os casos.

**Previsões gerais [O]**
- Histórico vazio mostra `Ainda não há histórico.` (`HistoryEmpty/Text` pt-BR). As previsões escrevem `(vazia)`.
- Memória vazia: MC, MR e M▾ desabilitados (já observado na Fase 4). As previsões escrevem `(vazia)`.

## A. Alguma previsão INFERIDA

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Expressão prevista | Histórico previsto (topo → base) | Memória prevista (topo → base) | O/I | Base |
|---|---|---|---|---|---|---|---|---|
| 3b-09 | Padrão | `7` `+` `5` `=` → `[Alt+2]` → `1` `+` `1` `=` → `[Alt+1]` | `12` → `0` → `2` → `0` | `7 + 5 =` → (vazia) → `1 + 1 =` → (vazia) | `[7 + 5 = \| 12]` → **(vazia)** → `[1 + 1 = \| 2]` → **`[7 + 5 = \| 12]`** | (vazia) em todas | INFERIDO (a lista é recarregada na troca de modo, b§4.4/L21; visor 0 após a troca) | b§4.4, a§3.2 |
| 3b-11 | Padrão | `7` `MS` | `7` | (vazia) | (vazia) | `7`; **MC, MR e M▾ habilitados** | INFERIDO (IsEnabled ← IsMemoryEmpty, b§3.4) | b§3.2, b§3.4 |
| 3b-18 | Padrão | `7` `MS` → `MC` | `7` → `7` | (vazia) | (vazia) | `7` → (vazia); **MC, MR e M▾ desabilitados** | INFERIDO (IsEnabled, b§3.4) | b§3.2, b§3.3 |
| 3b-19 | Padrão | `1` `÷` `3` `=` `MS` `C` `MR` → `×` `3` `=` | `0,3333333333333333` → **`1`** | (vazia) → `0,3333333333333333 × 3 =` | `[1 ÷ 3 = \| 0,3333333333333333]` → `[0,3333333333333333 × 3 = \| 1]`; `[1 ÷ 3 = \| 0,3333333333333333]` | `0,3333333333333333` | INFERIDO (o `1` depende da aritmética racional, Fase 3f; a cópia exata é O, b§3.1) | b§3.1, b§3.2 |
| 3b-25 | Padrão | `7` `MS` → `[Alt+2]` → `MR` | `7` → `0` → `7` | (vazia) | (vazia) | `7` → `7` → `7` | INFERIDO (a lista da memória continua na tela após a troca, b§4.4) | b§4.4 |
| 3b-26 | Padrão | `7` `MS` `8` `÷` `0` `=` → `C` `MR` | Não é possível dividir por zero → `7` | `8 ÷` → (vazia) | (vazia) | `7`; em erro **M+, M− e MS desabilitados, MC e MR habilitados** → `7` | INFERIDO (MC/MR habilitados em erro, b§3.4) | b§3.3, b§4.1, a§4.4 |

## B. Histórico (motor e VM OBSERVADOS)

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Expressão prevista | Histórico previsto (topo → base) | Memória prevista | O/I | Base |
|---|---|---|---|---|---|---|---|---|
| 3b-01 | Padrão | `7` `+` `5` `=` | `12` | `7 + 5 =` | `[7 + 5 = \| 12]` | (vazia) | OBSERVADO | b§4.1 H1 |
| 3b-02 | Padrão | `2` `+` `3` `×` → `4` `=` | `5` → `20` | `5 ×` → `5 × 4 =` | `[2 + 3 = \| 5]` → `[5 × 4 = \| 20]`; `[2 + 3 = \| 5]` | (vazia) | OBSERVADO (previsão da 3a-02: dois itens) | b§4.1 H2, a§3.3 |
| 3b-02c | **Científico** | `2` `+` `3` `×` → `4` `=` | `3` → `14` | `2 + 3 ×` → `2 + 3 × 4 =` | (vazia) → `[2 + 3 × 4 = \| 14]` | (vazia) | OBSERVADO | b§4.1 (H2 só no Padrão) |
| 3b-03 | Padrão | `2` `+` `3` `=` → `=` | `5` → `8` | `2 + 3 =` → `5 + 3 =` | `[2 + 3 = \| 5]` → `[5 + 3 = \| 8]`; `[2 + 3 = \| 5]` | (vazia) | OBSERVADO | b§4.1 |
| 3b-04 | Padrão | `5` `=` → `=` | `5` → `5` | `5 =` → `5 =` | `[5 = \| 5]` → `[5 = \| 5]`; `[5 = \| 5]` | (vazia) | OBSERVADO | b§4.1 |
| 3b-05 | Padrão | `8` `÷` `0` `=` → `C` `1` `+` `1` `=` | Não é possível dividir por zero → `2` | `8 ÷` → `1 + 1 =` | (vazia) → `[1 + 1 = \| 2]` | (vazia) | OBSERVADO | b§4.1 |
| 3b-06 | Padrão | `9` `√` → `5` | `3` → `5` | `√( 9 )` → (não prevista) | (vazia) → **`[√( 9 ) \| 3]`** (sem `=`) | (vazia) | OBSERVADO | b§4.1 H3 |
| 3b-07 | Padrão | `9` `√` `=` | `3` | `√( 9 ) =` | `[√( 9 ) = \| 3]` | (vazia) | OBSERVADO | b§4.1 H1 |
| 3b-08 | Padrão | `1` `+` `1` `=`, depois `=` vinte vezes | `22` | `21 + 1 =` | **20 itens**: topo `[21 + 1 = \| 22]`; base `[2 + 1 = \| 3]` (`[1 + 1 = \| 2]` saiu) | (vazia) | OBSERVADO | b§4.3 |
| 3b-10 | Padrão | `1` `+` `1` `=` → `LH` | `2` → `2` | `1 + 1 =` → `1 + 1 =` (inalterada) | `[1 + 1 = \| 2]` → (vazia) | (vazia) | OBSERVADO | b§4.3 |

## C. Memória (motor e VM OBSERVADOS)

| ID | Modo | Teclas exatas, em ordem | Visor previsto | Expressão prevista | Histórico previsto | Memória prevista (topo → base) | O/I | Base |
|---|---|---|---|---|---|---|---|---|
| 3b-12 | Padrão | `7` `MS` `3` `MS` | `3` | (vazia) | (vazia) | `3`; `7` | OBSERVADO | b§3.2 |
| 3b-13 | Padrão | `7` `MS` `3` `M+` | `3` | (vazia) | (vazia) | `10` | OBSERVADO | b§3.3 |
| 3b-14 | Padrão | `7` `MS` `3` `M−` | `3` | (vazia) | (vazia) | `4` | OBSERVADO | b§3.2 |
| 3b-15 | Padrão | `5` `M+` (memória vazia) | `5` | (vazia) | (vazia) | `5` | OBSERVADO | b§3.3 |
| 3b-16 | Padrão | `5` `M−` (memória vazia) | `5` | (vazia) | (vazia) | **`-5`** | OBSERVADO | b§3.2 |
| 3b-17 | Padrão | `7` `MS` `3` `MS` `C` `MR` | `3` | (vazia) | (vazia) | `3`; `7` | OBSERVADO | b§3.3 (MR = posição 0) |
| 3b-20 | Padrão | `1` `2` `3` `4` `MS` | `1.234` | (vazia) | (vazia) | `1.234` | OBSERVADO | b§3.2 |
| 3b-21 | Padrão | `2` `+` `3` `=` → `MS` | `5` → `5` | `2 + 3 =` → **(vazia)** | `[2 + 3 = \| 5]` → `[2 + 3 = \| 5]` | (vazia) → `5` | OBSERVADO | b§3.1, a§3.6 |
| 3b-22 | Padrão | `7` `MS` `C` `5` `+` `MR` `=` | `12` | `5 + 7 =` | `[5 + 7 = \| 12]` | `7` | OBSERVADO | b§3.3, b§4.1 |
| 3b-23 | Padrão | `7` `MS` `C` `9` `√` `MR` | `7` | (não prevista) | **`[√( 9 ) \| 3]`** (sem `=`) | `7` | OBSERVADO | b§4.1 H4 |
| 3b-24 | Padrão | `7` `MS` `C` `2` `+` `3` `M+` → `=` | `3` → `5` | `2 +` → `2 + 3 =` | (vazia) → `[2 + 3 = \| 5]` | `10` → `10` | OBSERVADO | b§3.1 (finaliza a digitação) |

## Observações

- **Texto bruto do histórico** [O, b§4.2], fora da taxa: os binários levam três espaços em volta do operador e um antes
  do `=`, por exemplo `"7   +   5 ="` e `"2   +   3 ="`. As unárias levam um espaço dentro dos parênteses: `"√( 9 )"` e
  `"√( 9 ) ="`.
- **3b-02**: é a previsão "dois itens no histórico" pedida desde a §3.3 da 3a.
- **3b-08**: a lista pode estar virtualizada. Se o item da base não for alcançável, anote só o topo e a contagem.
- **3b-09 e 3b-25**: a troca de modo manda C para a engine (01 §6.6). Por isso o visor previsto após a troca é `0`.
- **3b-19**: a linha de expressão após `MR` está vazia porque o comando seguinte a `=` a apaga (a§3.6).
- **3b-26**: o estado previsto dos botões em erro vale para quando há memória. A Fase 4 observou MC e MR desabilitados em
  erro com a memória vazia.
