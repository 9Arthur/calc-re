# 99 — Conclusão

## 1. Resumo do projeto

Engenharia reversa estática da Calculadora do Windows 11.2607.0.0 x64 (`./binarios`, somente leitura), com REA e
Ghidra 12.1.4. A Calculadora instalada foi usada só como caixa-preta, via UI Automation, para conferir previsões já
congeladas.

| Fase | Entregável | Conteúdo |
|---|---|---|
| 0–1 | `00-inventario.md` | pacote, hashes, motor de cálculo e interface em `CalcViewModel.dll` (C++/CX) e `CalculatorApp.dll` (.NET Native) |
| 2 | `01-arquitetura.md` | imports, RTTI, vtables, 558 métodos WinRT ligados a endereços, cadeia UI → VM → `CalculatorManager` → motor |
| 3a–3d | `02-features/a…d` | operações básicas e erro, histórico e memória, Científico, Programador |
| 3e, 3f | — | fora do escopo por decisão do usuário (L30); modo gráfico também (L8) |
| 4 | `03*-casos-de-teste.md` | 215 casos com previsões congeladas por SHA-256 antes de cada execução |
| 5 | `reimpl/` | reimplementação em Python feita só a partir do relatório |
| pós-5 | `03-diferencial-*.json`, `03-diferencial-resultados.md` | dois testes diferenciais fora da amostra (300 sequências aleatórias cada) |
| — | `04-lacunas.md` | 31 lacunas, com a situação de cada uma |

## 2. Evolução das taxas

A taxa de cada linha é a da **primeira passada**. Os números vêm das seções de resultados de cada `02-features/*.md` e de
`03-diferencial-resultados.md`.

| Etapa | O que mede | Padrão / 3a | 3b | Científico / 3c | Programador / 3d | Total |
|---|---|---:|---:|---:|---:|---:|
| Previsões da análise (Fases 3a–3d) | análise × Calculadora real, fora da amostra | 27/30 (90%) | 26/27 (96%) | 73/73 (100%)¹ | 83/85 (98%)² | 209/215 (97%) |
| Reimplementação × casos congelados (Fase 5) | dentro da amostra³ | 30/30 | 27/27 | 73/73 | 85/85 | 215/215 |
| Diferencial 1, 1ª passada (reimpl `100ee57a…`) | fora da amostra | 100/100 | — | 58/100⁴ | 87/100 | 245/300 (81,7%) |
| — o mesmo, só casos válidos | | 100/100 | — | 58/61 (95%) | 87/100 | 245/261 (93,9%) |
| Diferencial 1, 2ª passada Ci-062…100 (preparo verificado) | fora da amostra | — | — | 34/39 (87%) → Ci válidos 92/100 | — | — |
| Reimplementação corrigida (`2a2df4fe…`) | dentro da amostra³ | congelados 215/215; diferencial 1 300/300 | | | | |
| **Diferencial 2, 1ª passada** (semente 20261024) | **fora da amostra** | **98/100** | — | **96/100** (96/97 sem falha da automação) | **99/100** | **293/300 (97,7%)** |

1. O bloco B da 3c (26 valores de 32 dígitos) **não discrimina** o algoritmo do motor da matemática exata (02c §10.2), e
   o 3c-47 não era independente. São 46/46 casos independentes no bloco A.
2. Nos 56 casos discriminantes da 3d: 56/56.
3. As correções saíram desses mesmos casos. Essas linhas medem reprodução, não previsão.
4. 39 casos invalidados por contaminação do estado F-E da automação (§6.5).

Divergências por etapa, já classificadas:

| Etapa | Lacuna de documentação | Bug da reimpl | Motor numérico (3f) | Automação |
|---|---:|---:|---:|---:|
| Diferencial 1, 1ª passada | 14 | 2 | 0 | 39 |
| Diferencial 1, 2ª passada (Ci-062…100) | 4 | 1 | 0 | 0 |
| Diferencial 2, 1ª passada | 5 | 0 | 0 | 2 |

## 3. O que foi e o que não foi reproduzido

**Reproduzido** (fora da amostra no diferencial 2, salvo as três regras do §4):
- Operações básicas, divisão por zero e as mensagens de erro em pt-BR.
- `=` implícito do Padrão, `=` repetido, troca de operador, precedência do Científico (pilha de 25) e parênteses: × implícito sem `±`, número corrente zerado após operador (B1), operador salvo só com pendente (B3).
- Formato do visor: 16 e 32 dígitos, arredondamento, notação científica, `1,e+N`, agrupamento pt-BR, F-E.
- Funções do Científico: valores (via `mpmath`), domínios, cortes e redução de ângulo.
- Histórico (20 itens, separado por modo) e memória.
- Programador:
  - bases e tamanhos de palavra (truncamento, complemento de 2);
  - operações bit a bit e deslocamentos aritmético e lógico;
  - rotações com e sem transporte;
  - ÷ e mod inteiros;
  - painel HEX/DEC/OCT/BIN e o preenchimento BIN do painel **e do visor** (inclusive `0Resultado indefinido`).
- Botões desabilitados em erro nos três modos (`ErrorLayout` dos XBF).

**Não reproduzido:**
- Fora do escopo: modo gráfico (L8), conversão de unidades (L30), datas.
- O **algoritmo** do ratpak (π de 41 dígitos, séries, Γ). A reimplementação acerta os valores com `mpmath`, mas nenhum caso
  discriminou isso (L26). "Desvio do motor numérico" teve zero ocorrências, o que **não** prova a emulação.
- DMS, Degrees, Rand, colar, edição de token, clique em item do histórico (L22) e as decisões sem documento de L31.
- A camada C# (.NET Native, L3): só se conhece pelo efeito. Exemplos: troca de modo, reação do ToggleButton de F-E,
  quem aplica os `ErrorLayout`.
- A renderização exata da linha de expressão (L15/L20). Os diferenciais não leram a expressão.

## 4. As três regras abertas (diferencial 2)

Estão registradas em `03-diferencial-resultados.md` (etapa 3). Ainda não foram levadas aos `02-features`, ao
`04-lacunas` nem à reimplementação.

| | Regra observada | Hipótese | Como decidir |
|---|---|---|---|
| **D1** | `x =` sem operador e depois `%` usa x como base: `2 = 1/x %` → 0,01; `7 = 3 %` → 0,21 (Pd-005, Pd-087) [O caixa-preta] | [I] Algum caminho deixa acumulador = x no `=` sem operador. A leitura estática diz o contrário: o C grava acumulador 0 e `+0xe22` = 1 (l. 1325/1366), e o `=` só copia o atual para o acumulador se `+0xe22` = 0 (l. 1556–1557). Candidatos: `+0xe22` já é 0 nesse `=` (alguma gravação não lida, na VM ou no `DisplayNum`) ou outra camada grava o acumulador | ler `FUN_18012bb70`, `FUN_180112c40` e o caminho do C na VM. Caso barato: `C 7 = 50 %` (D1 prevê `3,5`; a reimpl dá `0`) |
| **D2** | `=` repetido depois de desempilhar a precedência repete a **última operação desempilhada** com o operando dela (Ci-010: 127; Pr-078: 4) | [O no código] O laço de desempilhar do `=` (l. 1764–1786) grava `+0xe0` = corrente (l. 1768) e `+0x18` = operador desempilhado. Falta documentar e implementar | `2 × 3 + 4 × 5 = =` no Científico: 26 e depois **46** (+ 20). A reimpl daria 130 (× 5) |
| **D3** | C com F-E ligado volta o visor ao formato normal: o F-E desliga no motor (Ci-028) [O caixa-preta] | [I] O C põe `IsFToEChecked` = false (0x1800d0c40). O ToggleButton, ligado por binding, desmarca e dispara `FtoEButtonToggled` → 119. Com o botão já desmarcado e o motor em F-E (contaminação do diferencial 1), o C não teve efeito, o que é coerente | ler o handler de `FtoeButton` em `CalculatorApp.dll` (L3, .NET Native). Caixa-preta: F-E, C, F-E de novo → o motor deve voltar a F-E |

## 5. Lições de método

**5.1 Calibração O/I.** As marcas funcionaram para o que se afirma, não para o que se omite.
- **Previsões [I]:** concentraram as falhas de previsão. Na 3a, as 3 falhas estavam todas na linha de expressão [I], e as
  54 leituras de visor conferiram. Na 3b, a única falha (3b-26) era uma previsão [I].
- **Afirmações [O]:** também erraram, por **completude**, não por conteúdo:
  - 3d-02/03 [O]: chamada presente no pseudocódigo e não lida;
  - "(não o visor)" no 02d §3.1: generalização sem procurar o segundo chamador;
  - 02c §3.12 [O]: omitiu a zeragem do número corrente (B1) e a regra do operador salvo (B3);
  - D2: o laço de desempilhar estava no pseudocódigo da 3a.
- **Lição:** [O] precisa vir acompanhado de "lido inteiro / lidos todos os chamadores" quando a frase é universal ("só",
  "não", "sempre").

**5.2 As duas origens de erro.**
1. **Código lido, mas descrito de forma incompleta ou generalizada.** Inclui 3a-02, 3a-24, 3d-02/03, A, B1, B3 e D2. A
   evidência estava no repositório (`trabalho/pseudocodigo/`), e o erro foi de redação. O único bug da reimplementação
   (B2: `±` antes de `(`) nasceu de um termo sem lista de códigos ("unária") e pertence a esta família.
2. **Comportamento numa camada não lida.** O C#/XAML de `CalculatorApp.dll` (L3) e os estados visuais. Inclui 3b-26
   (`ErrorLayout` da memória), os botões em erro do Científico (C/L19), o F-E em erro e com C (L25, D3) e provavelmente
   D1. Daqui só se sabe o efeito; os XBF ajudaram onde o efeito era declarativo.

**5.3 Congelamento.**
- Cada arquivo de casos teve o SHA-256 gravado antes de qualquer execução. Nos diferenciais, o hash da reimplementação
  também ficou congelado e foi conferido pelo executor.
- A primeira passada é a que conta. As reexecuções ficaram registradas à parte: 3b-08; a 2ª passada do Ci-062…100; a
  tentativa "CoreWindow", arquivada.
- O congelamento não impede erro de **classificação** depois. O Pr-013 foi atribuído só a B2 e tinha uma segunda causa
  (B3); a correção foi registrada como tal.

**5.4 Diferencial.**
- O 215/215 dentro da amostra escondia cinco regras, que o diferencial 1 achou em 300 sequências aleatórias.
- O diferencial 2, depois das correções, achou mais três. As divergências atribuíveis à análise caíram de 16 (14 + 2)
  para 5.
- As sequências aleatórias exercitam composições que casos escritos à mão não cobrem:
  - `(` logo após operador;
  - `±` antes de `(`;
  - `%` depois de `=`;
  - `=` repetido após precedência;
  - F-E em erro.
- O critério só lia visor e erro. Expressão, histórico e linhas do painel ficaram fora dos diferenciais.

**5.5 Ruído da automação.**
- **Contaminação de estado.** Um único estado contaminado (F-E acionado em erro, dif-Ci-061) invalidou 39 de 300 casos.
  O preparo passou a verificar pelo UIA o modo, o toggle de F-E, o ângulo e o visor exatamente `0`, reiniciando a
  Calculadora quando preciso. Na 2ª passada e no diferencial 2, nenhum preparo inválido.
- **Classe própria e teste de neutralidade.** As falhas da automação foram tratadas como classe à parte. Com a tecla não
  pressionada retirada, a reimplementação reproduziu exatamente o valor real (Ci-097, Ci-098).
- **Ruído restante:** toggles de submenu ausentes (2 no diferencial 2); `Abrir-Flyout` descarta o retorno "desabilitado"
  e relata "submenu não abriu".
- **Leitura só pelo UIA.** Nas fases 3a–3d, o OCR da expressão errou ou não leu 30 de 54 leituras (L20). Os
  diferenciais leram só o UIA, sem transcrição.

## 6. Verificação final dos hashes (2026-10-23 12:36:26)

`sha256sum -c hashes-originais.txt`: **25/25 OK**, status 0.
- 15 arquivos de `./binarios` e 4 de `./binarios-ptbr`: inalterados.
- Casos congelados intactos: `03-casos-de-teste.md`, `03b`, `03c`, `03d`, `03-diferencial-casos.json` e
  `03-diferencial2-casos.json`.

Binários **instalados** (registrados pela automação no diferencial 2): `CalculatorApp.exe` `f26a20f8…`,
`CalculatorApp.dll` `e0845520…` e `CalcViewModel.dll` `072cd589…`. São iguais aos analisados.

Árvore `reimpl/calculadora` agora: `2a2df4fe1ceef1a63022ad6c4cd10ef5ed40f15a5243b9c9efb602c1ae463ef9`. É a mesma
congelada no diferencial 2: nada mudou na reimplementação depois desse congelamento.
