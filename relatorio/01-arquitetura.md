# 01 — Arquitetura (Fase 2: mapa estrutural)

Alvo: `Microsoft.WindowsCalculator` 11.2607.0.0 x64. Fase 2 concluída em 2026-10-22, só com análise
estática: nada foi executado. Hashes conferidos antes da análise (15/15 OK).

Escopo combinado: o foco é `CalcViewModel.dll`. De `CalculatorApp.dll` entra só o necessário para a
ligação UI → view model. O modo gráfico (GraphControl, GraphingImpl, omsautimmss) ficou fora (ver
`04-lacunas.md`, L8).

Convenção: **[O]** = OBSERVADO (lido do artefato: bytes, metadados, pseudocódigo); **[I]** = INFERIDO
(conclusão a partir de observações, com a cadeia de raciocínio indicada). Endereços são VAs com image
base 0x180000000. "slot n" = índice de 8 bytes numa vftable. Nomes como `CalculatorManager::SendCommand`
são **rótulos** atribuídos nesta análise quando não há símbolo; os nomes de classe vêm do RTTI e os de
métodos WinRT vêm da `.winmd`.

## Resumo

```
CalculatorApp.dll  (UI: XAML/WinUI 2.8 + C# .NET Native; ApplicationViewModel gerenciado)
  │  {x:Bind}/{Binding} em propriedades WinRT; CalculatorButton.ButtonId=<NumbersAndOperatorsEnum> → ButtonPressed
  │  ativação WinRT (RoGetActivationFactory → manifesto → CalcViewModel.dll!DllGetActivationFactory)
  ▼
CalcViewModel.dll ─ camada VM (C++/CX, 44 runtime classes, 0x180001000–0x18010cdf0)
  │  StandardCalculatorViewModel ── ButtonPressed (DelegateCommand) → OnButtonPressed 0x1800d5aa0
  │      ├─ +0x150 CalculatorDisplay   (implementa ICalcDisplay; weak ref p/ o VM e p/ o HistoryViewModel)
  │      ├─ +0x168 EngineResourceProvider (implementa IResourceProvider; ResourceLoader "CEngineStrings")
  │      ├─ +0x178 CalculatorManager  (objeto embutido, ~0x100 bytes)
  │      └─ +0x048 HistoryViewModel   (recebe &CalculatorManager)
  ▼
CalcViewModel.dll ─ motor "CalcManager" (C++ estático, 0x18010cdf0–0x180143000, ~726 funções)
     CalculatorManager::SendCommand 0x18010d3d0 ──► engine::ProcessCommand 0x180112db0
        3 instâncias de engine (0x11a8 bytes): padrão (+0x20), científica (+0x18), programador (+0x28)
        aritmética de precisão arbitrária ("ratpak"; init 0x180121ec0(base, precisão))
     ◄── retorno: engine → ICalcDisplay (CalculatorManager repassa) → CalculatorDisplay → VM
         → INotifyPropertyChanged("DisplayValue", "IsInError", …) → binding XAML
```

| Pergunta da fase | Resposta curta | Seção |
|---|---|---|
| Imports/exports | `CalcViewModel.dll` exporta só `DllGetActivationFactory`/`DllCanUnloadNow`; não importa nenhuma DLL do pacote [O] | §2 |
| Strings | 1246 UTF-16 em `CalcViewModel.dll`, organizadas em 15 categorias (propriedades, chaves de recurso, regex de colar, telemetria, URLs de câmbio…) [O] | §3 |
| RTTI / classes C++ | 836 TypeDescriptors, 398 com vftable; hierarquia completa recuperada [O] | §4 |
| Tipos WinRT | 161 tipos (92 interfaces, 44 classes, 16 enums, 5 delegates, 4 structs); 558 métodos ligados aos slots nativos [O] | §5 |
| UI → VM → motor | cadeia completa, com endereços, do botão até `ProcessCommand` e de volta até o binding [O/I] | §6 |

## 1. Método e artefatos novos

| Artefato | Conteúdo |
|---|---|
| `trabalho/scripts/rtti_hierarquia.py` | estende `rtti_vtables.py`: ClassHierarchyDescriptor + BaseClassArray (bases, `mdisp`) e um demangler mínimo de nomes de tipo MSVC |
| `trabalho/rtti/CalcViewModel.hierarquia.json` | 398 classes com bases e vftables; 438 TypeDescriptors sem vftable |
| `trabalho/scripts/winmd_dump.py` | leitor ECMA-335 próprio (tabelas, heaps, assinaturas, Property/Event/Constant/CustomAttribute/InterfaceImpl) |
| `trabalho/winmd/CalculatorApp.ViewModel.{json,txt}` | todos os tipos WinRT com GUIDs, atributos, propriedades, eventos, métodos e valores de enum |
| `trabalho/scripts/winrt_vtable_map.py` → `trabalho/winmd/vtable-map.{json,md}` | 62 interfaces / 558 métodos WinRT → thunk ABI → implementação C++ |
| `trabalho/scripts/iid_scan.py` → `trabalho/winmd/iid-scan.json` | IIDs das interfaces VM procurados nos PEs |
| `trabalho/winmd/ui-xaml-member-strings.json` | strings `Tipo.Membro` do XAML type info de `CalculatorApp.dll` |
| `trabalho/scripts/hstring_globais.py` → `trabalho/hstring-globais.json` | 108 HSTRINGs globais → literal (chaves de recurso, propriedades, ids de anúncio, configuração, tipos) |
| `trabalho/scripts/pe_va.py` | leitura de bytes por VA, direto do arquivo |
| `trabalho/pseudocodigo/*.c` + `INDICE.tsv` | pseudocódigo Ghidra das funções citadas, com o Evidence ID |
| `trabalho/fase2-evidencias.json` | bundle de Evidence do REA (39 registros, 0 unknowns) |
| `trabalho/pri/` | parse do `resources.pri` e dos XBF (§7) |

Ferramentas: REA 6.7.0 / Ghidra 12.1.4. A sessão foi reaberta a partir do snapshot da Fase 1; a
contagem de linhas de tabela do `inspect_managed_members` (Evidence `ev_4a5b9393…`) bate com a do
parser próprio (Constant 387, Property 487, Event 29, MethodDef 1189, CustomAttribute 604) [O].

## 2. Imports e exports de `CalcViewModel.dll` [O]

- Exports: `DllCanUnloadNow` (RVA 0x143d80) e `DllGetActivationFactory` (RVA 0x143da0). Nada mais.
- Imports agrupados (lista completa em `trabalho/fase1-pe.json`):

| Grupo | DLLs | Uso [I] |
|---|---|---|
| C++/CX | `vccorlib140_app.DLL` (65 funções: `Platform::Details::Heap`, `EventSource*`, `ResolveWeakReference`, `__abi_WinRTraise*`…) | runtime das ref classes WinRT |
| C++ STL/CRT | `MSVCP140_APP` (96: iostreams, locale, `_Xregex_error`, PPL `_TaskEventLogger`), `VCRUNTIME140(_1)_APP`, `CONCRT140_APP` (reader_writer_lock), `api-ms-win-crt-*` | regex (colar), streams, tarefas assíncronas |
| Matemática CRT | `log10, round, ceil, pow, ceilf, log2`; `wcstod, strtod, _wtof, wcstoull, wcstol…` | poucas funções de ponto flutuante: o motor não faz a aritmética com `double` [I, a confirmar na 3f]; `log2` aparece no init do ratpak (Fase 1) |
| WinRT string/erro | `WindowsCreateStringReference`, `WindowsCompareStringOrdinal`… (9), `RoOriginateError` | HSTRING |
| Sistema | localização (`GetLocaleInfoEx`, `ResolveLocaleName`…), tempo, SRW locks, `GetIntegratedDisplaySize` | formatação local, data |

- Não importa nenhuma DLL do pacote, nem `api-ms-win-core-winrt-l1-1-0` (a ativação de tipos do sistema
  passa pelo `vccorlib`) [O].
- `CalculatorApp.dll` (só para a ligação com o VM): a tabela de import do PE tem só `SharedLibrary.dll`
  e `mrt100_app.dll` [O]. `api-ms-win-core-winrt-l1-1-0.dll` e `RoGetActivationFactory` aparecem como
  strings ASCII nos offsets 0x164875/0x1648aa, ao lado de `clrcompression.dll` [O]. [I] São imports
  resolvidos sob demanda pelo runtime do .NET Native, não pela tabela de import do PE.

## 3. Strings de `CalcViewModel.dll` [O]

Fonte: `trabalho/strings/CalcViewModel.dll.txt`, com 1246 strings UTF-16 (offset de arquivo à esquerda).
Categorias:

| Categoria | Exemplos (offset de arquivo) | Uso / ligação |
|---|---|---|
| Nomes de propriedade p/ `PropertyChanged` | `DisplayValue` 0x1870b0, `IsInError` 0x177370, `OpenParenthesisCount` 0x187528, `IsInputEmpty` 0x187558, `HexDisplayValue`…, `ValueBitLength` 0x1879d8 | literais `L"…"` passados a `FUN_180013a60` (RaisePropertyChanged [I]); p.ex. 0x180013ad0 usa `L"IsInError"` |
| Chaves de recurso (`Resources`) | `Format_CalculatorResults`, `Format_MaxDigitsReached`, `NoRightParenthesisAdded_Announcement`, `Format_MemorySave`, `Display_Copied`, `Memory_Cleared`, `HistoryList_Cleared`, `CategoryName_*`, `UnitName_*`/`UnitAbbreviation_*` (312), `Date_*` | parte delas vira HSTRING global na inicialização estática: são 108 globais, que misturam chaves de recurso, nomes de propriedade, ids de anúncio (`DisplayUpdated`, `MaxDigitsReached`…), chaves de configuração (`CURRENCY_UNIT_FROM_KEY`…) e nomes de tipo (`trabalho/hstring-globais.json`) |
| Subárvore do motor | `CEngineStrings` 0x176350 | `EngineResourceProvider` (§6.8) |
| Nomes do enum de botões | `Zero`…`Submit`, `BINPOS0..63`, `NumbersAndOperatorsEnum` 0x17e810 | `ToString` do enum (C++/CX) |
| Funções científicas (narração) | `SineDegrees` 0x17af20, `InverseCotangentGradians`, `HyperbolicSecant`, `DegreeMinuteSecond`, `LogBaseY`, `YRoot` | rótulos de acessibilidade [I] |
| Validação de colar (regex) | `[\s\x85]*` 0x179070, `(?:[-+]?(?:\d+(\.\d*)?|\.\d+))` 0x1790c0, hex/oct/bin `…((_|'|\`)…)*` 0x179120–0x1791d8, sufixos `[uU]?[lL]{0,2}`, prefixos `(0[xX])?`, `(0[nN])?`, `(0[otOT])?`, `(0[byBY])?` | `CopyPasteManager` |
| Erros de colar | `PastedExpressionSizeGreaterThanMaxAllowed`, `InvalidExpressionForPresentMode`, `OperandCountGreaterThanMaxCount`, `ExponentLengthGreaterThanMaxLength` (0x1792f0–0x179480) | `CopyPasteManager::ValidatePasteExpression` / `ExtractOperands` (nomes literais em 0x179350, 0x179430) |
| Motor (asserts) | `C:\__w\1\s\src\CalcManager\UnitConverter.cpp` 0x18a9b0, `…\CalcManager\CalculatorHistory.cpp` 0x18b2e0, `uIdx < m_historyItems.size()` 0x18b348, `tokenList.size() == EXPECTEDSERIALIZEDUNITTOKENCOUNT` | o componente do motor se chama **CalcManager** [O]; é código C++ com `_wassert` |
| Motor (números) | `[+-]?(\d*)[` + `]?(\d*)(?:e[+-]?(\d*))?$` 0x18b3b8/0x18b3d0; `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_@` 0x18b410; `TwoPowX`, `ProgrammerMod` | validação de número e dígitos de base [I] |
| Snapshot | `unhandled command type.` 0x186310, `ill-formed command.` 0x186a50, `Invalid command type` 0x1879f8 | restauração de estado (`Snapshot.*`) |
| Telemetria | `WindowCreated`, `ButtonUsageInSession`, `ModeChanged`, `HistoryItemLoad`, `MemoryItemLoad`, `InputPasted`, `RecallSnapshot`, `RecallRestore`… (0x17d530–0x17db00) | `TraceLogger` → `TraceLogging.TraceLoggingCommon` 0x17e880 |
| Câmbio | `CURRENCY_CONVERTER_STATIC_DATA.txt`, `…_ALL_RATIOS_DATA.txt`, `ms-appx:///DataLoaders/DefaultFromToCurrency.json`, 2 URLs `https://go.microsoft.com/fwlink/?linkid=2093153/2093154&apikey=…` (0x17f3b0, 0x17f490) | `CurrencyDataLoader`; explica a capacidade `internetClient` do manifesto [I] |
| Data | `IsDateDiffMode`, `Date_SameDates`, `Date_OutOfBoundMessage`, `Windows.Globalization.Calendar` | `DateCalculatorViewModel` / `DateCalculationEngine` |
| Gráfico (fora de escopo) | `KGF*`, `EquationHasNoSolution`, `DivideByZero` 0x1840b0, `InvalidEquationSyntax`… | códigos de erro do modo gráfico |
| Build | `C++/WinRT version:2.0.250303.5` (ASCII 0x1862f0) | o módulo mistura C++/CX e C++/WinRT [O] |

Observação: a string `DivideByZero` de 0x1840b0 pertence à lista de erros do **modo gráfico** (ela fica
junto de `GE_NotSupported`, `ParenthesisMismatch` etc.). Não é a mensagem do motor padrão, que vem de
`CEngineStrings` (§7).

## 4. RTTI e classes C++ [O]

Fonte: `trabalho/rtti/CalcViewModel.hierarquia.json`. São 836 TypeDescriptors, 1366 COLs e 398 classes
com vftable. Por namespace de topo: Platform 114, std 100, **CalculatorApp 99**, Concurrency 37,
Windows 28, UnitConversionManager 5, CalculationManager 3, expressão sem namespace 5.

### 4.1 Motor (CalcManager)

| Classe | Bases (RTTI) | vftable (slots) | Observação |
|---|---|---|---|
| `CalculationManager::CalculatorManager` | `ICalcDisplay` | 0x18018ac40 (11) | ctor 0x18010cdf0; os 11 slots só repassam para `this+8` (§6.5) |
| `CalculationManager::CalculatorHistory` | `IHistoryDisplay` | 0x18018c390 (2) | slots 0x1801280e0, 0x180128130 |
| `CalculationManager::IResourceProvider` | — | 0x1801d76c0 (2: dtor, `_purecall`) | interface |
| `ICalcDisplay` | — | sem vftable própria (só TD) | 11 métodos, deduzidos pelos implementadores |
| `IHistoryDisplay` | — | 0x18018c3a8 (2) | |
| `CBinaryCommand` | `IBinaryCommand`, `IOperatorCommand`, `IExpressionCommand` | 0x1801da1a8 (4) | tokens de expressão |
| `CUnaryCommand` | `IUnaryCommand`, `IOperatorCommand`, `IExpressionCommand` | 0x1801da1d0 (5) | |
| `COpndCommand` | `IOpndCommand`, `IExpressionCommand` | 0x1801da220 (11) | operando |
| `CParentheses` | `IParenthesisCommand`, `IExpressionCommand` | 0x1801da200 (3) | |
| `UnitConversionManager::UnitConverter` | `IUnitConverter` | 0x18018bb28 (16) | ctor 0x1801185d0 |
| `UnitConversionManager::IUnitConverterVMCallback` / `IViewModelCurrencyCallback` / `IConverterDataLoader` / `ICurrencyConverterDataLoader` | — | 4 / 6 / 6 / (TD) | interfaces de callback e de carga |

- **Ausência importante [O]:** não há RTTI para a classe do motor propriamente dito (o objeto de 0x11a8
  bytes criado por `CalculatorManager`), nem para os tipos de número de precisão arbitrária. [I] Essas
  classes não têm funções virtuais, então o compilador não gerou RTTI para elas. Elas são identificadas
  só pelo código (§6.6–6.7).

### 4.2 Camada VM nativa (classes C++ que não são WinRT)

| Classe | Implementa | vftable | Papel |
|---|---|---|---|
| `CalculatorApp::ViewModel::Common::CalculatorDisplay` | `ICalcDisplay` | 0x1801d64e0 (11) | ponte motor → VM (§6.5) |
| `CalculatorApp::ViewModel::Common::EngineResourceProvider` | `CalculationManager::IResourceProvider` | 0x1801da190 (2) | ctor 0x180049130; `GetCEngineString` 0x180049260 |
| `CalculatorApp::ViewModel::Common::UnitConverterDataLoader` | `IConverterDataLoader` | 0x1801dd688 (6) | ctor 0x180081bf0 |
| `CalculatorApp::ViewModel::DataLoaders::CurrencyDataLoader` | `IConverterDataLoader`, `ICurrencyConverterDataLoader` | 0x1801dd188 (6) + 0x1801dd148 (7) | ctor 0x18006e830 |
| `CalculatorApp::ViewModel::UnitConverterVMCallback` | `IUnitConverterVMCallback` | 0x1801ec098 (4) | callback motor → `UnitConverterViewModel` |
| `CalculatorApp::ViewModel::ViewModelCurrencyCallback` | `IViewModelCurrencyCallback` | 0x1801ec0c0 (6) | idem, câmbio |

### 4.3 Classes WinRT (C++/CX)

Cada runtime class da `.winmd` tem uma classe RTTI homônima com bases `__I<Classe>PublicNonVirtuals`
(+ `ProtectedVirtuals`/`ProtectedNonVirtuals` vazias), `Platform::Object`, `IWeakReferenceSource` e,
quando aplicável, `INotifyPropertyChanged`. Cada uma tem também uma `__<Classe>ActivationFactory` com
`IActivationFactory` e as interfaces `Statics`/`Factory` [O]. Exemplo, `StandardCalculatorViewModel`:
7 vftables, com a principal em 0x1801e8ba8 (183 slots, `this+0`); a factory tem a vftable 0x1801d65c0
(18 slots).

## 5. Tipos WinRT (`CalculatorApp.ViewModel.winmd`) [O]

Fonte: `trabalho/winmd/CalculatorApp.ViewModel.txt` (gerado pelo `winmd_dump.py`; MVID
502ca6df-507d-4414-82ae-ccc9d87058c9).

- 161 tipos: 92 interfaces, 44 classes, 16 enums, 5 delegates, 4 structs. Há 32 classes com
  `ActivatableAttribute` e 5 só com `StaticAttribute` (`AppResourceProvider`, `NarratorAnnouncement`,
  `TraceLogger`, `LocalizationService`, `NavCategory`), totalizando **37**, o mesmo número de classes
  `inProcessServer` que o manifesto atribui a `CalcViewModel.dll` (Fase 1) [O].
- Classes principais (props/eventos/métodos não acessores):

| Classe | Ativação | Props | Métodos de destaque |
|---|---|---:|---|
| `StandardCalculatorViewModel` | `.ctor()` + Statics | 62 | `ButtonPressed` (ICommand), `SendCommandToCalcManager(Int32)`, `ResetCalcManager(Boolean)`, `OnMemory*`, `SelectHistoryItem`, `SwitchProgrammerModeBase(NumberBase)`, `SwitchAngleType`, `FtoEButtonToggled`, `OnCopyCommand`/`OnPasteCommand`, `SetCalculatorType(ViewMode)`, `UpdateOperand(Int32,String)` |
| `HistoryViewModel` | não ativável: obtido via `StandardCalculatorViewModel.HistoryVM` | 6 | `OnHistoryItemAdded(UInt32)`, `ShowItem`, `DeleteItem`, `ReloadHistory(ViewMode)`, `ClearCommand`, `HideCommand` |
| `HistoryItemViewModel` | — | 4 | `Expression`, `Result`, `AccExpression`, `AccResult` |
| `MemoryItemViewModel` | `.ctor(StandardCalculatorViewModel)` | 2 | `Value`, `Position`, `Clear`, `MemoryAdd`, `MemorySubtract` |
| `UnitConverterViewModel` | `.ctor()` | 43 | `ButtonPressed`, `SwitchActive`, `UnitChanged`, `CategoryChanged`, `OnPaste`, `RefreshCurrencyRatios`, `Close` (IClosable) |
| `DateCalculatorViewModel` | `.ctor()` | 16 | (usa `DateCalculationEngine`) |
| `Common.CopyPasteManager` | `.ctor()` + Statics | 7 (`Max*Length`) | `ValidatePasteExpression`, `ExtractOperands`, `ExpressionRegExMatch`, `SanitizeOperand`, `TryOperandToULL` |
| `Common.CalculatorButtonPressedEventArgs` | `.ctor(String feedback, NumbersAndOperatorsEnum)` | 2 | `GetOperationFromCommandParameter(Object)` |
| `Common.DelegateCommand` | `.ctor(DelegateCommandHandler)` | — | implementa `Windows.UI.Xaml.Input.ICommand` |
| `Snapshot.*` (11 classes) | `.ctor(...)` | — | estado serializável: `CalcManagerSnapshot`, `CalcManagerHistoryItem`, `CalcManagerToken`, `UnaryCommand`/`BinaryCommand`/`OperandCommand`/`Parentheses` (← `ICalcManagerIExprCommand`), `Primary/ExpressionDisplaySnapshot`, `StandardCalculatorSnapshot`, `ApplicationSnapshot` |

- Enums (valores completos em `trabalho/winmd/CalculatorApp.ViewModel.txt`):
  - `NumbersAndOperatorsEnum` (187 membros): `Zero..Nine`=130..139, `A..F`=140..145, `Add`=93,
    `Subtract`=94, `Multiply`=92, `Divide`=91, `Equals`=121, `Decimal`=84, `Negate`=80, `Clear`=81,
    `ClearEntry`=82, `Backspace`=83, `Percent`=118, `Sqrt`=110, `Invert`=114, `Sin/Cos/Tan`=102..104,
    `InvSin/InvCos/InvTan`=202..204, `EPowerX`=205, `Degree`=321, `Radians`=322, `Grads`=323,
    `Degrees`=324, `FToE`=119, `Mod`=95, `And/Or/Xor`=86/87/88, `Lsh/Rsh`=89/90, `Rol/Ror`=99/100,
    `Not`=101, `Qword/Dword/Word/Byte`=317..320, `HexButton/DecButton/OctButton/BinButton`=313..316,
    `IsStandardMode/IsScientificMode/IsProgrammerMode`=200/201/209, `MemoryClear/MemoryRecall/MemoryAdd/MemorySubtract`=122/123/125/126,
    `Memory`=146, `BINPOS0..63`=700..763, `Sec..InvCoth`=400..411, `TwoPowerX`=412, `Abs/Floor/Ceil`=413..415,
    `RolC/RorC`=416/417, `LogBaseY`=500, `Nand/Nor`=501/502, `RshL`=505, `Rand`=600, `Euler`=601, e os do modo gráfico ≥ 1000.
  - `ViewMode` (−1..17: Standard 0, Scientific 1, Programmer 2, Date 3, Volume 4 … Currency 16, Graphing 17);
    `NumberBase` (Hex 5, Dec 6, Oct 7, Bin 8); `BitLength` (8/16/32/64); `RadixType`; `CategoryGroupType`;
    `TokenType`; `NetworkAccessBehavior`; `CurrencyLoadStatus`; `DateUnit`; `MyVirtualKey`.
  - [I] Os valores de `NumbersAndOperatorsEnum` são os **mesmos códigos de comando do motor**: o VM
    repassa o inteiro sem tradução para `CalculatorManager::SendCommand`, salvo as exceções de §6.4.

### 5.1 Regra ABI → implementação (C++/CX) [O]

Para a vftable da interface (offset = `mdisp` da base no RTTI): os slots 0–5 são IUnknown+IInspectable,
o slot `6+k` é o thunk ABI do k-ésimo método (ordem das linhas MethodDef na `.winmd`) e o slot
`6+M+k` é a implementação C++ (M = número de métodos da interface). Evidências:

- Thunk de `SendCommandToCalcManager` (slot 79 = 6+73) em 0x18001f720: testa `this+0x320` (disposed) e
  executa `add rcx,0x178; call 0x18010d3d0`, repassando `edx` intacto (assembly, Evidence `ev_a220ffa8…`).
- Thunk de `get_DisplayValue` (slot 7) em 0x18001ddc0: chama `(*this)[0x2f8/8 = 95]` = slot 6+88+1, que
  é a implementação (Evidence `ev_3eaf7c55…`).
- Os thunks de `UpdateOperand` (slot 6) e `OnMemoryButtonPressed` (slot 80) chamam diretamente 0x1800da6e0
  e 0x1800d6bf0, que estão nos slots 94 e 168 = 6+88+k.

Com essa regra, `trabalho/winmd/vtable-map.md` lista **62 interfaces / 558 métodos** com thunk ABI e
implementação. Esse arquivo é o índice de entrada para a Fase 3.

## 6. Comunicação UI → view model → motor

### 6.1 Lado da UI (`CalculatorApp.dll`)

1. [O] **IIDs**: `CalculatorApp.dll` contém, em binário, 79 dos 97 IIDs de interfaces e delegates da
   `.winmd` (região 0x2b9c28–0x2c1328, p.ex. `__IStandardCalculatorViewModelPublicNonVirtuals`
   602897c8-… em 0x2b9c68). Os 18 ausentes são as interfaces `Protected*` (vazias) e tipos que só o próprio
   VM usa (`DateCalculationEngine`, `NetworkManager`, `NetworkBehaviorChangedHandler`,
   `__ILocalizationSettingsFactory`, `__INarratorAnnouncementStatics`,
   `__ICalculatorButtonPressedEventArgsStatics`). `GraphControl.dll` não contém nenhum desses IIDs
   (`trabalho/winmd/iid-scan.json`).
   - [I] O código .NET Native da UI faz QueryInterface e chamadas diretas nessas interfaces. As 79
     interfaces formam a superfície efetivamente consumida pela UI.
2. [O] **Metadados de binding XAML**: há strings UTF-16 `CalculatorApp.ViewModel.<Classe>.<Membro>`
   para 56 das 62 propriedades de `StandardCalculatorViewModel`; as 6 ausentes são as estáticas
   `*PropertyName`. Há também 37/43 de `UnitConverterViewModel`, 6/6 de `HistoryViewModel`, 4/4 de
   `HistoryItemViewModel`, 2/2 de `MemoryItemViewModel` e 7/7 de `DisplayExpressionToken`
   (`trabalho/winmd/ui-xaml-member-strings.json`). Ao lado delas ficam os nomes de tipos de UI
   (`CalculatorApp.MainPage` 0x2939d4, `CalculatorApp.Memory`, `CalculatorApp.MemoryListItem`…).
   - [I] É o XAML type info gerado pelo compilador XAML (IXamlType/IXamlMember), usado pelos bindings.
3. [O] `CalculatorApp.ManagedViewModels.ApplicationViewModel` (UTF-16 0x293a84) e o assembly de entrada
   `Calculator.ManagedViewModels.dll` (manifesto de build 0x337415). [I] O view model de topo é **C#**
   (compilado AOT dentro de `CalculatorApp.dll`). Ele cria `StandardCalculatorViewModel` /
   `UnitConverterViewModel` / `DateCalculatorViewModel` por ativação WinRT e alterna o modo com
   `SetCalculatorType(ViewMode)`. Os membros internos dele não foram recuperados (L3).
4. [I] Ativação: `new StandardCalculatorViewModel()` em .NET Native → `RoGetActivationFactory`
   (import tardio, §2) → manifesto (`inProcessServer` → `CalcViewModel.dll`) →
   `DllGetActivationFactory` → `__StandardCalculatorViewModelActivationFactory` → construtor
   0x1800d24c0 (único chamador de `CalculatorManager::ctor`, Evidence `ev_c90a0e56…`).

### 6.2 `StandardCalculatorViewModel`: construtor e layout [O]

Construtor 0x1800d24c0 (Evidence `ev_d5fa7104…`), com os offsets relativos ao objeto:

| Offset | Conteúdo | Evidência |
|---|---|---|
| +0x00..+0x30 | 7 vftables do objeto | gravação das vftables |
| +0x048 | `HistoryViewModel` criado por `FUN_1800b5270(alloc, this+0x178)` | depois chama `FUN_1800b5db0(historyVM, this+0x150)` |
| +0x068 / +0x069 | `IsInError` / `IsOperatorCommand` (bool) | 0x180013ad0, 0x1800d5aa0 |
| +0x0d8 | texto derivado do valor exibido, gravado por `SetPrimaryDisplay` e usado em `Format_MaxDigitsReached` ([I] provável `CalculationResultAutomationName`) | 0x1800d35b0, 0x1800dab90 |
| +0x0ec | `CurrentRadixType` = 6 (DecBase) | ctor |
| +0x100 | `OpenParenthesisCount` | 0x1800d3780 |
| +0x118 | cache do `ButtonPressed` (DelegateCommand) | 0x1800d1520 |
| +0x148 | modo de ângulo atual = 0x141 (Degree=321) | ctor; atualizado em `OnButtonPressed` |
| +0x150 | **`CalculatorDisplay`** (vftable 0x1801d64e0; +0x158 = weak ref ao VM; +0x160 = weak ref ao HistoryViewModel) | ctor |
| +0x168 | **`EngineResourceProvider`** (ctor 0x180049130) | ctor |
| +0x178 | **`CalculatorManager`** (ctor 0x18010cdf0(this+0x178, &display, &resourceProvider)) | ctor |
| +0x240..+0x270 | formatos localizados `Format_CalculatorExpression`, `Format_CalculatorResults`, `…_Decimal`, `Format_Hex/Dec/Oct/BinButtonValue` | `FUN_180009a40(loader, DAT_180206110..1d0)` + `hstring-globais.json` |
| +0x2c4 | `ValueBitLength` = 0x40 (QWord) | ctor |
| +0x2d8 | `AuditoryFeedback` do último botão | 0x1800d5aa0 |
| +0x320 | flag "disposed" | todos os thunks ABI |

### 6.3 Caminho de um botão (UI → motor)

```
XAML: CalculatorButton (C#) ButtonId=<nome de NumbersAndOperatorsEnum>   [O, XBF §7.3]
      Command=ButtonPressed via x:Bind; parâmetro = CalculatorButtonPressedEventArgs ou enum   [I]
  └─► ICommand.Execute → DelegateCommand (vftable 0x1801d6178)
       └─► handler 0x1800d5aa0  (registrado por get_ButtonPressed 0x1800d1520 [O])
            "OnButtonPressed(Object^ p)" [rótulo]
            ├─ feedback = FUN_18000fdb0(p)  → this+0x2d8
            ├─ op = FUN_18000fce0(p): QI p para o IID 40fdd0cd-… (CalculatorButtonPressedEventArgs,
            │        verificado em 0x1801782b8) → get_Operation; senão desempacota o enum [O]
            ├─ se IsInError: SendCommand(Clear=0x51) no motor; segue só para dígitos 0–9 (130–139),
            │        Decimal (84), A–F (140–145) ou BINPOS (700–763); os demais são descartados
            │        (tabelas 0x180189538 e 0x1801894c8, lidas do arquivo) [O]
            ├─ se IsEditingEnabled e op ∉ {FToE, Degree..Grads}: FUN_1800d8b90 (edição de token) e retorna
            ├─ op ∈ {200, 201, 209} (modos): set_IsEditingEnabled(false)
            ├─ op == 146 (Memory): OnMemoryButtonPressed 0x1800d6bf0 e retorna
            ├─ op ∈ {Clear, ClearEntry, 200, 209}: desliga IsFToEChecked se ligado
            ├─ 321..323: grava o modo de ângulo em this+0x148
            ├─ recalcula IsOperatorCommand (bitmask 0x1ff900000000003 sobre op−0x53) → PropertyChanged
            ├─ TraceLogger: FUN_180061650(op, modo)
            └─► CalculatorManager::SendCommand(this+0x178, op)  0x18010d3d0
```

### 6.4 `CalculatorManager::SendCommand` 0x18010d3d0 [O] (Evidence `ev_1d8b84a3…`)

- `200` → `SetStandardMode` 0x18010d0e0; `201` → `SetScientificMode` 0x18010d1f0; `209` →
  `SetProgrammerMode` 0x18010d300. Cada um termina com `display->slot10` (InputChanged).
- `321..323` (Degree/Radians/Grads) → grava `this+0x9c` e repassa ao motor.
- `119` (FToE) → alterna `this+0x98` e repassa.
- **Funções inversas viram INV + função**: o motor recebe `146` (0x92) e depois a função direta.
  Exemplos: `InvSin 202 → 146, 102`, `InvCos 203 → 146, 103`, `InvTan 204 → 146, 104`,
  `EPowerX 205 → 146, 108 (LogBaseE)`, `InvSinh..InvTanh 206..208 → 146, 105..107`, e `InvSec/InvCsc/InvCot/InvSech/InvCsch/InvCoth`
  (401, 403, 405, 407, 409, 411) → `146, n−1`.
  - [I] No motor, o código 146 é o modificador "INV". No enum da UI, o mesmo valor se chama `Memory`,
    mas o VM intercepta `Memory` antes (§6.3), então não há conflito.
- Demais comandos → `engine->ProcessCommand(op)` = **0x180112db0**, seguido de `display->slot10`.
- `ResetCalcManager(bool)` → 0x18010d060: chama `SetStandardMode`, envia 321 (Degree) e Clear à engine
  científica (+0x18) e desliga FToE nela se estiver ligado, envia Clear à engine de programador (+0x28)
  e, se `clearMemory`, chama 0x18010d940.

### 6.5 Retorno motor → UI: `ICalcDisplay` (11 slots)

Em `CalculatorManager` (vftable 0x18018ac40), cada slot só repassa para `this+8` (o `ICalcDisplay` recebido
no construtor = `CalculatorDisplay` do VM). Os slots 0 e 2 são suprimidos quando `this+0x38 != 0` [O]
(Evidence `ev_1eb67b56…`). Em `CalculatorDisplay` (vftable 0x1801d64e0), cada slot resolve a weak ref
(+8 → VM, IID em 0x180179ca8; +0x10 → HistoryViewModel, IID em 0x180179d48) e chama um método do VM [O]
(Evidence `ev_2cce8cca…`):

| Slot | Assinatura observada | Método do VM chamado | Efeito observado | Rótulo [I] |
|---:|---|---|---|---|
| 0 | `(const wstring&, bool)` | 0x1800d35b0 | formata o texto (0x1800d2ee0), atualiza `DisplayValue` (vslot 0x300) e chama `IsInError` | SetPrimaryDisplay(text, isError) |
| 1 | `(bool)` | 0x180013ad0 | `PropertyChanged("IsInError")` | SetIsInError |
| 2 | `(p, p)` | 0x1800d3d30 | tokens + comandos da expressão | SetExpressionDisplay(tokens, commands) |
| 3 | `(int)` | 0x1800d3780 | `PropertyChanged("OpenParenthesisCount")` | SetParenthesisNumber |
| 4 | `()` | 0x1800d3ba0 | anúncio `NoRightParenthesisAdded_Announcement` | OnNoRightParenAdded |
| 5 | `()` | 0x1800dab90 | anúncio `Format_MaxDigitsReached` + texto exibido | MaxDigitsReached |
| 6 | `()` | 0x1800dadc0 | anúncio `Format_ButtonPressAuditoryFeedback` (usa o feedback salvo em +0x2d8) | BinaryOperatorReceived (provável) |
| 7 | `(int)` | **HistoryViewModel** `OnHistoryItemAdded` 0x1800b5780 | assert `uIdx < m_historyItems.size()` | OnHistoryItemAdded(index) |
| 8 | `(p)` | 0x1800d4b70 | reconstrói `MemorizedNumbers` (vslot 0x3d8) | SetMemorizedNumbers |
| 9 | `(int)` | 0x1800d6e90 | atualiza um `MemoryItemViewModel` | MemoryItemChanged(index) |
| 10 | `()` | 0x1800d6b20 | `PropertyChanged("IsInputEmpty")` | InputChanged |

As chaves de anúncio vêm de HSTRINGs globais inicializados estaticamente (p.ex. `DAT_180206250` ←
`L"Format_ButtonPressAuditoryFeedback"` em 0x1800050e8; `trabalho/hstring-globais.json`) [O].
`PropertyChanged` chega à UI pelos bindings (§6.1.2) [I].

### 6.6 `CalculatorManager` (motor, lado de cima) [O]

Layout (`this` = VM+0x178), visto no construtor da Fase 1 e nas funções 0x18010d0e0/1f0/300/3d0/060:

| Offset | Conteúdo |
|---|---|
| +0x00 | vftable `ICalcDisplay` (0x18018ac40) |
| +0x08 | `ICalcDisplay*` de saída (= `CalculatorDisplay` do VM) |
| +0x10 | **engine atual** |
| +0x18 / +0x20 / +0x28 | engine **científica** / **padrão** / **programador** (criadas sob demanda, 0x11a8 bytes) |
| +0x30 | `IResourceProvider*` |
| +0x38 | flag que suprime os slots 0/2 (provável carga de item do histórico [I]) |
| +0x40/+0x48 | vetor de números memorizados (begin/end), usado por `OnMemoryAdd` |
| +0x98 / +0x9c | flag FToE / modo de ângulo |
| +0xa0/+0xa8, +0xb0/+0xb8 | `shared_ptr` do histórico **padrão** / **científico** (`CalculatorHistory`, 2 instâncias de 20 itens, Fase 1) |
| +0xc0 | histórico atual |

Troca de modo (Evidence `ev_1eb67b56…`):

| Modo | Construtor da engine `0x180111bd0(eng, a, b, resProv, display, history)` | Após trocar |
|---|---|---|
| Padrão (200) | `a=0, b=0`, histórico padrão | `ProcessCommand(314 DecButton)`, `Clear`; precisão `eng+0xe28 = 16`; `ratpak_init(radix, 16)`; extra 0x18012d820 |
| Científico (201) | `a=1, b=0`, histórico científico | idem com precisão **32** |
| Programador (209) | `a=1, b=1`, sem histórico | idem com precisão **64**; não muda `+0xc0` |

[I] `a` liga a precedência de operadores (o modo padrão avalia em sequência) e `b` liga o modo inteiro
(programador). Isso vem do padrão de uso e precisa ser confirmado na Fase 3a/3d.

API de memória e histórico usada pelo VM (Evidence `ev_b2a5b5e1…`): 0x18010d760 (memorizar),
0x18010d9b0 (carregar item n), 0x18010dab0/0x18010dbe0 (após `MemoryAdd`), 0x18010d810 (limpar item n),
0x18010d940 (limpar memória). A seguir vêm `ProcessCommand(123 MemoryRecall / 125 MemoryAdd)` e
`display->slot9`.

### 6.7 Engine (sem RTTI) [O]

- Construtor 0x180111bd0 (Evidence `ev_b35fbe49…`): `+0x0` e `+0x1` recebem os booleanos `a`/`b`;
  `+0x8` = `ICalcDisplay*`; `+0x10` = `IResourceProvider*`; `+0x38` = `'.'` (0x2e);
  `+0x11a2` = `','` (0x2c); `+0xe20` = flag testada pelo VM antes de `MemoryRecall`/`MemoryAdd` ([I] estado de erro);
  `+0xe24` = **base 10**; `+0xe28`/`+0xe2c` = precisão 32; `+0xf50` = tamanho de palavra (0..3) →
  `+0xf54` = 64/32/16/8 bits; `+0xf70` = coletor de histórico/expressão (0x18010e8f0); objetos numéricos
  em `+0x98, +0xe0, +0x120, +0x160`; duas áreas de 0x640 bytes em `+0x1a0` e `+0x7e0` [I: pilhas de
  operandos/operadores].
- Ponto de entrada: `ProcessCommand` 0x180112db0. Ele tem 57 callees resolvidos e 50 chamadas indiretas
  não resolvidas (Evidence `ev_d431ac44…`). O detalhamento fica para a Fase 3.
- Aritmética: `ratpak_init` 0x180121ec0(base, precisão) (Fase 1) é chamado a cada troca de modo com a
  precisão do modo [O]. O código de precisão arbitrária fica na faixa 0x180121xxx–0x18013xxxx [I].

### 6.8 Recursos do motor [O]

`EngineResourceProvider` (ctor 0x180049130) guarda em `+8` um `ResourceLoader` criado com
`L"CEngineStrings"`. `GetCEngineString(id)` (0x180049260) trata três chaves especiais com dados de
`LocalizationSettings`: `sDecimal`, `sThousand` e `sGrouping` (literais em 0x18017bc10/28/40,
referenciados por `lea` em 0x1800492ae/2ee/32e; a terceira o decompilador omitiu). Os demais ids viram
`ResourceLoader.GetString(id)` (Evidence `ev_22196beb…`) [O].

O construtor de `CalculatorManager` carrega 152 ids da tabela 0x18018af40 (offset de arquivo 0x189f40;
pares ponteiro+tamanho) por esse método (Fase 1). A tabela foi extraída para `trabalho/cengine-ids.json`
[O]. Os índices 0–118 usam chaves numéricas, com irregularidades: o índice 1 usa a chave `62`, as chaves
`36`, `98` e `110` não aparecem, e o índice 97 usa a chave `10` (repetida). Os índices 119–151 usam
chaves nominais (`SecDeg`…`InverseCoth`, `TwoPowX`, `LogBaseY`, `Abs`, `Floor`, `Ceil`, `Nand`, `Nor`,
`CubeRoot`, `ProgrammerMod`). [I] As chaves numéricas são os ids de uma tabela de strings legada do
motor. Os valores EN-US estão em §7.

**Atualização (Fase 3a) [O]:** a tabela é só a lista de chaves a **carregar**. `FUN_180111b10` percorre os
152 `wstring_view` (0x18018af40…0x18018b8c0), chama `GetCEngineString` e grava num `unordered_map<wstring,
wstring>` global (0x180206678) só as chaves com texto não vazio. O motor consulta esse mapa **pelo nome da
chave**: `to_wstring(n)` em 0x180094ca0 + `operator[]` em 0x1800e5a40. Então as irregularidades de posição
não têm efeito, e uma chave ausente produz `""`. Ver `02-features/a-operacoes-basicas.md` §7.

### 6.9 Histórico e memória (visão de ligação)

- `HistoryViewModel` é criado pelo VM padrão com `&CalculatorManager` (0x1800b5270) e recebe o
  `CalculatorDisplay` (0x1800b5db0) [O]. A UI o obtém por `HistoryVM` [O]. `OnHistoryItemAdded` é chamado
  pelo slot 7 de `ICalcDisplay` [O]. `SelectHistoryItem` (0x1800db3d0) reaplica tokens/expressão e o
  resultado pelos mesmos métodos dos slots 2 e 0 [O].
- Memória: comandos `MemoryAdd/MemorySubtract/MemoryItemPressed/ClearMemoryCommand` (ICommand do VM) →
  `OnMemory*` (0x1800d6bf0, 0x1800d7350, 0x1800d76b0, 0x1800d78f0, 0x1800d7ac0) → API de §6.6 → slots 8/9
  → `MemorizedNumbers` (`IVector<MemoryItemViewModel>`) [O].

### 6.10 Conversor de unidades (cadeia) [O]

`__UnitConverterViewModelActivationFactory` 0x18010cc80 → 0x1800f7840 (aloca 0x2a8) →
**`UnitConverterViewModel::ctor` 0x1800efe10**, que cria:
`UnitConverterDataLoader` (make_shared 0x1800fdf50 → ctor 0x180081bf0), `CurrencyDataLoader` (ctor
0x18006e830) e `UnitConverter` (make_shared 0x1800fe060 → 0x1801056e0 → ctor 0x1801185d0, vftable
0x18018bb28) (Evidence `ev_2232832a…`, `ev_6b8bfb15…`, `ev_ed8eb5da…`). Os callbacks voltam por
`UnitConverterVMCallback` / `ViewModelCurrencyCallback`. As taxas de câmbio vêm de cache/arquivo e da
web (strings de §3).

### 6.11 Outros componentes do VM

| Componente | Papel | Evidência |
|---|---|---|
| `CopyPasteManager` | valida e normaliza o que é colado (regex por modo/base, limites `Max*`) | winmd + strings 0x179018–0x179480 |
| `DateCalculationEngine` / `DateCalculatorViewModel` | cálculo de datas com `Windows.Globalization.Calendar` | winmd + strings 0x17ab58, 0x183250… |
| `Snapshot.*` | serialização do estado do motor (tokens, comandos, histórico) | winmd + RTTI (`ICalcManagerIExprCommand`) |
| `TraceLogger` | telemetria via `TraceLogging.dll` | strings 0x17d530…, 0x17e880 |
| `LocalizationSettings` / `LocalizationService` | separadores, dígitos nativos, fontes | strings `sDecimal`/`sThousand`/`sGrouping`, uso em 0x180049260 e 0x1800d7ac0 (troca de dígitos 0–9 por dígitos locais) |
| `NetworkManager` | estado da rede para o câmbio | winmd (IID ausente da UI) |

## 7. Recursos: `resources.pri` e XBF

Fonte: `trabalho/pri/` (parser `trabalho/scripts/pri_dump.py` + `xbf_dump.py`; layout, offsets e
validações em `trabalho/pri/LEIAME.md`). A referência de formato foi só a de parsers genéricos
(PriTools/XbfTools, Apache-2.0), sem nada específico da Calculadora. Esse trabalho foi feito por um
agente auxiliar; as afirmações abaixo foram conferidas por amostragem nos arquivos gerados e nos bytes.

**Referências de formato usadas (registro explícito):**
- **PriTools** (`chausner/PriTools`, Apache-2.0, commit `765d4544`): documento `Package Resource Index File
  Format.md` e `PriFormat/Sections/*.cs`. Base do layout PRI de `trabalho/scripts/pri_dump.py` e
  `pri_valida.py`: cabeçalho/TOC, `[mrm_pridescex]`, `[mrm_decn_info]`, `[mrm_hschemaex]` (com o algoritmo do
  checksum CRC32), `[mrm_res_map2_]` (incluindo a referência de esquema usada pelo PRI pt-BR) e
  `[mrm_dataitem]`. As constantes de rodapé do `.md` divergem do arquivo e do próprio código C#; prevaleceram
  os bytes (`trabalho/pri/LEIAME.md` §2).
- **XbfTools** (`chausner/XbfTools`, Apache-2.0, commit `dbeadcd7`): `XbfFormat/XbfHeader.cs`,
  `XbfReader.cs`, `XbfType.cs`, `XbfProperty.cs` e a tabela `XbfFrameworkTypes.cs` (IDs de tipo/propriedade
  do framework, que segundo o próprio arquivo vêm do `GenXbf.dll` do Windows SDK 10.0.26100.0), convertida em
  `trabalho/scripts/dados/xbf_framework_ids.json`. Base de `trabalho/scripts/xbf_dump.py`, com duas hipóteses
  próprias (`trabalho/pri/LEIAME.md` §5.1).
- Os dois são parsers genéricos de formato. Nenhum código-fonte ou análise da Calculadora foi consultado.

### 7.1 `resources.pri` [O]

- 137 seções (`[mrm_decn_info]`, `[mrm_pridescex]`, `[mrm_hschemaex]`, `[mrm_res_map2_]` e 133
  `[mrm_dataitem]`) com rodapés `0xDEF5FADE` válidos, 661 escopos e **1323 itens**: 108
  `CEngineStrings`, 1166 `Resources` e 49 `Files`. O esquema e o resource map concordam; todos os
  2546 candidatos e 1380 data items são referenciados; o CRC32 recalculado do esquema
  (0x55A27B9B) é igual ao gravado. Idiomas: EN-US (1274 candidatos) e EN-GB (1032).
- **pt-BR (atualização de 2026-10-22):** `./binarios-ptbr/resources.pri` (pacote `split.language-pt`
  11.2607.0.0, íntegro e assinado; `trabalho/ptbr/LEIAME.md`). O esquema é o mesmo do pacote principal
  (checksum 0x55A27B9B, referenciado e não copiado). Tem PT-BR e PT-PT para as 1032 chaves que têm EN-GB no
  principal. Tabelas em `trabalho/ptbr/CEngineStrings.tsv` e `Resources.tsv`.
- Tabelas: `trabalho/pri/CEngineStrings.tsv`, `trabalho/pri/Resources.tsv` (`chave, idioma, valor`).

### 7.2 `CEngineStrings`: tokens de expressão e mensagens do motor [O]

Os valores são, em sua maioria, os símbolos que o motor escreve na expressão (`11` `÷`, `12` `×`,
`13` `+`, `14` `-`, `15` `Mod`, `16` `yroot`, `17` `^`, `22` `sin`, `24` `tan`, `28` `ln`, `29` `log`,
`30`/`90` `√`, `35` `dms`, `37`/`89` `10^`, `48`/`49` `(`/`)`, `67`…`84` `sin₀`, `cosᵣ⁻¹`, `tan₉`…,
`91` `sqr`, `92` `cube`, `94` `fact`, `95` `1/`, `96` `degrees`, `97` `negate`). Entre eles estão as
**mensagens de erro**:

| Chave | EN-US | Índice na tabela do motor (`trabalho/cengine-ids.json`) |
|---|---|---:|
| `99` | Cannot divide by zero (data item 4/695 @0x1E1C4, compartilhado com `Resources/DivideByZero`) | 98 |
| `100` | Invalid input | 99 |
| `101` | Result is undefined | 100 |
| `105` | Not enough memory | 104 |
| `107`, `119`, `120` | Overflow | 106, 117, 118 |
| `108`, `118` | Result not defined | 107, 116 |

Observações [O]:
- **Revalidado antes da 3a** (`trabalho/pri/LEIAME.md` §8): os dois pontos abaixo não são erro do parser.
  O efeito no motor está em `02-features/a-operacoes-basicas.md` §7: chave ausente → `""`; `23` é o
  fallback do Cos, que usa as chaves `68`/`74`/`80`.
- **43 das 152 entradas da tabela do motor (42 chaves distintas; `62` aparece duas vezes) não têm item
  no PRI**. Como o esquema é único para todos os idiomas, elas não existem em nenhum idioma. Chaves ausentes: `0`, `62`,
  `3`, `5`, `31`–`34`, `39`, `42`–`46`, `50`–`65`, `93`, `102`–`104`, `106`, `109`, `111`–`117` (basta
  cruzar `cengine-ids.json` com `CEngineStrings.tsv` para reproduzir). Todas as 108
  chaves do PRI aparecem na tabela do motor. [I] Para as ausentes, `ResourceLoader.GetString` devolve
  vazio. O efeito disso no motor fica para a Fase 3.
- `CEngineStrings/23` = `cis` (bytes `63 69 73` em 0x1F8DC), entre `22` `sin` e `24` `tan`. [I] Parece
  erro de digitação de `cos` no próprio recurso EN-US. É um bom candidato a caso de teste da Fase 4:
  "cos" na expressão do modo científico.
- `Resources` traz também `Overflow` = "Overflow (the number is too large)", `CalculationFailed`,
  `Format_MaxDigitsReached` = "Max digits reached. %1" e os textos de acessibilidade e de feedback
  auditivo por botão (p.ex. `divideButton/…CalculatorButton/AuditoryFeedback` = "divided by").

### 7.3 XBF (XAML compilado): ligação dos botões ao VM [O, salvo indicação; ver ressalva L12]

- 32 XBF v2.1, extraídos com sha256 conferido e tabelas de strings lidas (`trabalho/pri/xbf-strings/`).
  A desmontagem do fluxo de nós (`xbf-nos/`) é heurística e serve de pista, não de prova (LEIAME §5.1).
- **Botão → operação** (os nomes `ButtonId` e os valores do enum estão na tabela de strings de cada XBF
  [O]; o pareamento objeto → propriedade → valor vem da desmontagem heurística do fluxo de nós, L12): cada botão é um `CalculatorApp.Controls.CalculatorButton` (controle C#) cuja
  propriedade `ButtonId` recebe o **nome de um membro de `NumbersAndOperatorsEnum`**. Exemplos:
  `DivideButton` → `Divide` (91), `ClearButton` → `Clear` (81), `EqualButton` → `Equals` (121),
  `Num0Button` → `Zero` (130); `FlipButtons` → `BINPOS0..63` (700–763). São 266 objetos ao todo em
  `trabalho/pri/xbf-botoes.tsv`, com o valor numérico do enum vindo do winmd e o rótulo EN-US.
- `CommandParameter` literal só em casos especiais: `FtoeButton` = `FToE` (119); `Degree/Radian/Grads`
  = 0/1/2; `Qword/Dword/Word/Byte` = 0/1/2/3; botões de memória = `{StaticResource Zero}`.
- `Command="…ButtonPressed"` **não** aparece em nenhum XBF. [I] O comando é ligado por `x:Bind`, que o
  compilador XAML converte em código C# dentro de `CalculatorApp.dll`.
- [I] Fechando a cadeia: o `CalculatorButton` (C#) monta um `CalculatorButtonPressedEventArgs(feedback,
  ButtonId)`. O recurso `…CalculatorButton/AuditoryFeedback` fornece o feedback, e o construtor está na
  winmd com essa assinatura. O botão envia esse objeto como parâmetro do comando, e `OnButtonPressed`
  faz QueryInterface justamente para o IID desse tipo (§6.3).
- `{Binding}` que coincidem com propriedades do VM: `DisplayValue`, `ExpressionTokens`, `IsProgrammer`
  (`Calculator.xbf`), `IsMemoryEmpty` (`Memory.xbf`), `IsDecimalEnabled` (`NumberPad.xbf`), `Unit1/Unit2/
  Units/Value1Active/Value2Active/IsDropDownEnabled` (`UnitConverter.xbf`) e 12 de `DateCalculatorViewModel`.

## 8. Índice de endereços para a Fase 3

| Feature | Pontos de entrada |
|---|---|
| a) básico / divisão por zero | `OnButtonPressed` 0x1800d5aa0 → `SendCommand` 0x18010d3d0 → `ProcessCommand` 0x180112db0; `SetPrimaryDisplay` (VM) 0x1800d35b0; flag de erro `engine+0xe20`; `CEngineStrings` |
| b) histórico e memória | `HistoryViewModel` 0x1800b5270 / `OnHistoryItemAdded` 0x1800b5780 / `ReloadHistory` 0x1800b53d0; `CalculatorHistory` (vftable 0x18018c390: 0x1801280e0, 0x180128130); memória 0x18010d760/9b0/810/940/ab0/be0; VM 0x1800d6bf0…0x1800d7ac0 |
| c) científico | `SetScientificMode` 0x18010d1f0; mapeamento INV em 0x18010d3d0; ângulo `CalculatorManager+0x9c`, VM+0x148 |
| d) programador | `SetProgrammerMode` 0x18010d300; `engine+0xf50/+0xf54`; `SwitchProgrammerModeBase` 0x1800d8a40; `set_ValueBitLength` 0x1800db070 |
| e) conversão de unidades | `UnitConverterViewModel::ctor` 0x1800efe10; `UnitConverter` ctor 0x1801185d0 / vftable 0x18018bb28; loaders 0x180081bf0, 0x18006e830 |
| f) motor numérico | engine ctor 0x180111bd0; `ratpak_init` 0x180121ec0; precisões 16/32/64 em 0x18010d0e0/1f0/300 |

Mapa completo método WinRT → endereço: `trabalho/winmd/vtable-map.md`.

## 9. Checklist da fase

| Item | Status |
|---|---|
| Imports/exports | respondido (§2) |
| Strings | respondido (§3; inventário completo em `trabalho/strings`) |
| RTTI, classes C++, vftables | respondido para `CalcViewModel.dll` (§4); o motor sem RTTI foi identificado pelo código (§6.6–6.7) |
| Tipos WinRT dos `.winmd` | respondido para `CalculatorApp.ViewModel.winmd` (§5); `GraphControl.winmd` fora de escopo (L8) |
| Mapa de módulos e comunicação UI → VM → motor | respondido (§6), com rótulos [I] para métodos de interfaces C++ sem símbolo (L7) e motor sem RTTI (L9) |
| Recursos (PRI/XBF) | respondido para EN-US/EN-GB (§7); pt-BR adicionado em 2026-10-22 (§7.1, L2 resolvida) |
