# Projeto: engenharia reversa da Calculadora do Windows

Alvo: Microsoft.WindowsCalculator 11.2607.0.0 x64, binários em ./binarios
(somente leitura; hashes em ./hashes-originais.txt).
Ferramentas: REA (MCP) com provedor Ghidra 12.1.4.

## Regras
- Responda sempre em português.
- NÃO consulte o repositório microsoft/calculator nem qualquer código-fonte,
  write-up ou análise da Calculadora na internet. Só pode consultar
  documentação do REA, do Ghidra e de formatos (PE, APPX/MSIX, WinRT/winmd,
  PRI, XBF).
- NÃO modifique ./binarios. Arquivos de trabalho vão em ./trabalho.
- NÃO execute os binários. Análise estática apenas.
  Exceção (Fase 4): é permitido executar a Calculadora instalada no Windows
  como teste caixa-preta, via UI Automation, só para coletar resultados
  reais. Nada observado nessa execução pode alterar previsões já congeladas
  (o SHA-256 de relatorio/03-casos-de-teste.md está em hashes-originais.txt;
  as colunas de previsão não mudam). Divergências são registradas e
  investigadas no binário.
- Toda conclusão precisa de evidência: arquivo, endereço, string, símbolo ou
  trecho de pseudocódigo. Marque cada afirmação como OBSERVADO ou INFERIDO.
- Se faltar ferramenta ou configuração que exija reiniciar o Claude Code,
  pare e me diga exatamente o que fazer.
- Ao fim de cada fase, salve o entregável, resuma e espere eu responder
  "continue".

## Fases
0. Ambiente: confirme que as ferramentas do REA aparecem nesta sessão e que
   o Ghidra funciona, testando com ./binarios/CalculatorApp.exe (pequeno).
1. Inventário: arquivos, tipo, arquitetura e hash; AppxManifest.xml;
   executável, DLLs, .winmd, .pri, dependências. Indique qual binário contém
   o motor de cálculo e qual contém a interface, com evidência.
2. Mapa estrutural: imports/exports, strings, RTTI e classes C++, vtables,
   tipos WinRT dos .winmd. Mapa de módulos e de comunicação
   (UI -> view model -> motor).
3. Features, uma por vez:
   a) operações básicas e divisão por zero
   b) histórico e memória
   c) modo científico (funções, graus/radianos)
   d) modo programador (bases, bit a bit, tamanhos de palavra)
   e) conversão de unidades
   f) motor numérico (representação e precisão)
   Para cada: ponto de entrada, cadeia de chamadas, estruturas de dados,
   regras e casos de borda.
   Toda subfase da Fase 3 (a partir da 3b) termina com este ciclo, nesta ordem:
   1. análise estática documentada em relatorio/02-features/<feature>.md;
   2. casos de teste com as previsões num arquivo próprio,
      relatorio/03<x>-casos-de-teste.md (x = letra da subfase). O
      relatorio/03-casos-de-teste.md continua congelado e não é tocado;
   3. SHA-256 do arquivo de casos gravado em hashes-originais.txt ANTES de
      qualquer execução. A partir daí as colunas de previsão não mudam;
   4. execução caixa-preta com trabalho/automacao/rodar-casos.ps1 (mesma
      exceção da Fase 4: só UI Automation na Calculadora instalada);
   5. comparação previsto × real com taxa de acerto por bloco, na seção de
      resultados do 02-features/<feature>.md. Leituras feitas por captura
      de tela (expressões, listas) indicam se foram transcritas
      manualmente. Divergências são investigadas no binário.
4. Casos de teste: entradas e resultados previstos pela análise, para eu
   executar manualmente na Calculadora no Windows e devolver os resultados.
5. Reimplementação em Python em ./reimpl, só a partir do que foi documentado,
   com testes usando os casos da Fase 4 que eu confirmar.

## Entregáveis em ./relatorio
00-inventario.md, 01-arquitetura.md, 02-features/<feature>.md,
03-casos-de-teste.md, 04-lacunas.md (o que não foi possível determinar e por quê).

## Adendo (2026-10-24): demonstração visual
Atividade posterior ao experimento principal, feita depois de concluídas a análise,
a validação e a reimplementação. As regras acima continuam valendo sem alteração.
- Para produzir a demonstração visual do README, a Calculadora instalada foi executada
  como caixa-preta (entrada de teclado e mouse, UI Automation e captura de tela), lado a
  lado com a GUI da reimplementação, recebendo as mesmas entradas.
- O modo Programador foi demonstrado à parte: a GUI da original ao lado da saída real
  da CLI em Python, porque a GUI da reimplementação não tem esse modo.
- Artefatos em docs/assets/; scripts de geração em trabalho/demo/.
- Esta exceção vale só para gerar essas demonstrações documentadas. Ela não autoriza
  executar binários durante a análise estática e não altera as regras de congelamento
  das previsões, de integridade dos hashes nem de comparação dos resultados. Nada
  observado nessa execução alimenta relatórios, casos de teste, resultados ou a
  reimplementação.
