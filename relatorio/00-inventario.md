# 00 — Inventário

Alvo: `Microsoft.WindowsCalculator` 11.2607.0.0 x64 (pasta `./binarios`, somente leitura).
Fase 1 concluída em 2026-10-22. Análise só estática: nada foi executado.

Convenção: **[O]** = OBSERVADO (lido diretamente do artefato); **[I]** = INFERIDO (conclusão
a partir de observações, com a cadeia de raciocínio indicada).

## Resumo

| Pergunta | Resposta | Evidência principal |
|---|---|---|
| Onde está o **motor de cálculo**? | `CalcViewModel.dll` (C++ nativo, motor linkado estaticamente) [I, forte] | RTTI `CalculationManager::CalculatorManager`; construtor 0x18010cdf0 chama `FUN_180121ec0(10, 32)`, que inicializa aritmética de precisão arbitrária (§8.1) |
| Onde está a **interface**? | `CalculatorApp.dll` (C# compilado AOT por .NET Native), com o XAML compilado (XBF) em `resources.pri`; `CalculatorApp.exe` é só um lançador [I, forte] | manifesto, imports do runtime .NET Native, 27 URIs `ms-appx:///Views/*.xaml`, 32 XBF no PRI (§8.2) |
| Como a UI chega ao motor? | ativação WinRT: `CalculatorApp.dll` → `RoGetActivationFactory` → manifesto → `CalcViewModel.dll!DllGetActivationFactory` [I] | §7.3 |
| Motor de **gráficos** | `omsautimmss.dll` ("Microsoft Math Engine", do Office), via `GraphingImpl.dll` ← `GraphControl.dll` [O/I] | §7.3 |

## 1. Método e artefatos de trabalho

| Artefato | Conteúdo |
|---|---|
| `trabalho/scripts/pe_inventario.py` | parser PE próprio (biblioteca padrão), escrito a partir da especificação PE/COFF: cabeçalhos, seções, imports, delay-imports, exports, CLR, debug/PDB, VERSIONINFO |
| `trabalho/scripts/rtti_vtables.py` | recuperação de RTTI MSVC x64 (TypeDescriptor → CompleteObjectLocator → vftable) |
| `trabalho/fase1-pe.json` | saída do parser PE para os 224 arquivos |
| `trabalho/fase1-hashes-completos.txt` | SHA-256 de todos os 224 arquivos |
| `trabalho/fase1-winmd-tipos.json` | tipos WinRT dos três `.winmd` do aplicativo |
| `trabalho/rtti/*.json` | classes RTTI e vftables de `CalcViewModel`, `GraphControl`, `GraphingImpl` e `TraceLogging` |
| `trabalho/strings/*.txt` | strings ASCII e UTF-16 (com offset de arquivo) dos 5 PEs principais |
| `trabalho/fase1-evidencias.json` | bundle de Evidence do REA (16 registros) |
| `trabalho/ghidra/CalcViewModel.dll.snapshot` | snapshot da sessão Ghidra, para reaproveitar na Fase 2 |

Ferramentas: REA 6.7.0 com Ghidra 12.1.4 (decompilação, xrefs) e `rea-dotnet-static` (metadados
`.winmd`), mais `file`, `strings`, `openssl` e os scripts acima.

## 2. Integridade

- [O] `sha256sum -c hashes-originais.txt`: 15/15 OK, antes e depois da análise.
- [O] O `AppxBlockMap.xml` lista 221 arquivos (HashMethod SHA-256). Todos estão em `./binarios`, com o
  tamanho declarado, e **os 501 hashes de bloco (64 KiB) conferem**. Os únicos arquivos fora do
  BlockMap são os esperados: `AppxBlockMap.xml`, `AppxSignature.p7x` e `AppxMetadata/CodeIntegrity.cat`.
- [O] `AppxSignature.p7x` = cabeçalho `PKCX` + PKCS#7. Certificados: `CN=Microsoft Corporation`, emitido
  por `Microsoft Marketplace CA G 023` → `Microsoft MarketPlace PCA 2011` → `Microsoft Root
  Certificate Authority 2011`. A assinatura **não** foi verificada criptograficamente; só a cadeia foi listada.
- [I] A cópia em `./binarios` é idêntica, byte a byte, ao conteúdo descrito pelo BlockMap do pacote assinado.
- Os SHA-256 completos estão em `trabalho/fase1-hashes-completos.txt`. Os 5 arquivos sem hash em
  `hashes-originais.txt` (`AppxManifest.xml`, `AppxBlockMap.xml`, `AppxSignature.p7x`,
  `AppxMetadata/CodeIntegrity.cat`, `resources.pri`) estão cobertos lá.

## 3. Pacote: `AppxManifest.xml` [O]

| Item | Valor |
|---|---|
| Identity | `Microsoft.WindowsCalculator`, 11.2607.0.0, x64, `CN=Microsoft Corporation, …` |
| Aplicativo | `Id="App"`, `Executable="CalculatorApp.exe"`, `EntryPoint="Calculator.App"`, múltiplas instâncias permitidas |
| Família alvo | `Windows.Universal`, min 10.0.19041.0, testado até 10.0.26100.0 |
| Dependências (pacotes-framework) | `Microsoft.UI.Xaml.2.8` ≥ 8.2501.31001.0; `Microsoft.NET.Native.Framework.2.2` ≥ 2.2.29512.0; `Microsoft.NET.Native.Runtime.2.2` ≥ 2.2.28604.0; `Microsoft.VCLibs.140.00` ≥ 14.0.33519.0; `Microsoft.VCLibs.140.00.UWPDesktop` ≥ 14.0.33728.0 |
| Recursos | idiomas `EN-US`, `EN-GB`; escala `200` |
| Protocolos | `calculator:` e `ms-calculator:` |
| Extensão | `com.microsoft.windows.dontmaximizeonsmallscreen` |
| Capacidades | `internetClient`, `rescap:appLicensing` |
| Build | `TargetFrameworkMoniker=.NETCore,Version=v5.0`; `OptimizingToolset=ilc.exe`; `ilc.exe 2.2.31116.00`; VS 18.0; `MakePri.exe 10.0.26100.8249` |

Classes WinRT ativáveis (`windows.activatableClass.inProcessServer`):

| DLL servidora | Classes |
|---|---|
| `CalcViewModel.dll` | 37 classes `CalculatorApp.ViewModel.*`, entre elas `StandardCalculatorViewModel`, `UnitConverterViewModel`, `DateCalculatorViewModel`, `GraphingCalculatorViewModel`, `MemoryItemViewModel`, `Common.DateCalculation.DateCalculationEngine`, `Common.CopyPasteManager`, `Common.NavCategory`, `Snapshot.*` (CalcManagerSnapshot, CalcManagerToken, BinaryCommand, UnaryCommand, OperandCommand, Parentheses…) |
| `GraphControl.dll` | `GraphControl.Equation`, `Grapher`, `KeyGraphFeaturesInfo`, `Variable`, `GraphControl_XamlTypeInfo.XamlMetaDataProvider` |
| `TraceLogging.dll` | `TraceLogging.TraceLoggingCommon` |
| `Microsoft.Web.WebView2.Core.dll` | 6 classes `Microsoft.Web.WebView2.Core.CoreWebView2*` |

## 4. Arquivos PE

| Arquivo | Bytes | SHA-256 (16 primeiros) | Formato | Linker | Timestamp PE (UTC) | Subsistema | CLR | PDB (CodeView) | Exports |
|---|---:|---|---|---|---|---|---|---|---|
| `CalcViewModel.dll` | 2216448 | `072cd589ec97875b` | PE32+ x64 DLL | 14.51 | 2026-08-05T17:07:49 | windows_cui | não | `C:\__w\1\b\Release\x64\CalcViewModel\CalcViewModel.pdb` | DllCanUnloadNow, DllGetActivationFactory |
| `CalculatorApp.ViewModel.winmd` | 84992 | `547b38048cfa4030` | PE32 x86 DLL | 14.51 | 2026-08-05T17:07:49 | windows_cui | WindowsRuntime 1.4 | — | — |
| `CalculatorApp.dll` | 6722560 | `e08455206dab3ab2` | PE32+ x64 DLL | 11.0 | 2026-08-05T17:11:30 | windows_gui | não | `C:\__w\1\s\src\x64\Release\Calculator\ilc\CalculatorApp.pdb` | DllGetClassObject, RHBinder__ShimExeMain |
| `CalculatorApp.exe` | 19968 | `f26a20f8bd65fd23` | PE32+ x64 EXE | 11.0 | 2026-08-05T17:11:30 | windows_gui | não | — | — |
| `GraphControl.dll` | 730624 | `4ab3e8343143f61b` | PE32+ x64 DLL | 14.51 | 2026-08-05T17:06:08 | windows_cui | não | `C:\__w\1\b\Release\x64\GraphControl\GraphControl.pdb` | DllCanUnloadNow, DllGetActivationFactory |
| `GraphControl.winmd` | 23040 | `3e635fdcb0198a30` | PE32 x86 DLL | 14.51 | 2026-08-05T17:05:56 | windows_cui | WindowsRuntime 1.4 | — | — |
| `GraphingImpl.dll` | 83968 | `80d4ff11e607d651` | PE32+ x64 DLL | 14.51 | 2026-08-05T17:04:52 | windows_cui | não | `C:\__w\1\b\Release\x64\GraphingImpl\GraphingImpl.pdb` | `Graphing::IMathSolver::CreateMathSolver` (C++ decorado) |
| `Microsoft.UI.Xaml.winmd` | 286208 | `f0537d83601c6cad` | PE32 x86 DLL | 11.0 | 2025-01-31T19:31:49 | windows_cui | WindowsRuntime 1.4 | — | — |
| `Microsoft.Web.WebView2.Core.dll` | 773712 | `05c06241310ceeb2` | PE32+ x64 DLL | 14.41 | 2024-11-10T08:23:58 | windows_cui | não | `Microsoft.Web.WebView2.Core.pdb` | DllCanUnloadNow, DllGetActivationFactory |
| `Microsoft.Web.WebView2.Core.winmd` | 131656 | `436bb2630685d31b` | PE32 x86 DLL | 11.0 | 2024-11-10T08:23:05 | windows_cui | WindowsRuntime 1.4 | — | — |
| `TraceLogging.dll` | 32768 | `7311509af3a4e207` | PE32+ x64 DLL | 14.51 | 2026-08-05T17:04:56 | windows_cui | não | `C:\__w\1\b\Release\x64\TraceLogging\TraceLogging.pdb` | DllCanUnloadNow, DllGetActivationFactory |
| `TraceLogging.winmd` | 4608 | `d18086d94b98391c` | PE32 x86 DLL | 14.51 | 2026-08-05T17:04:56 | windows_cui | WindowsRuntime 1.4 | — | — |
| `WebView2Loader.dll` | 165968 | `462b36fd1be6ca9f` | PE32+ x64 DLL | 14.0 | 2024-11-09T18:33:54 | windows_cui | não | `WebView2Loader.dll.pdb` | CreateCoreWebView2Environment[WithOptions], GetAvailableCoreWebView2BrowserVersionString[WithOptions], CompareBrowserVersions |
| `clrcompression.dll` | 66960 | `b16a75adce8c335e` | PE32+ x64 DLL | 14.16 | 2022-05-27T16:06:39 | windows_cui | não | `D:\a\_work\1\s\corefx\bin\obj\Windows_NT.x64.Release\native_aot\clrcompression\Release\clrcompression.pdb` | 7× `CompressionNative_*` (zlib: Deflate/Inflate/Crc32) |
| `omsautimmss.dll` | 6811496 | `70ed287c9af00c14` | PE32+ x64 DLL | 14.24 | 2020-08-08T06:28:39 | windows_cui | não | `d:\dbs\el\od\target\x64\ship\math_solverengine\x-none\omsautimmss.pdb` | `MathSolverEngine::CreateMathSolver` (C++ decorado) |

VERSIONINFO [O]:

| Arquivo | FileDescription | FileVersion | ProductName |
|---|---|---|---|
| `CalculatorApp.exe` / `CalculatorApp.dll` | Calculator | 11.2607.0.0 | Microsoft Calculator |
| `CalcViewModel.dll` | CalcViewModel.exe (sic) | 11.2607.0.0 | Microsoft Calculator ViewModel |
| `GraphControl.dll` | GraphControl.exe (sic) | 11.2607.0.0 | Microsoft Calculator GraphControl |
| `TraceLogging.dll` | TraceLogging.exe (sic) | 11.2607.0.0 | Microsoft Calculator TraceLogging |
| `omsautimmss.dll` | Microsoft Math Engine Public API | 16.0.13208.10000 | Microsoft Office |
| `Microsoft.Web.WebView2.Core.dll` | Microsoft Edge Embedded Browser WinRT Component | 1.0.2903.40 | (idem) |
| `WebView2Loader.dll` | Microsoft Edge Embedded Browser WebView Loader | 1.0.2903.40 | (idem) |
| `clrcompression.dll` | (o parser simplificado não extraiu) | 4.6.31327.01, branch `release/uwp6.2-MSRC` | Microsoft® .NET Framework |

Natureza de cada PE:
- [O] Os `.winmd` são PE32 com cabeçalho CLI, metadados `WindowsRuntime 1.4`, IL-only e sem código executável.
- [O] `CalcViewModel.dll`, `GraphControl.dll` e `TraceLogging.dll` importam `vccorlib140_app.DLL`
  (C++/CX) e exportam `DllGetActivationFactory`. [I] São componentes WinRT em C++ nativo.
- [O] `CalculatorApp.dll` não tem cabeçalho CLR, tem **zero** TypeDescriptors RTTI e importa
  `mrt100_app.dll` (45 funções `Rhp*`/`RhTypeCast_*`) e `SharedLibrary.dll`. [I] É código gerenciado
  compilado para nativo pelo .NET Native (confirmado pelo manifesto de build embutido, §8.2).

## 5. Arquivos que não são PE

| Arquivo | Tipo | Observação |
|---|---|---|
| `AppxManifest.xml` | XML (CRLF) | §3 |
| `AppxBlockMap.xml` | XML | 221 arquivos, 501 blocos; §2 |
| `AppxSignature.p7x` | `PKCX` + PKCS#7 DER | §2 |
| `AppxMetadata/CodeIntegrity.cat` | catálogo PKCS#7 assinado | não analisado em detalhe |
| `resources.pri` | PRI, magic `mrm_pri2` | §6 |
| `Assets/` | 203 PNG + `CalculatorIcons.ttf` | ícones e tiles (variantes `scale-*`, `contrast-*`), ícones de modo (`Standard`, `Scientific`, `Programmer`, `Date`, `Graphing`) e a fonte "Calculator Fluent Icons" v1.07 |

## 6. `resources.pri` [O]

- Magic `mrm_pri2`. Seções encontradas: `[mrm_decn_info]`, `[mrm_pridescex]`, `[mrm_hschemaex]`,
  `[def_hnamesx]`, `[mrm_res_map2_]`, `[mrm_dataitem]`.
- **32 XBF (XAML compilado) embutidos**: há 32 ocorrências do magic `XBF\0` e 32 nomes `.xbf`, entre
  eles `App`, `MainPage`, `Calculator`, `NumberPad`, `OperatorsPanel`, `CalculatorStandardOperators`,
  `CalculatorScientificOperators`, `CalculatorScientificAngleButtons`, `CalculatorProgrammer{Operators,RadixOperators,BitFlipPanel,DisplayPanel}`,
  `HistoryList`, `Memory`, `MemoryListItem`, `UnitConverter`, `DateCalculator`, `GraphingCalculator`,
  `GraphingNumPad`, `GraphingSettings`, `EquationInputArea`, `EquationStylePanelControl`,
  `KeyGraphFeaturesPanel`, `SupplementaryResults`, `Settings`, `SettingsCard`, `SettingsExpander`,
  `TitleBar`, `DelighterUnitStyles`, `Compact`, `Generic`, `generic`.
- Nomes de subárvore de recursos encontrados: `Resources`, `Files`, **`CEngineStrings`** (ASCII).
- Qualificadores vistos: `EN-US` (UTF-16) e 22 nomes de arquivo `Assets\*.scale-200*.png`.
- O parse completo do PRI (valores das strings) fica para a Fase 2/3. Ele será necessário para as
  mensagens de erro do motor, como a de divisão por zero.

## 7. Dependências

### 7.1 DLLs importadas que não estão no pacote [O]
`mrt100_app.dll`, `SharedLibrary.dll` [I: pacotes `Microsoft.NET.Native.Runtime/Framework.2.2`];
`vccorlib140_app.DLL`, `MSVCP140_APP.dll`, `CONCRT140_APP.dll`, `VCRUNTIME140_APP.dll`,
`VCRUNTIME140_1_APP.dll` [I: `Microsoft.VCLibs.140.00`]; sistema: `kernel32`, `ADVAPI32`, `ole32`,
`OLEAUT32`, `BCrypt`, `d2d1`, `d3d11`, `dxgi`, `DWrite`, além de `api-ms-win-*`.
A implementação do WinUI 2.8 (`Microsoft.UI.Xaml.dll`) não está no pacote; só a `.winmd` está.

### 7.2 Imports entre módulos do pacote [O]

```
CalculatorApp.exe  --import-->  CalculatorApp.dll!RHBinder__ShimExeMain
CalculatorApp.dll  --import-->  clrcompression.dll (Deflate/Inflate)
GraphControl.dll   --delay-import-->  GraphingImpl.dll
GraphingImpl.dll   --import-->  omsautimmss.dll (CreateMathSolver)
```

### 7.3 Ligações por ativação WinRT [I]

`CalculatorApp.dll` importa `RoGetActivationFactory` [O] e contém, em UTF-16, 258 ocorrências de
nomes `CalculatorApp.ViewModel.*`, 56 de `GraphControl.*` e 1 de `TraceLogging.*` [O]. O manifesto
associa esses ActivatableClassIds às DLLs servidoras (§3) [O]. `CalcViewModel.dll` e `GraphControl.dll`
contêm `TraceLogging.TraceLoggingCommon` em UTF-16 [O]. A cadeia provável é:

```
CalculatorApp.dll (UI, C#/.NET Native)
   ├─ RoGetActivationFactory("CalculatorApp.ViewModel.*") ─► CalcViewModel.dll  (view models C++/CX + motor)
   ├─ RoGetActivationFactory("GraphControl.*")            ─► GraphControl.dll ─► GraphingImpl.dll ─► omsautimmss.dll
   ├─ RoGetActivationFactory("Microsoft.Web.WebView2.*")  ─► Microsoft.Web.WebView2.Core.dll (+ WebView2Loader.dll)
   └─ (CalculatorApp, CalcViewModel, GraphControl) ──────► TraceLogging.dll (telemetria)
```

## 8. Qual binário contém o quê

### 8.1 Motor de cálculo: `CalcViewModel.dll`

1. [O] RTTI (strings `.?AV…` em `.rdata`; endereços = string do TypeDescriptor):
   `CalculationManager::CalculatorManager` (0x180204c30), `CalculationManager::CalculatorHistory`
   (0x180205278), `CalculationManager::HISTORYITEM`, `CalculationManager::IResourceProvider` (0x1801ef8b8),
   classes de comando de expressão `CBinaryCommand` (0x1801f2ad8), `CUnaryCommand`, `COpndCommand`, `CParentheses`,
   `IExpressionCommand`, `ICalcDisplay` (0x1801efb08), `IHistoryDisplay`, e `UnitConversionManager::UnitConverter`
   (0x180205210). Nenhum outro PE do pacote tem esses nomes: `CalculatorApp.dll` tem 0 RTTI, e os
   namespaces RTTI de `GraphControl`/`GraphingImpl`/`TraceLogging` são outros.
2. [O] Pelo script RTTI, o vftable de `CalculatorManager` está em **0x18018ac40** (11 entradas). O Ghidra
   (`xrefs`) mostra referências a ele só em 0x18010ce0a/0x18010ce11, dentro de `FUN_18010cdf0`.
   O pseudocódigo (Evidence `ev_a7872811…`) mostra o **construtor**: grava o vftable, cria dois objetos
   `CalculatorHistory` (campo `0x14` = 20) e termina com `FUN_180111b10(this[6])` e
   **`FUN_180121ec0(10, 0x20)`**.
3. [O] `FUN_180121ec0(uint p1, int p2)` (Evidence `ev_b802f4cd…`):
   `DAT_1802054fc = ceil(31.0 / log2(p1)) - 1`; cria cerca de 20 constantes globais com `FUN_18012f780(n)` para
   n ∈ {0, 1, 2, 6, 10, −1, 0xFFFF, 180, 200, 360, 400, 100000, 3249, −1000}; cria estruturas com
   `FUN_18012e9d0(0x21)` preenchidas com {1, 1, 0, k} para k ∈ {1, 2, 5, 6, 10, 0x55, 100}; chama
   `FUN_1801309b0(x, 0x40|0x20|0x1F, 0x80000000, p2)` e outras rotinas sobre essas constantes.
   - [I] É a inicialização de uma biblioteca de aritmética de **precisão arbitrária**, com `p1` = base (10)
     e `p2` = precisão (32 dígitos). `ceil(31/log2(base)) - 1` dá quantos dígitos da base cabem numa palavra
     de 31 bits (9 para base 10). 180/200/360/400 combinam com conversão de ângulos (graus/grados), e
     64/32/31 bits com tamanhos de palavra do modo programador. A confirmar na Fase 3f.
4. [O] `FUN_180111b10` percorre a tabela 0x18018af40–0x18018b8c0 (152 pares ponteiro+tamanho de strings
   UTF-16: `"0"`, `"62"`, `"2"` … `"Floor"`, `"Ceil"`, `"Nand"`, `"Nor"`, `"CubeRoot"`, `"ProgrammerMod"`)
   e, para cada par, chama o slot +8 do vftable do objeto recebido (`this[6]`, terceiro argumento do construtor).
   `CalcViewModel.dll` contém `CEngineStrings` em UTF-16 (offset de arquivo 0x176350), e o `resources.pri`
   tem uma subárvore `CEngineStrings`.
   - [I] O motor carrega suas strings localizadas por `IResourceProvider` a partir de `CEngineStrings`.
5. [O] `CalcViewModel.dll` não importa nenhuma outra DLL do pacote, só CRT, VCLibs e WinRT do sistema.
   - [I] O motor está **linkado estaticamente** em `CalcViewModel.dll`; não existe DLL de motor separada.
6. [O] `CalcViewModel.dll` também contém (pelo manifesto e pelo RTTI) a conversão de unidades
   (`UnitConversionManager::UnitConverter`), o cálculo de datas
   (`CalculatorApp.ViewModel.Common.DateCalculation.DateCalculationEngine`) e o `CopyPasteManager`, cujos
   validadores de entrada são regex em UTF-16 (offsets de arquivo 0x179018–0x1792e0, por exemplo
   `[0-1]+((_|'|\`)[0-1]+)*`).
7. [O] Busca por bytes em todos os PEs e no PRI: `CalculatorManager@CalculationManager`, `CBinaryCommand`,
   `ICalcDisplay` e `UnitConverter@UnitConversionManager` só aparecem em `CalcViewModel.dll`.

Exceção: o modo **gráfico** usa outro motor matemático, `omsautimmss.dll` (Office "Math Engine Public API",
PDB `math_solverengine`), por meio de `GraphingImpl.dll` (export `Graphing::IMathSolver::CreateMathSolver`) [O/I].

### 8.2 Interface: `CalculatorApp.dll` (com `CalculatorApp.exe` e `resources.pri`)

1. [O] Manifesto: `Executable="CalculatorApp.exe"`, `EntryPoint="Calculator.App"`, `OptimizingToolset=ilc.exe`,
   dependências `Microsoft.NET.Native.*` e `Microsoft.UI.Xaml.2.8`.
2. [O] `CalculatorApp.exe` tem 2 procedimentos; `entry` (0x180008000) só salta para
   `CalculatorApp.dll!RHBinder__ShimExeMain` (Fase 0, Evidence `ev_c46c6b48…`).
3. [O] `CalculatorApp.dll`, offset de arquivo 0x337310: manifesto de build do .NET Native, com
   `Tool chain: ilc.exe / nutc_driver.exe / rhbind.exe / sg.exe 2.2.31116` e uma lista `Framework:` de
   assemblies de entrada (`Calculator.ManagedViewModels.dll`, `CommunityToolkit.*` 8.2, `mscorlib`,
   187 `System.*`…). [I] O código C# do app e das bibliotecas .NET foi compilado AOT para dentro desta DLL.
4. [O] Strings UTF-16 com nomes de tipos de UI: `CalculatorApp.MainPage`, `Calculator`, `NumberPad`,
   `OperatorsPanel`, `CalculatorStandardOperators`, `CalculatorScientificOperators`, `CalculatorProgrammer*`,
   `HistoryList`, `Memory`, `UnitConverter`, `DateCalculator`, `GraphingCalculator`, `Settings`, `TitleBar`;
   12 controles `CalculatorApp.Controls.*` (`CalculationResult`, `CalculatorButton`, `EquationTextBox`,
   `MathRichEditBox`, `RadixButton`…); conversores; `CalculatorApp.ManagedViewModels.ApplicationViewModel`;
   27 URIs `ms-appx:///Views/*.xaml`; 187 ocorrências de `Microsoft.UI.Xaml.`.
5. [O] Os 32 XBF do `resources.pri` têm os mesmos nomes das views referenciadas.
6. [I] A UI é XAML (WinUI 2.8) com code-behind C#. Ela delega estado e lógica aos view models C++ de
   `CalcViewModel.dll` (§7.3), exceto `ApplicationViewModel`, que é gerenciado.

### 8.3 Componentes auxiliares

| Componente | Papel [I, salvo indicação] |
|---|---|
| `GraphControl.dll` + `.winmd` | controle XAML de gráfico (Direct2D/D3D11/DWrite [O: imports]); tipos `Grapher`, `Equation`, `Variable`, `KeyGraphFeaturesInfo`, `ErrorType`, `EvaluationErrorCode`, `SyntaxErrorCode` [O] |
| `GraphingImpl.dll` | adaptador `Graphing::IMathSolver` → `omsautimmss.dll` [O: export/import] |
| `omsautimmss.dll` | motor de álgebra simbólica e gráficos do Office (1503 TypeDescriptors RTTI, namespaces `MathSolverEngine`, `GraphEngine2D`…) [O] |
| `TraceLogging.dll` + `.winmd` | telemetria (`TraceLogging.TraceLoggingCommon`) |
| `Microsoft.Web.WebView2.Core.dll` + `.winmd`, `WebView2Loader.dll` | WebView2 1.0.2903.40; uso a determinar na Fase 2 |
| `clrcompression.dll` | zlib nativo do .NET (`CompressionNative_*`), importado por `CalculatorApp.dll` [O] |
| `Microsoft.UI.Xaml.winmd` | metadados do WinUI 2.8, cuja implementação está no pacote-framework |

### 8.4 Tipos WinRT dos `.winmd` [O] (rea-dotnet-static, metadados completos)

| winmd | TypeDefs | Métodos | Namespaces |
|---|---:|---:|---|
| `CalculatorApp.ViewModel.winmd` | 161 (+`<Module>`) | 1189 | `.ViewModel` (60), `.ViewModel.Common` (63), `.Common.Automation` (9), `.Common.DateCalculation` (5), `.Snapshot` (23), `.DataLoaders` (1) |
| `GraphControl.winmd` | 28 | 264 | `GraphControl` (26), `GraphControl.GraphControl_XamlTypeInfo` (2) |
| `TraceLogging.winmd` | 3 | 10 | `TraceLogging` |

Tipos de `CalculatorApp.ViewModel.winmd` que não são interface (69): `StandardCalculatorViewModel`,
`HistoryViewModel`, `HistoryItemViewModel`, `MemoryItemViewModel`, `UnitConverterViewModel`,
`DateCalculatorViewModel`, `GraphingCalculatorViewModel`, `EquationViewModel`, `VariableViewModel`,
`Common.NumbersAndOperatorsEnum`, `Common.NumberBase`, `Common.BitLength`, `Common.RadixType`,
`Common.ViewMode`, `Common.CopyPasteManager`, `Common.DateCalculation.DateCalculationEngine`,
`Snapshot.*`, entre outros (lista completa em `trabalho/fase1-winmd-tipos.json`). O mapeamento de
membros fica para a Fase 2.

## 9. Lacunas desta fase (também registradas em `04-lacunas.md`)

- Os PDBs não estão disponíveis: todas as funções nativas aparecem sem nome (`FUN_…`), e os nomes de
  classe vêm só do RTTI.
- O pacote só tem recursos `EN-US`/`EN-GB`. Pacotes de recursos de outros idiomas (por exemplo pt-BR)
  não estão em `./binarios`, então mensagens localizadas em outros idiomas não podem ser lidas.
- `CalculatorApp.dll` é .NET Native (não é NativeAOT moderno nem IL). O REA não recupera metadados
  .NET desse formato; a análise dele vai depender de strings e do Ghidra.
- O uso do WebView2 não foi determinado.
- O parse completo do `resources.pri` (valores das strings `CEngineStrings`) não foi feito.
- A assinatura PKCS#7 e o catálogo `CodeIntegrity.cat` não foram verificados criptograficamente.
