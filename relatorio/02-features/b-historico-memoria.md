# 02b — Histórico e memória (Fase 3b)

Alvo: `CalcViewModel.dll` (SHA-256 `072cd589…d21d`), 11.2607.0.0 x64. A análise é só estática (REA 6.7.0 /
Ghidra 12.1.4) e foi feita antes de qualquer execução desta fase. Data: 2026-10-22.

Convenção: **[O]** OBSERVADO, lido de pseudocódigo, assembly ou bytes, com endereço. **[I]** INFERIDO, com o
raciocínio indicado. Os nomes de função (`MemorizeNumber`, `AddToHistory`…) são **rótulos** desta análise (L1).
`motor+0xNNN` é um offset na engine (0x11a8 bytes); `CM+0xNN` é um offset no `CalculatorManager` (= VM+0x178).

Evidência REA: `trabalho/fase3b-evidencias.json`. Os registros desta fase são `ev_aaacf983…`, `ev_664e490c…`,
`ev_7ec668fa…`, `ev_644572fa…` (decompilação) e `ev_a24b8693…` (bytes de 0x18017cb10). O pseudocódigo está em
`trabalho/pseudocodigo/<endereço>.c`, indexado em `INDICE.tsv` ("Fase 3b"). Funções já lidas nas fases 2 e 3a
(`0x180112db0`, `0x1800d6bf0`, `0x1800d7350`, `0x1800d76b0`, `0x1800d7ac0`, `0x1800d4b70`, `0x1800b5780`,
`0x18010cdf0`, `0x18010d0e0`, `0x18010f200`, `0x18010ec10`) foram relidas a partir dos arquivos salvos.

## Resumo

| Pergunta | Resposta curta |
|---|---|
| Onde mora o estado | **Motor** (`CalculatorManager`): memória = `vector` de racionais em CM+0x40/+0x48; histórico = 2 objetos `CalculatorHistory` (Padrão CM+0xa0, Científico CM+0xb0), atual em CM+0xc0 [O] |
| Quem grava um item de histórico | o coletor de expressão do motor (`FUN_18010fb30`, motor+0xf70), chamado por `=`, pelo `=` implícito do Padrão e por dígito/MR logo após uma unária [O] |
| Limites | histórico: **20** itens por modo (constante 0x14 em `0x18010cdf0`); o mais antigo sai [O]. Memória: **100** itens (`FUN_18010dd40`) [O] |
| Ordem | as duas listas mostram o **mais novo em cima** (histórico `InsertAt(0)`; memória `insert(begin)`) [O] |
| Precisão da memória | MS guarda o **racional completo** do valor atual, não o texto do visor (`FUN_18012b790` só copia fora do modo inteiro) [O] |
| M+/M− sem memória | M+ = MS. M− grava **−x** (MS seguido de duas subtrações de x) [O] |
| MR | carrega o item 0 no registrador do motor (motor+0xd8) e copia para o valor atual [O] |
| Modos | a memória é única (fica no `CalculatorManager`, a troca de modo não a toca) [O]; o histórico é separado por modo [O] |

## 1. Cadeia de chamadas

### 1.1 Memória
```
XAML Calculator.xbf (01 §7.3, xbf-botoes.tsv):
  memButton  (MS)  ButtonId=Memory(146) ──► OnButtonPressed 0x1800d5aa0 ──► OnMemoryButtonPressed 0x1800d6bf0
  MemRecall  (MR)  CommandParameter={StaticResource Zero} ──► MemoryItemPressed ──► OnMemoryItemPressed 0x1800d7350 (pos 0)
  MemPlus    (M+)  CommandParameter=Zero ──► MemoryAdd      ──► OnMemoryAdd      0x1800d76b0 (pos 0)
  MemMinus   (M−)  CommandParameter=Zero ──► MemorySubtract ──► OnMemorySubtract 0x1800d78f0 (pos 0)
  ClearMemoryButton (MC) ──► ClearMemoryCommand (get 0x1800d1640, handler 0x1800d6680)
  itens da lista (MemoryListItem.xbf): MemoryItemViewModel.Clear/MemoryAdd/MemorySubtract
        0x1800bb290 / 0x1800bb320 / 0x1800bb3b0 ──► OnMemoryClear 0x1800d7ac0 / OnMemoryAdd / OnMemorySubtract (pos do item)
VM ──► CalculatorManager (VM+0x178):
  MemorizeNumber 0x18010d760 · MemorizedNumberLoad 0x18010d9b0 · MemorizedNumberSubtract 0x18010d8c0
  MemorizedNumberChanged 0x18010dab0 · MemorizedNumberClear 0x18010d810 · MemorizedNumberClearAll 0x18010d940
  SetMemorizedNumbersString 0x18010dbe0 ──► ICalcDisplay slot 8 ──► VM SetMemorizedNumbers 0x1800d4b70
  ──► engine::ProcessCommand 0x180112db0 com 122 (MC), 123 (MR), 124 (MS), 125 (M+), 126 (M−)
```
[O] A ligação MR/M+/M− → comando com parâmetro `Zero` vem do XBF, com a ressalva da L12 (pareamento heurístico).
Os comandos `MemoryItemPressed`/`MemoryAdd`/`MemorySubtract` são propriedades `ICommand` do VM (winmd). A ligação
`Command=` → propriedade está no C# compilado (L3) e é [I].

### 1.2 Histórico
```
engine::ProcessCommand ──► coletor motor+0xf70 ──► FUN_18010fb30 (finaliza)
   ├─ coletor[0] slot 1 = CalculatorHistory::AddToHistory 0x180128130 (tokens, comandos, texto do resultado) → índice
   └─ coletor[2] slot 7 (+0x38) = CalculatorManager → ICalcDisplay slot 7 → CalculatorDisplay
        → HistoryViewModel::OnHistoryItemAdded 0x1800b5780 (índice) → HistoryItemViewModel ctor 0x1800b48d0
UI: HistoryButton → HistoryFlyout (HistoryList.xbf): HistoryListView, HistoryEmpty, ClearHistory
   ClearHistory ──► HistoryViewModel.ClearCommand ──► OnClearCommand 0x1800b65a0
   item ──► ShowItem 0x1800b5e60 ──► evento HistoryItemClicked ──► (C#) SelectHistoryItem 0x1800db3d0  [I na ligação]
troca de modo ──► ReloadHistory 0x1800b53d0(ViewMode)  [chamador no C#, I]
```

## 2. Estruturas de dados [O]

| Onde | Conteúdo | Evidência |
|---|---|---|
| CM+0x40 / +0x48 / +0x50 | `vector<Rational>` da memória (begin/end/cap), elemento de 0x40 bytes (= o racional da 3a) | `>> 6` em 0x18010d760, 0x18010d810 |
| CM+0xa0/+0xa8 | `shared_ptr<CalculatorHistory>` do Padrão | `0x18010cdf0`; `SetStandardMode` 0x18010d0e0 faz CM+0xc0 = CM+0xa0 |
| CM+0xb0/+0xb8 | `shared_ptr<CalculatorHistory>` do Científico | `0x18010cdf0`; `ReloadHistory` usa +0xb0 quando o modo é 1 |
| CM+0xc0 | histórico atual | `OnHistoryItemAdded`, `OnClearCommand` |
| `CalculatorHistory` +0x08/+0x10/+0x18 | `vector<shared_ptr<HISTORYITEM>>` (16 bytes por item) | `0x180128130` |
| `CalculatorHistory` +0x20 | **máximo de itens = 0x14 (20)** | `puVar1[4] = 0x14` em `0x18010cdf0` (as duas instâncias) |
| `HISTORYITEM` (0x60 bytes) | +0x00 `shared_ptr` tokens; +0x10 `shared_ptr` comandos; +0x20 `wstring` expressão; +0x40 `wstring` resultado | `0x180128130` (`_Ref_count_obj2<CalculationManager::HISTORYITEM>`), `0x1800b5780` lê +0x20 e +0x40 |
| motor+0xd8 | ponteiro para um racional: **registrador de memória** da engine (operando de MR/M+/M−) | casos 0x7a–0x7e de `0x180112db0`; `FUN_180112410` |
| motor+0x22 | `bool` testado por MR: se 1, MR não copia o registrador, só zera o flag | `case 0x7b` |
| motor+0xf8c | índice do operando corrente no coletor (−1 = nenhum) | `FUN_18010ec10` zera; operando novo grava; `FUN_18010fb30` → `FUN_18010e840` zera |
| VM `MemorizedNumbers` (vslot 0x3d8) | `IVector<MemoryItemViewModel>` (Value, Position) | `0x1800d4b70` |
| `HistoryViewModel` +0x78 (param_1[0xf]) | `CalculatorManager*`; +0x98 (param_1[0x13]) modo atual (0/1) | ctor 0x1800b5270, `ReloadHistory` |
| `HistoryItemViewModel` | +0x20 Expression, +0x38 Result, +0x28 AccExpression (de tokens, `FUN_1800b4a70`), +0x30 AccResult (`FUN_18004ea00`), +0x40/+0x50 tokens e comandos | ctor 0x1800b48d0 |

## 3. Regras da memória

### 3.1 Comandos da engine (`ProcessCommand` 0x180112db0) [O]
Antes do despacho (início de `ProcessCommand`):
- se motor+0x21 (digitando) e o comando é 0x77–0x7e (entre outros): o texto digitado é **finalizado** (`FUN_180121d50`)
  e vira o valor atual. Logo, MS/M+/M− durante a digitação usam o número digitado;
- se motor+0xe22 == 0 (o comando anterior foi `=`): `FUN_180112c40` **limpa a linha de expressão** (3a §3.6). Isso
  vale para MC, MR, MS, M+ e M−;
- em erro (motor+0xe20), tudo é descartado, exceto C.

| Código | Botão | Efeito |
|---:|---|---|
| 124 (0x7c) | MS | motor+0xd8 = `FUN_18012b790(atual)`. Fora do modo inteiro (motor+0x01 = 0) é **cópia exata** do racional [O] |
| 122 (0x7a) | MC | motor+0xd8 = 0 (`FUN_180126760(…, 0)`) |
| 123 (0x7b) | MR | se motor+0x22 == 0: atual = *motor+0xd8; se não, zera +0x22. Depois trata o coletor (§4.3) e chama `DisplayNum` |
| 125 (0x7d) | M+ | motor+0xd8 = `FUN_18012b790(*motor+0xd8 + atual)` (`FUN_1801278b0`) |
| 126 (0x7e) | M− | motor+0xd8 = `FUN_18012b790(*motor+0xd8 − atual)` (`FUN_180127980`) |

Nenhum desses casos acrescenta token à expressão.

### 3.2 `CalculatorManager` [O]
- **MemorizeNumber 0x18010d760 (MS):** só fora de erro. `ProcessCommand(124)`; toma o racional de motor+0xd8
  (o ponteiro é zerado) e o **insere no início** do vetor (`FUN_18010de10(vec, …, begin, …)`). Se passar de 100
  itens, `FUN_18010dd40` corta para 100, descartando o último (o mais antigo). Depois `SetMemorizedNumbersString`.
- **MemorizedNumberLoad 0x18010d9b0(i):** fora de erro; `i` < tamanho, senão `FUN_1800e72a0` (erro de índice). Copia
  `mem[i]` para motor+0xd8 (`FUN_180112410`).
- **MemorizedNumberChanged 0x18010dab0(i):** fora de erro: `mem[i] = *motor+0xd8` e o ponteiro é solto.
- **MemorizedNumberSubtract 0x18010d8c0(i):** fora de erro. Se a memória está **vazia**: `MemorizeNumber()` e depois
  chama a si mesma **duas vezes** com i = 0. Se não: `Load(i)`, `ProcessCommand(126)`, `Changed(i)`,
  `SetMemorizedNumbersString`. No fim chama `ICalcDisplay` slot 9 (`MemoryItemChanged(i)`).
  - Consequência: com a memória vazia e valor x, M− grava x, depois x − x = 0, depois 0 − x = **−x**.
- **MemorizedNumberClear 0x18010d810(i):** remove `mem[i]` (desloca os seguintes). Não testa erro.
- **MemorizedNumberClearAll 0x18010d940:** esvazia o vetor, `ProcessCommand(122)`, `SetMemorizedNumbersString`.
- **SetMemorizedNumbersString 0x18010dbe0:** para cada item, `FUN_180116f90(motor, …, item, base motor+0xe24)` (a
  mesma conversão do visor) e o agrupamento `FUN_18012c350` (separador de milhar). Envia o vetor de textos ao
  `ICalcDisplay` slot 8 (+0x40).

### 3.3 VM (`StandardCalculatorViewModel`) [O]
- **MS** `OnMemoryButtonPressed` 0x1800d6bf0: `MemorizeNumber`; telemetria (0x92); anúncio `Format_MemorySave`
  ("%1 salvo na memória", texto do visor em VM+0x40).
- **MR** `OnMemoryItemPressed` 0x1800d7350(pos): só se `MemorizedNumbers.Size != 0`. Se `motor+0xe20 == 0`:
  `Load(pos)`, `ProcessCommand(123)`, `ICalcDisplay` slot 10. Depois fecha o flyout de memória (`FUN_1800e4eb0`, [I]) e
  registra telemetria.
- **M+** `OnMemoryAdd` 0x1800d76b0(pos): se `motor+0xe20 == 0`: memória vazia (CM+0x40 == CM+0x48) → `MemorizeNumber`;
  se não, `Load(pos)`, `ProcessCommand(125)`, `Changed(pos)`, `SetMemorizedNumbersString`. Depois slot 9.
- **M−** `OnMemorySubtract` 0x1800d78f0(pos): telemetria e `MemorizedNumberSubtract(pos)`.
- **MC** handler 0x1800d6680: `MemorizedNumberClearAll`; anúncio `Memory_Cleared` ("Memória limpa").
- **Limpar item** `OnMemoryClear` 0x1800d7ac0(pos): `MemorizedNumberClear(pos)`, `RemoveAt(pos)`, renumera as
  posições e, se ficou vazia, `IsMemoryEmpty = true`.
- **SetMemorizedNumbers** 0x1800d4b70 (slot 8): lista vazia → `Clear()` e `IsMemoryEmpty = true`. Senão, enquanto a lista
  da VM é menor, cria `MemoryItemViewModel` para o item novo e faz `InsertAt(0)`. Quando os tamanhos batem, atualiza
  `Value` dos itens cujo texto mudou. Os dígitos passam pela troca para dígitos nativos (`FUN_180022b20`), que não muda
  nada quando o dígito zero local é `'0'`.

### 3.4 Habilitação dos botões [I]
`Calculator.xbf` tem os setters `ClearMemoryButton.IsEnabled`, `MemRecall.IsEnabled`, `MemPlus.IsEnabled`,
`MemMinus.IsEnabled` e `MemButton.IsEnabled` (strings 96–101) e `Memory.xbf` usa `IsMemoryEmpty`. [I] MC, MR e M▾
dependem de `IsMemoryEmpty`; M+, M− e MS dependem do erro. Isso combina com o observado na Fase 4: memória vazia → MC,
MR e M▾ desabilitados; em erro → M+, M− e MS também (L19).

## 4. Regras do histórico

### 4.1 Gravação de um item [O]
`FUN_18010fb30(coletor, textoResultado)`: se coletor[0] existe, chama `AddToHistory(tokens, comandos, texto)`
**sem nenhum filtro** e passa o índice devolvido a `OnHistoryItemAdded`. Depois esvazia tokens e comandos e põe o
índice do operando corrente em −1 (`FUN_18010e840`).

O motor chama `FUN_18010fb30` em quatro situações (todas em 0x180112db0):

| # | Situação | Texto do resultado | Expressão gravada |
|---|---|---|---|
| H1 | `=` sem erro (`case 0x79`, fim) | visor agrupado (`FUN_18012c350(motor+0xe48)`) | tokens + `=` (chave `41`) |
| H2 | operador binário com outro pendente, **só no Padrão** (`*motor == 0`), sem erro (`=` implícito, 3a §3.3) | visor agrupado já com o resultado parcial | tokens + `=` |
| H3 | dígito ou separador com operando corrente (+0xf8c ≠ −1), sem operador pendente (+0x20 = 0), sem erro, sem parênteses abertos e **último comando unário** (0x62–0x76, 400–411 ou 0x50) | visor agrupado (o resultado da unária) | tokens **sem** `=` |
| H4 | MR nas mesmas condições de H3 (`case 0x7b`) | visor agrupado, **antes** de mostrar o valor da memória | tokens **sem** `=` |

Nas condições de H3/H4 com operador pendente, ou com outro último comando, o motor só remove o operando corrente da
expressão (`FUN_18010ff50`) e reexibe a linha (slot 2). Não grava histórico.

Consequências:
- `=` **sempre** grava, inclusive sem operador: `5 =` grava `5 =` → 5, e `= =` grava duas vezes (o 2º `=` recria o
  operando a partir do visor porque +0xf8c ficou −1).
- O `=` repetido grava a conta repetida: `2 + 3 = =` grava `2 + 3 =` → 5 e `5 + 3 =` → 8.
- Erro não grava: em `8 ÷ 0 =` o `DisplayError` liga +0xe20, e o fim do `case 0x79` só grava se +0xe20 == 0.
- C não apaga o histórico (`case 0x51` não toca o `CalculatorHistory`).

### 4.2 Texto da expressão [O no texto; I na exibição]
- `AddToHistory` 0x180128130 monta a expressão com `FUN_180128000`: **concatena os tokens separados por um espaço**
  (o primeiro sem espaço antes).
- Os tokens de um binário são `" "`, `op`, `" "` (`FUN_18010ec10`; `DAT_18017cb14` = `20 00` = L" ", lido em
  0x18017cb10). O `=` é um token só, `"="` (chave `41`, valor `=` no PRI). O operando é o texto do visor.
- Uma unária vira `prefixo(` (prefixo + chave `48`, numa string só) antes do operando e `)` (chave `49`) depois
  (`FUN_18010f200`, `FUN_1801107e0`).
- Exemplos do texto bruto: `7 + 5 =` → **`"7   +   5 ="`** (três espaços em volta do operador); `9 √` →
  **`"√( 9 )"`**. Isso explica o afastamento dentro dos parênteses visto na linha de expressão (L15), pelo menos para o
  histórico.
- `HistoryItemViewModel` (0x1800b48d0) recebe o texto sem mudança (`FUN_180022140` = `WindowsCreateString`), salvo a troca
  para dígitos nativos. [I] O `TextBlock` mostra os espaços como estão.
- O resultado é o texto do visor no momento da gravação (com agrupamento de milhar).

### 4.3 Lista na VM [O]
- `OnHistoryItemAdded` 0x1800b5780(i): assert `uIdx < m_historyItems.size()`. Cria o `HistoryItemViewModel` do item i. Se
  `Items.Size >= máximo` (CalculatorHistory+0x20), faz `RemoveAt(Size − 1)`; depois **`InsertAt(0)`** e
  `PropertyChanged(ItemsCount)` (`DAT_180205f90`).
- `AddToHistory`: com `size >= 20`, remove o **primeiro** do vetor do motor (o mais antigo) e depois faz `push_back`.
  Motor e VM concordam: os 20 mais recentes ficam, com o mais novo no topo da lista.
- `ReloadHistory` 0x1800b53d0(modo): modo 0 usa CM+0xa0 e modo 1 usa CM+0xb0 (outros modos: retorna). Reconstrói a
  lista do fim para o começo, com o mais novo primeiro.
- `OnClearCommand` 0x1800b65a0: se `AreHistoryShortcutsEnabled` (vslot 0xc0; o ctor liga com `set(1)`): esvazia o
  vetor do histórico **atual** (CM+0xc0) e `Items.Clear()`, e anuncia `HistoryList_Cleared` ("Histórico limpo"). **Não
  envia nada ao motor**: visor e linha de expressão não mudam.
- `DeleteItem` 0x1800b60c0: remove o item do vetor e da lista e anuncia `Format_HistorySlotCleared` (`DAT_180205fd0`,
  `trabalho/hstring-globais.json`). As chaves dos outros anúncios citados também vêm desse arquivo: `ItemsCount`
  0x180205f90, `HistoryList_Cleared` 0x180205fb0, `Format_MemorySave` 0x180206270, `Memory_Cleared` 0x1802062d0 e
  `Format_MemorySlotCleared` 0x1802062b0 (este em `OnMemoryClear`).
- `SelectHistoryItem` 0x1800db3d0: reaplica tokens e comandos (`FUN_1800d3dd0`, `SetExpressionDisplay` 0x1800d3d30) e o
  resultado (`SetPrimaryDisplay` 0x1800d35b0).

### 4.4 Separação por modo [O no motor; I na tela]
- `SetStandardMode` 0x18010d0e0 faz CM+0xc0 = CM+0xa0; `SetScientificMode` usa CM+0xb0; o Programador não muda CM+0xc0
  (01 §6.6). Os itens gravados num modo vão para o histórico desse modo.
- [I] Ao trocar de modo, o C# (`ApplicationViewModel`, L3) chama `ReloadHistory(modo)`. Então a lista mostrada é a do modo
  atual. Esse chamador não foi lido.
- A troca de modo **não mexe na memória** (CM+0x40 não aparece em 0x18010d0e0/1f0/300), e o VM é o mesmo
  (`SetCalculatorType`, [I] 01 §6.1.3). Então a memória é compartilhada entre Padrão e Científico.

## 5. Casos de borda

| # | Situação | Comportamento previsto | Base |
|---|---|---|---|
| E1 | `2 + 3 × 4 =` no Padrão | 2 itens: `5 × 4 =` → 20 (topo) e `2 + 3 =` → 5 | O (H2 + H1) |
| E2 | mesma conta no Científico | 1 item: `2 + 3 × 4 =` → 14 | O (H2 só no Padrão) |
| E3 | `5 =`, `= =` | cada `=` grava um item | O |
| E4 | erro | nada é gravado | O |
| E5 | 21 contas | ficam 20; sai a mais antiga | O |
| E6 | `9 √` + dígito, ou + MR | grava `√( 9 )` → 3, sem `=` | O |
| E7 | MS, MS | o novo fica no topo | O |
| E8 | M+ sem memória | igual a MS | O |
| E9 | M− sem memória | grava −x | O |
| E10 | MR | carrega o item do topo (posição 0) | O |
| E11 | MS de 1/3 | guarda o racional exato; MR × 3 = 1 | O (cópia) + I (aritmética da 3f) |
| E12 | MS/M+/MC logo após `=` | apagam a linha de expressão | O |
| E13 | MC | lista vazia; MC, MR e M▾ desabilitados | O (motor/VM) + I (IsEnabled) |
| E14 | Limpar histórico | só a lista; visor e expressão iguais | O |
| E15 | memória com mais de 100 itens | fica com 100; sai a mais antiga | O; não testado (caso longo) |
| E16 | troca Padrão ↔ Científico | histórico de cada modo separado; memória a mesma | O motor + I UI |

## 6. Lacunas desta fase
Registradas em `relatorio/04-lacunas.md`: L21 (chamador de `ReloadHistory` e de `SelectHistoryItem` no C#), L22
(clique num item de histórico e botões por item da memória não automatizados), L15 (atualizada com §4.2).

## 7. Casos de teste
Em `relatorio/03b-casos-de-teste.md`, congelado por SHA-256 em `hashes-originais.txt` antes da execução.

## 8. Resultados da execução caixa-preta (2026-10-22)

**Ordem dos fatos.** Previsões congeladas às 19:25:44 (SHA-256 `c114045b…bf38`). Depois disso, e só depois, vieram o
levantamento da árvore UIA dos submenus (`trabalho/automacao/arvore-uia-3b.txt`), o teste do script com 3b-01 e 3b-12
(19:27:59) e a execução completa (19:28:48). Os SHA-256 instalados de `CalculatorApp.exe`, `CalculatorApp.dll` e
`CalcViewModel.dll` são iguais aos de `./binarios` (`log-execucao-3b-execucao1.txt`).

**Execução.** `trabalho/automacao/rodar-casos.ps1 -Etapa Casos3b`. Antes de cada caso, o script limpa o histórico dos
modos Científico e Padrão ("Limpar todo o histórico" no submenu), faz MC se estiver habilitado, vai ao modo do caso, aperta
C e **confere** que histórico e memória estão vazios (aborta se não estiverem).
- Resultados: `relatorio/resultados-reais-3b.txt`; brutos em `trabalho/automacao/resultados-reais-3b-execucao{1,2}.txt`.
- **Reexecução de 3b-08 (registrada):** na 1ª execução o leitor usava `FindAll` e só recebia os 18 itens que o ListView
  virtualizado tinha realizado (até `[4 + 1 = | 5]`). O leitor passou a usar `ItemContainerPattern` +
  `VirtualizedItemPattern.Realize`, e 3b-08 foi refeito sozinho (19:39:41), junto com 3b-02 como controle (igual à 1ª). O
  resultado vale com a 2ª leitura; a 1ª está guardada. As capturas de 3b-02 e 3b-08 são da 2ª execução.

**Origem de cada leitura.**
- Visor: texto de `NormalOutput` (UIA RawView).
- Histórico e memória: texto dos TextBlocks `HistoryItemExpression`, `HistoryItemValue` e `MemoryItemValue` (UIA RawView).
  **Nenhuma leitura de lista foi transcrita**: o texto vem do UIA, com os espaços originais. O Name dos itens é o texto do
  Narrador e fica só no log.
- Linha de expressão: lida da captura (`capturas/3b-*.png`), em `trabalho/automacao/transcricao-capturas-3b.tsv`. Coluna
  "origem": `ocr` = o OCR do Windows leu certo (conferido na captura); `manual` = **transcrita a olho** porque o OCR errou ou
  não leu. São **25 manuais em 44 leituras**. As 44 transcrições foram conferidas com o Name do Narrador
  (`CalculatorExpression`, em `log-execucao-3b-*.txt`) e todas batem.

**Critério (fixado antes da execução, `comparar-3b.py`).** *Acerto*: todas as leituras previstas conferem. *Parcial*: visor,
histórico e memória conferem; falha só expressão ou estado de botão. *Erro*: falha visor, histórico ou memória. Expressões são
comparadas sem espaços; visor e memória, exatamente.

Comparação gerada por `python3 -I trabalho/automacao/comparar-3b.py .`, que confere o hash do arquivo congelado. A última
coluna diz, por leitura (L1, L2…), se a expressão foi transcrita manualmente:

| ID | Bloco | Classe | Divergências | Origem da expressão por leitura |
|---|---|---|---|---|
| 3b-09 | A | acerto | — | L1:manual L2:ocr L3:manual L4:ocr |
| 3b-11 | A | acerto | — | L1:ocr |
| 3b-18 | A | acerto | — | L1:ocr L2:ocr |
| 3b-19 | A | acerto | — | L1:ocr L2:manual |
| 3b-25 | A | acerto | — | L1:ocr L2:ocr L3:ocr |
| 3b-26 | A | parcial | L1 MC=des (previsto hab); L1 MR=des (previsto hab) | L1:manual L2:ocr |
| 3b-01 | B | acerto | — | L1:manual |
| 3b-02 | B | acerto | — | L1:manual L2:manual |
| 3b-02c | B | acerto | — | L1:manual L2:manual |
| 3b-03 | B | acerto | — | L1:manual L2:manual |
| 3b-04 | B | acerto | — | L1:manual L2:manual |
| 3b-05 | B | acerto | — | L1:manual L2:manual |
| 3b-06 | B | acerto | — | L1:manual L2:manual |
| 3b-07 | B | acerto | — | L1:manual |
| 3b-08 | B | acerto | — | L1:ocr |
| 3b-10 | B | acerto | — | L1:manual L2:manual |
| 3b-12 | C | acerto | — | L1:ocr |
| 3b-13 | C | acerto | — | L1:ocr |
| 3b-14 | C | acerto | — | L1:ocr |
| 3b-15 | C | acerto | — | L1:ocr |
| 3b-16 | C | acerto | — | L1:ocr |
| 3b-17 | C | acerto | — | L1:ocr |
| 3b-20 | C | acerto | — | L1:ocr |
| 3b-21 | C | acerto | — | L1:manual L2:ocr |
| 3b-22 | C | acerto | — | L1:manual |
| 3b-23 | C | acerto | — | L1:manual |
| 3b-24 | C | acerto | — | L1:manual L2:manual |

**Taxa de acerto por bloco.**

| Bloco | Casos | Acerto | Parcial | Erro | Taxa |
|---|---:|---:|---:|---:|---:|
| A | 6 | 5 | 1 | 0 | 83% |
| B | 10 | 10 | 0 | 0 | 100% |
| C | 11 | 11 | 0 | 0 | 100% |
| Total | 27 | 26 | 1 | 0 | 96% |

São 44 pontos de leitura, e em cada um se leem visor, histórico e memória. Os 132 valores conferem, e as 44 expressões também (sem
espaços). A única falha está no estado de dois botões em 3b-26, uma previsão [I].

**Divergência D1, 3b-26: MC e MR desabilitados em erro, com memória** [O, XBF].
- `Views/Calculator.xbf`, grupo `ErrorVisualStates`, estado **`ErrorLayout`** (fluxo de nós em `trabalho/pri/xbf-nos/Views/Calculator.txt`,
  0x006a8f–0x006ae9): cinco `Setter` com `Value="False"` para `ClearMemoryButton.IsEnabled`, `MemRecall.IsEnabled`,
  `MemPlus.IsEnabled`, `MemMinus.IsEnabled` e `MemButton.IsEnabled`.
- Em erro, os cinco botões de memória são desabilitados por estado visual, independentemente de `IsMemoryEmpty`.
  `MemoryButton` (M▾) **não** está na lista e continua dependendo só de haver memória. Isso confere com a leitura de 3b-26
  (M▾ habilitado em erro, com memória).
- Causa da previsão errada: a §3.4 supôs que MC/MR dependiam só de `IsMemoryEmpty`. A tabela de strings já listava os setters
  logo após `ErrorLayout` (strings 93–101), mas a análise não abriu o fluxo de nós.
- [I] Quem aplica o estado é o C# (`VisualStateManager.GoToState` com `IsInError`, L3). O mesmo grupo de setters aparece em
  `DisplayModeAlwaysOnTop` (modo Sobrepor).

**Inferências confirmadas.**
- §4.4 / L21: na troca de modo, a lista de histórico mostra o histórico do modo novo (3b-09).
- §4.4: a memória continua na tela e no motor após a troca de modo, e MR no Científico lê o item gravado no Padrão (3b-25).
- §3.4: MC, MR e M▾ seguem `IsMemoryEmpty` fora de erro (3b-11, 3b-18).
- E11: MS guarda o valor exato. `MR × 3 =` dá `1`, e não `0,9999999999999999` (3b-19).
- §4.2: o texto bruto do histórico tem os espaços previstos (`7   +   5 =`, `√( 9 )`, `5 =`), lido pelo UIA, fora da taxa.
