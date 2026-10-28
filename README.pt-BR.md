# Calculadora do Windows: engenharia reversa estática e reimplementação em Python

> Projeto independente e educacional, sem afiliação, endosso ou suporte da Microsoft.
> "Windows" e "Calculadora do Windows" são marcas da Microsoft Corporation. Nenhum
> binário, recurso ou código-fonte da Microsoft é distribuído neste repositório.

Esta é a versão curta. O [README em inglês](README.md) é o documento principal; os
relatórios da análise estão em português na pasta `relatorio/`.

## O que é

Um experimento de engenharia reversa da Calculadora do Windows
(`Microsoft.WindowsCalculator` 11.2607.0.0, x64) feito **só com análise estática**,
em sessões do Claude Code com o servidor MCP REA e o Ghidra. As regras estão em
[`CLAUDE.md`](CLAUDE.md): nada é executado, o código-fonte público da Calculadora não
é consultado, toda afirmação é marcada como observada ou inferida, e as previsões são
congeladas por SHA-256 antes de qualquer teste caixa-preta na Calculadora instalada.

Depois da análise, a calculadora foi reimplementada em Python **a partir só dos
relatórios** (`reimpl/calculadora`): modos Padrão, Científico e Programador, histórico,
memória, formatação do visor e uma CLI.

## Como usar

```sh
cd reimpl
python3 -m venv .venv
.venv/bin/pip install -e '.[testes]'            # ou: pip install mpmath pytest
.venv/bin/python -m calculadora 2 + 3 '*' 4 =    # CLI; sem argumentos é interativa, :ajuda lista as teclas
.venv/bin/python -m calculadora -m cientifico 30 SIN
.venv/bin/python -m pytest                       # 220 testes (215 casos congelados + integridade)
```

## Resultados medidos neste projeto

| Medida | Resultado |
|---|---:|
| Previsões da análise × Calculadora real (215 casos congelados, 1ª passada) | 209/215 (97%) |
| Reimplementação × casos congelados (dentro da amostra) | 215/215 |
| Teste diferencial 2 (300 sequências aleatórias, fora da amostra) | 293/300 (97,7%) |

Fontes: `relatorio/99-conclusao.md` e `relatorio/03-diferencial-resultados.md`.

## Limitações

O projeto **não está completo**. Fora do escopo: conversão de unidades e moedas, modo
gráfico, datas, e o algoritmo numérico próprio do motor (as funções transcendentais usam
`mpmath`, não a emulação do ratpak). No Científico faltam DMS, Degrees e Rand, três
regras achadas no último diferencial ainda não foram implementadas, e algumas decisões
não têm documento que as sustente. A lista completa está em
[`relatorio/04-lacunas.md`](relatorio/04-lacunas.md) e na seção "Known limitations" do
README em inglês.

## Licença

O código e a documentação deste repositório são distribuídos sob a [Licença MIT](LICENSE).
A licença cobre apenas o conteúdo deste repositório. Os binários da Microsoft analisados, e
quaisquer artefatos derivados deles, não estão incluídos neste repositório e não são
cobertos por esta licença (ver o Disclaimer).
