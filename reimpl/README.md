# Reimplementação (Fase 5, escopo 3a–3d)

Pacote Python `calculadora`, feito só a partir de `relatorio/`, que reproduz a Calculadora do Windows 11.2607.0.0
nos modos Padrão, Científico e Programador, com histórico, memória e a formatação do visor (`NumberToString`).
A conversão de unidades (3e) e a emulação do motor numérico (3f) ficaram fora do escopo (04-lacunas L30).

## Uso

```sh
python3 -m venv .venv && .venv/bin/pip install mpmath pytest   # ou: pip install -e '.[testes]'
.venv/bin/python -m calculadora                     # interativo (Padrão); :ajuda lista as teclas
.venv/bin/python -m calculadora -m cientifico 30 SIN
.venv/bin/python -m calculadora 2 + 3 '*' 4 =       # Padrão: 20, com dois itens de histórico
.venv/bin/python -m calculadora -m programador -- R:HEX '#F0' NOT
.venv/bin/python -m pytest                          # 215 casos + 5 de integridade (220 no total)
.venv/bin/python ferramentas/mutacoes.py            # teste negativo do harness
```

As teclas usam a notação dos passos de `trabalho/automacao/rodar-casos.ps1`: número com vários dígitos = um botão por
dígito, `#1A3` aceita A–F, `>` (só nos testes) é um ponto de leitura. A CLI aceita também apelidos (`÷ × − √ x² 1/x`).

## Estrutura: módulo → componente documentado

| Módulo | Componente do binário | Base |
|---|---|---|
| `viewmodel.py` | `StandardCalculatorViewModel`: `OnButtonPressed` (erro → C), painel HEX/DEC/OCT/BIN, `ErrorLayout`, ciclo do tamanho | 01 §6.3, 02a §4.4, 02b §8, 02d §1/§3 |
| `gerenciador.py` | `CalculatorManager` (SendCommand, INV + função, engines por modo, memória) e `CalculatorHistory` (20 itens) | 01 §6.4/§6.6, 02b §2–§4 |
| `motor.py` | engine: `ProcessCommand`, `DoOperation`, `SciCalcFunctions`, `DisplayNum`, `DisplayError`, precedência, parênteses, modo inteiro | 02a, 02b §3.1/§4.1, 02c, 02d |
| `coletor.py` | coletor de expressão/histórico (motor+0xf70): tokens, `=` implícito, H1–H4, `(`…`)` da troca de operador | 02a §3.3/§6, 02b §4, 02c §3.11 |
| `entrada.py` | objeto de entrada (motor+0x28): dígitos, separador, ⌫, ±, Exp, limites | 02a §3.1, 02c §3.8, 02d §3.3 |
| `formatacao.py` | `NumberToString` 0x1801300f0 (float/científica), versão inteira 0x180116f90, agrupamento 0x18012c350, linha BIN da VM | 02a §5, 02c §3.13, 02d §3.1 |
| `numerico.py` | ratpak: racionais exatos (`Fraction`), domínios, códigos de erro; transcendentais com `mpmath` | 02a §4, 02c §3, L26 |
| `textos.py` | `CEngineStrings` (símbolos EN-US, erros pt-BR) e o mapa de exceções do texto de cada comando | 01 §7.2, 02a §7 |
| `cli.py`, `teclas.py` | CLI e interpretador de teclas | — |

**Funções transcendentais (L26).** sen/cos/tan e inversas, hiperbólicas, ln/log/eˣ, potências e raízes não exatas
e Γ saem do `mpmath` com 120 dígitos e voltam a racional exato. **O algoritmo do motor não foi emulado**: o π de 41
dígitos (`asin(1/2)·6`), as séries de Taylor até ~10⁻¹²⁸, o corte `FUN_1801265d0` e a Γ de `FUN_18013b1b0` não estão
aqui. São emuladas as regras lidas no binário que mudam o resultado visível: redução DEG/GRAD exata (mod 360/400 com
truncamento), domínio trig `x < 10¹⁰⁰` com sinal, corte `|y| ≤ 10⁻ᴾ → 0`, tan com cos = 0 → erro, asen com
`||x| − 1| ≤ 10⁻ᴾ → π/2`, n! fora de [−1000, 3249] → Estouro, potência inteira exata e raiz de denominador ímpar de
base negativa. Como mostra a auditoria da 3c (02c §10.2), nenhum caso do oráculo discrimina o algoritmo numérico.

## Oráculo e testes

- **Casos**: os 215 IDs dos arquivos congelados `relatorio/03-casos-de-teste.md` e `03b/03c/03d`. Os passos vêm de
  `rodar-casos.ps1` (o que foi executado), extraídos por `ferramentas/extrair_casos.py` para `tests/casos.json`.
  `tests/test_congelados.py` confere o SHA-256 de cada arquivo congelado contra `hashes-originais.txt` e que os IDs
  coincidem.
- **Valores reais**: `relatorio/resultados-reais*.txt` (visor, histórico, memória, botões, linhas, bits, lidos do UIA).
  Para a expressão: a coluna já transcrita do `resultados-reais.txt` (3a) e `trabalho/automacao/transcricao-capturas-3{b,c,d}.tsv`
  (3b–3d). O OCR bruto não é usado. Leituras sem transcrição (86 das 112 da 3d) ficam sem expressão a comparar.
- **Critério**: visor, histórico (texto bruto, com os três espaços do binário), memória, linhas e bits exatos;
  expressão sem espaços (L20), e `‹` (linha cortada) exige sufixo; botões, os que a leitura registrou. Um teste por
  caso; ele passa só se **todas** as leituras conferem.
- **Leituras comparadas**: 3a 54 visores + 54 expressões + 297 estados de botão; 3b 44 × (visor, expressão,
  histórico, memória) + 264 estados de botão; 3c 89 visores + 89 expressões; 3d 112 visores + 448 linhas + 26
  expressões + 10 conjuntos de bits.
- **Preparo**: uma calculadora nova por caso, no modo do caso, com o ângulo (3c) e a base, tamanho e opção de
  deslocamento (3d) do caso. Equivale ao preparo da automação (C, memória e histórico vazios). Na 3d-93 (execução 2) a
  automação apertou CE antes do C porque o C não estava visível; a reimplementação aperta só C, com o mesmo efeito.
- **Botão desabilitado**: como na automação (3a-09), um botão desabilitado não é pressionado. O estado modelado é o do
  modo Padrão (02a §4.4, 02b §8) e, desde a correção pós-diferencial, o do Científico e do Programador em erro (L19).

## Resultado

| Subfase | Casos | Passam |
|---|---:|---:|
| 3a | 30 | 30 (100%) |
| 3b | 27 | 27 (100%) |
| 3c | 73 | 73 (100%) |
| 3d | 85 | 85 (100%) |
| Total | 215 | 215 (100%) |

**Ressalva de independência.** O relatorio já incorpora as correções feitas a partir dessas mesmas execuções: o `=`
implícito do Padrão (3a-02), a limpeza da expressão após `=` (3a-24), o C em erro (3a-10), o `ErrorLayout` (3b-26) e o
preenchimento da linha BIN (3d-02/03). Então 215/215 mostra que o documento, como está hoje, basta para reproduzir
tudo o que foi observado. Não é uma validação independente das previsões; essas taxas estão nas seções de resultados de
cada `02-features/*.md`.

**Teste negativo** (`ferramentas/mutacoes.py`): cada regra quebrada derruba casos. Arredondar por truncamento derruba
16 casos; tirar o preenchimento da linha BIN, 29; usar fmod no mod, 2; pressionar botão desabilitado, 1; tirar o
agrupamento, 20; tirar o corte 10⁻ᴾ, 4.

## Correções pós-diferencial (2026-10-23)

O teste diferencial (`relatorio/03-diferencial-resultados.md`) achou cinco regras que faltavam ou estavam erradas. Os
documentos foram corrigidos primeiro (02c §3.12, 02d §3.1, 04-lacunas L19) e o código depois:
- **visor em BIN** passa por `FUN_1800d98a0` (`viewmodel.primario`, `formatacao.preencher_binario`), também em erro;
- **`(` depois de operador binário** zera o número corrente (`motor._abre`);
- **`±` antes de `(`** não gera o × implícito (`motor._ANTES_DE_PARENTESE`, l. 2024 do ProcessCommand);
- **`(` salva o operador só se há pendente** (B3, `motor._abre`);
- **botões desabilitados em erro** no Científico e no Programador pelos `ErrorLayout` dos XBF (`teclas.desabilitado`,
  `viewmodel.desabilitado_em_erro`); F-E e ângulo ficam habilitados, como observado (L19).

Com elas, 215/215 congelados e 300/300 do diferencial 1. O diferencial 1 deixa de ser fora da amostra.

## Consultas ao binário

Uma, motivada por um teste que falhou por falta de documentação (registrada em 04-lacunas L29):
- **Painel do Programador em erro.** O oráculo mostrava as quatro linhas vazias em erro (3d-44…47, 72, 76, 78, 80, 85),
  e o relatorio não tratava disso. Consultei o pseudocódigo já extraído na 3d (`trabalho/fase3d-evidencias.json`,
  Evidence `ev_ef6f96f5…`, agora salvo em `trabalho/pseudocodigo/0x1800d9b20.c`). Nenhuma sessão nova do REA foi
  aberta. `FUN_1800d9b20` só calcula as linhas se o vslot 0x350 devolve 0; senão grava as strings vazias [O].

## Decisões sem documento ([I] no código)

| Onde | Decisão |
|---|---|
| `formatacao.numero_para_texto` | com e > 0 e mais de P dígitos, arredonda para P significativos (o documento detalha só e ≤ 0) |
| `numerico.potencia` | x⁰ = 1, 0^y (y > 0) = 0; \|y·log10\|x\|\| ≥ 10⁵ → Estouro; acima de ~50 mil dígitos a potência inteira sai do mpmath (guarda de memória: o motor real limita os racionais por uma regra não documentada para as operações básicas) |
| `numerico.exp`, `de_mp` | Estouro quando o resultado passaria de 10^±42000 |
| `numerico.arco_cosseno`, `hiperbolica` | domínio do acos igual ao do asen; acosh(x < 1) e atanh(\|x\| ≥ 1) → Entrada inválida |
| `motor._funcao` (sec/csc/cot, sech/csch/coth) | recíprocas das diretas; as inversas são o arco da recíproca. Nada disso foi lido |
| `motor._do_inteiro` | o resultado do binário é truncado logo na operação; nos caminhos documentados, o valor é o mesmo do truncamento feito pelo DisplayNum |
| `viewmodel` | F-E e ângulo habilitados em erro, contra o setter de `FtoeButton` no XBF (observação caixa-preta, L19) |
| `motor` | INV não finaliza a digitação nem conta como "último comando"; `)` sem `(` não muda o último comando; C não desliga o INV; `flag_mr` (+0x22) nunca é ligado |
| `coletor.envolver_tudo` | o "trecho" que recebe `(`…`)` são os tokens depois do último `(` aberto |
| `entrada` | ⌫ no expoente apaga o último dígito dele e, sem dígitos, sai do modo expoente; zero à esquerda do expoente não entra |
| `viewmodel.definir_modo` | a troca de modo (C#, L3) não passa pelo teste de erro de `OnButtonPressed` |
| `viewmodel.bits` | em erro, nenhum bit (o texto binário fica vazio, L29) |

**Não reimplementados** (semântica fora do relatorio): DMS, Degrees, Rand, a edição de token da VM
(`IsEditingEnabled`), colar (`CopyPasteManager`), snapshots e o clique em item de histórico (L22). A CLI responde
"não reimplementado" para eles.
