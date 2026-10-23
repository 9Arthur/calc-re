# Fase 0 — Verificação do ambiente

Data: 2026-10-22
Evidências REA exportadas: `trabalho/fase0-evidencias.json` (5 registros, 0 unknowns)

## 1. Ferramentas REA na sessão

| Item | Valor | Status |
|---|---|---|
| Servidor MCP | `rea` / pacote `rea-agents` 6.7.0 | OBSERVADO (`binary_session.server_identity`) |
| Catálogo | 207 ferramentas MCP, 6 prompts, 153 comandos CLI | OBSERVADO |
| Cliente | claude-code 2.1.308, protocolo 2026-07-28 | OBSERVADO |
| Ferramentas `mcp__rea__*` visíveis nesta sessão | sim (carregadas via ToolSearch e chamadas com sucesso) | OBSERVADO |

## 2. Provedor Ghidra

| Item | Valor | Status |
|---|---|---|
| Versão | Ghidra 12.1.4 | OBSERVADO (`analysis_provider_candidates`) |
| Instalação | `~/ferramentas/ghidra_12.1.4_PUBLIC` (pasta local do usuário) | OBSERVADO |
| Headless | `support/analyzeHeadless` presente | OBSERVADO |
| Decompilador nativo | `Ghidra/Features/Decompiler/os/linux_x86_64/decompile` presente | OBSERVADO |
| Java | OpenJDK 25.0.4.1 (`/usr/lib/jvm/java-25-openjdk-amd64`) | OBSERVADO |
| Checagens (configuration, platform, architecture, installation, version, headless, native_decompiler) | todas `ok: true` | OBSERVADO |

Outros provedores relevantes para fases futuras:
- `rea-dotnet-static` (`inspect_managed_artifact`, `inspect_managed_members`,
  `inspect_managed_native_boundaries`): disponível. Candidato para ler os `.winmd`. OBSERVADO
- `rea-artifact-graph` (`inspect_artifact`, `extract_artifact`): disponível. OBSERVADO
- Indisponíveis e irrelevantes para o projeto: Android/ADB, JEB, macOS, firmware,
  WASM, pcap, sigrok, SQLite, layout ELF. OBSERVADO

## 3. Teste com `binarios/CalculatorApp.exe`

Integridade: `sha256sum -c hashes-originais.txt` → 15/15 OK, antes e depois do teste.
O SHA-256 que o REA calculou na abertura (`f26a20f8…b242`) é igual ao do arquivo de hashes. OBSERVADO

| Operação REA | Resultado | Evidence ID |
|---|---|---|
| `open_binary` (provider ghidra) | PE x86_64 executável | — |
| `binary_overview` | image base 0x180000000; 5 blocos (Headers, .rdata, .data, .rsrc, .text); 2 procedimentos; 29 strings | `ev_bb2e0f85…38eb` |
| `list_procedures` | `EXTERNAL:0x1 CALCULATORAPP.DLL::RHBinder__ShimExeMain` (externa); `0x180008000 entry` (thunk → EXTERNAL:0x1) | `ev_39592e12…fa8c1` |
| `procedure_pseudo_code` 0x180008000 | decompilou: `void entry(void) { RHBinder__ShimExeMain(); return; }` | `ev_c46c6b48…d5346` |
| `list_strings` | 29 strings, entre elas `CalculatorApp.dll`, `RHBinder__ShimExeMain`, VERSIONINFO (`FileVersion 11.2607.0.0`, `ProductName Microsoft Calculator`) e o manifesto (`asInvoker`) | `ev_68bcaa1b…c8909` |
| `close_binary` | sessão fechada; o banco do Ghidra era efêmero e não houve escrita no binário | — |

Conclusão: o REA executa o Ghidra headless, a autoanálise termina e o decompilador
gera pseudocódigo. OBSERVADO

## 4. Notas para a Fase 1 (não são conclusões da Fase 0)

- O `.text` do EXE tem 512 bytes, e o único código é um salto para o export
  `RHBinder__ShimExeMain` de `CalculatorApp.dll`. OBSERVADO
- O EXE é só um lançador; o código da aplicação fica em `CalculatorApp.dll`. INFERIDO
- O prefixo `RHBinder`/"RH" coincide com a convenção do toolchain .NET Native
  (runtime "Redhawk") usado em apps UWP. Se isso se confirmar,
  `CalculatorApp.dll` contém código gerenciado compilado AOT, e a busca por
  RTTI/classes C++ da Fase 2 precisa de outra abordagem nesse módulo. INFERIDO,
  a verificar na Fase 1 com imports/exports e seções.

## 5. Pendências de configuração

Nenhuma. Não é preciso reiniciar o Claude Code nem instalar nada.
