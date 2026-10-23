# rodar-casos.ps1 - Fase 4, teste caixa-preta da Calculadora instalada via UI Automation.
# Uso (do WSL):
#   powershell.exe -ExecutionPolicy Bypass -File "$(wslpath -w trabalho/automacao/rodar-casos.ps1)" -Etapa Arvore
#   powershell.exe -ExecutionPolicy Bypass -File "$(wslpath -w trabalho/automacao/rodar-casos.ps1)" -Etapa Casos
# Etapa Arvore: grava a arvore UIA (modos Padrao e Cientifico) em arvore-uia.txt, ao lado deste script.
# Etapa Casos: executa os casos da 3a e grava relatorio/resultados-reais.txt.
# Etapa Arvore3b: arvore UIA dos submenus de historico e memoria (arvore-uia-3b.txt).
# Etapa Casos3b: casos de relatorio/03b-casos-de-teste.md -> relatorio/resultados-reais-3b.txt; antes de cada caso
#   limpa historico (Cientifico e Padrao) e memoria e confere o estado. CASOS3B=id1,id2 (com WSLENV=CASOS3B) filtra os casos.
# Etapa Arvore3c: botoes e submenus do modo Cientifico (arvore-uia-3c.txt).
# Etapa Casos3c: casos de relatorio/03c-casos-de-teste.md -> relatorio/resultados-reais-3c.txt. CASOS3C=id1,id2 filtra.
# Etapa Arvore3d: arvore UIA do modo Programador, submenus e teclado de bits (arvore-uia-3d.txt).
# Etapa Casos3d: casos de relatorio/03d-casos-de-teste.md -> relatorio/resultados-reais-3d.txt. CASOS3D=id1,id2 filtra.
# Etapa Diferencial: casos de relatorio/03-diferencial-casos.json -> relatorio/resultados-reais-diferencial.jsonl
#   (uma linha JSON por caso, acrescentada ao fim; so visor final e estado de erro pelo UIA). DIF=id1,id2 filtra.
# Nao instala nada: usa so UIAutomationClient/UIAutomationTypes e System.Windows.Forms (SendKeys).
param(
    [ValidateSet('Arvore', 'Casos', 'Arvore3b', 'Casos3b', 'Arvore3c', 'Casos3c', 'Sonda3c', 'Arvore3d', 'Casos3d', 'Diferencial')][string]$Etapa = 'Arvore',
    [int]$PausaMs = 250
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms, System.Drawing, System.Runtime.WindowsRuntime
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class W32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
# Coordenadas UIA e CopyFromScreen em pixels fisicos
[void][W32]::SetProcessDPIAware()

$AE = [System.Windows.Automation.AutomationElement]
$Escopo = [System.Windows.Automation.TreeScope]
$Raiz = $AE::RootElement
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$DirScript = Split-Path -Parent $MyInvocation.MyCommand.Path
$DirProjeto = Split-Path -Parent (Split-Path -Parent $DirScript)

function Obter-Janela {
    for ($i = 0; $i -lt 60; $i++) {
        foreach ($j in $Raiz.FindAll($Escopo::Children, [System.Windows.Automation.Condition]::TrueCondition)) {
            if ($j.Current.Name -match '^(Calculadora|Calculator)$') { return $j }
        }
        if ($i -eq 0) { Start-Process 'explorer.exe' 'shell:AppsFolder\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App' }
        Start-Sleep -Milliseconds 500
    }
    throw 'Janela da Calculadora nao encontrada'
}

function Focar($janela) {
    $h = [IntPtr]$janela.Current.NativeWindowHandle
    [void][W32]::ShowWindow($h, 9)
    [void][W32]::SetForegroundWindow($h)
    try { $janela.SetFocus() } catch {}
    Start-Sleep -Milliseconds 300
}

function Trocar-Modo($janela, [string]$tecla) {
    Focar $janela
    [System.Windows.Forms.SendKeys]::SendWait("%$tecla")
    Start-Sleep -Milliseconds 1500
}

function Despejar-Arvore($elem, [int]$nivel, [System.Text.StringBuilder]$sb) {
    $c = $elem.Current
    $tipo = $c.ControlType.ProgrammaticName -replace '^ControlType\.', ''
    [void]$sb.AppendLine(('{0}[{1}] Name="{2}" AutomationId="{3}" Class="{4}" Enabled={5} Offscreen={6}' -f
            ('  ' * $nivel), $tipo, $c.Name, $c.AutomationId, $c.ClassName, $c.IsEnabled, $c.IsOffscreen))
    if ($nivel -gt 40) { return }
    $w = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $f = $w.GetFirstChild($elem)
    while ($f -ne $null) {
        Despejar-Arvore $f ($nivel + 1) $sb
        $f = $w.GetNextSibling($f)
    }
}

if ($Etapa -eq 'Arvore') {
    $janela = Obter-Janela
    $sb = New-Object System.Text.StringBuilder
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    [void]$sb.AppendLine("# Arvore UI Automation da Calculadora $($pkg.Version) $($pkg.Architecture)")
    [void]$sb.AppendLine("# Coletada em $(Get-Date -Format s); cultura $((Get-Culture).Name), UI $((Get-UICulture).Name)")
    foreach ($m in @(@('1', 'Padrao'), @('2', 'Cientifico'))) {
        Trocar-Modo $janela $m[0]
        $janela = Obter-Janela
        [void]$sb.AppendLine('')
        [void]$sb.AppendLine("##### Modo $($m[1]) (Alt+$($m[0])) #####")
        Despejar-Arvore $janela 0 $sb
    }
    Trocar-Modo $janela '1'
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'arvore-uia.txt'), $sb.ToString(), $Utf8)
    Write-Output "arvore gravada: $(Join-Path $DirScript 'arvore-uia.txt')"
    exit 0
}

# ---------------------------------------------------------------- Etapa Casos
# Identificadores tirados de arvore-uia.txt (AutomationId), nao do codigo-fonte.
$Teclas = @{
    'C' = 'clearButton'; 'CE' = 'clearEntryButton'; 'BS' = 'backSpaceButton'; 'NEG' = 'negateButton'
    'DEC' = 'decimalSeparatorButton'; '/' = 'divideButton'; '*' = 'multiplyButton'; '-' = 'minusButton'
    '+' = 'plusButton'; '=' = 'equalButton'; '%' = 'percentButton'; 'SQRT' = 'squareRootButton'
    'SQR' = 'xpower2Button'; 'INV' = 'invertButton'
}
0..9 | ForEach-Object { $Teclas["$_"] = "num$($_)Button" }
# Notacao de 03-casos-de-teste.md, para o relatorio
$Notacao = @{
    'C' = 'C'; 'CE' = 'CE'; 'BS' = '⌫'; 'NEG' = '±'; 'DEC' = ','; '/' = '÷'; '*' = '×'; '-' = '−'; '+' = '+'
    '=' = '='; '%' = '%'; 'SQRT' = '√'; 'SQR' = 'x²'; 'INV' = '1/x'
}
$NotacaoId = @{
    'percentButton' = '%'; 'clearEntryButton' = 'CE'; 'clearButton' = 'C'; 'backSpaceButton' = '⌫'
    'invertButton' = '1/x'; 'xpower2Button' = 'x²'; 'squareRootButton' = '√'; 'divideButton' = '÷'
    'multiplyButton' = '×'; 'minusButton' = '−'; 'plusButton' = '+'; 'equalButton' = '='
    'negateButton' = '±'; 'decimalSeparatorButton' = ','; 'ClearMemoryButton' = 'MC'; 'MemRecall' = 'MR'
    'MemPlus' = 'M+'; 'MemMinus' = 'M−'; 'memButton' = 'MS'; 'MemoryButton' = 'M▾'
    'HistoryButton' = 'Histórico'; 'TogglePaneButton' = 'Navegação'; 'NormalAlwaysOnTopButton' = 'Sobrepor'
}
0..9 | ForEach-Object { $NotacaoId["num$($_)Button"] = "$_" }

# Passos: tokens separados por espaco; numero com varios digitos = um botao por digito;
# '>' = ponto de leitura intermediario (o '→' da tabela). A leitura final e sempre feita.
$Casos = @(
    @{ Id = '3a-18'; Modo = '1'; Passos = 'C 1 / 3 =' }
    @{ Id = '3a-19'; Modo = '1'; Passos = 'C 2 / 3 =' }
    @{ Id = '3a-22'; Modo = '1'; Passos = 'C 1 / 3000 =' }
    @{ Id = '3a-21'; Modo = '1'; Passos = 'C 9999999999999999 + 1 =' }
    @{ Id = '3a-20'; Modo = '1'; Passos = 'C 1234567890123456 > 7' }
    @{ Id = '3a-08'; Modo = '1'; Passos = 'C 4 NEG SQRT' }
    @{ Id = '3a-26'; Modo = '1'; Passos = 'C 9999999999999999 SQR > SQR > SQR > SQR > SQR > SQR > SQR > SQR > SQR > SQR' }
    @{ Id = '3a-01'; Modo = '1'; Passos = 'C 7 + 5 =' }
    @{ Id = '3a-02'; Modo = '1'; Passos = 'C 2 + 3 * > 4 =' }
    @{ Id = '3a-02c'; Modo = '2'; Passos = 'C 2 + 3 * > 4 =' }
    @{ Id = '3a-03'; Modo = '1'; Passos = 'C 9 - 12 =' }
    @{ Id = '3a-04'; Modo = '1'; Passos = 'C 8 / 0 =' }
    @{ Id = '3a-05'; Modo = '1'; Passos = 'C 0 / 0 =' }
    @{ Id = '3a-06'; Modo = '1'; Passos = 'C / 0 =' }
    @{ Id = '3a-07'; Modo = '1'; Passos = 'C 0 INV' }
    @{ Id = '3a-10'; Modo = '1'; Passos = 'C 8 / 0 = > CE' }
    @{ Id = '3a-11'; Modo = '1'; Passos = 'C 2 + 3 = > =' }
    @{ Id = '3a-12'; Modo = '1'; Passos = 'C 2 + 3 = > 4 =' }
    @{ Id = '3a-13'; Modo = '1'; Passos = 'C 5 * =' }
    @{ Id = '3a-14'; Modo = '1'; Passos = 'C 5 + * 3 =' }
    @{ Id = '3a-15'; Modo = '1'; Passos = 'C 50 + 10 % > =' }
    @{ Id = '3a-16'; Modo = '1'; Passos = 'C 50 * 10 % > =' }
    @{ Id = '3a-17'; Modo = '1'; Passos = 'C 10 %' }
    @{ Id = '3a-24'; Modo = '1'; Passos = 'C 2 + 3 = > BS' }
    @{ Id = '3a-27'; Modo = '1'; Passos = 'C 9 SQRT' }
    @{ Id = '3a-28'; Modo = '1'; Passos = 'C 3 SQR > C 4 INV' }
    @{ Id = '3a-29'; Modo = '1'; Passos = 'C 5 + 3 CE 2 =' }
    @{ Id = '3a-09'; Modo = '1'; Passos = 'C 8 / 0 = > + > 5' }
    @{ Id = '3a-23'; Modo = '1'; Passos = 'C 000 > DEC > BS' }
    @{ Id = '3a-25'; Modo = '1'; Passos = 'C 0 NEG > C 5 NEG' }
)

$Log = New-Object System.Text.StringBuilder
function L([string]$t) { [void]$Log.AppendLine($t) }

function Nucleo {
    # CoreWindow com o conteudo XAML (os botoes da barra de titulo ficam fora)
    $j = Obter-Janela
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::ClassNameProperty, 'Windows.UI.Core.CoreWindow')
    $n = $j.FindFirst($Escopo::Children, $c)
    if ($n -eq $null) { throw 'CoreWindow nao encontrada' }
    return $n
}

function Elem([string]$id) {
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::AutomationIdProperty, $id)
    return (Nucleo).FindFirst($Escopo::Descendants, $c)
}

function Texto-Bruto([string]$id) {
    $e = Elem $id
    if ($e -eq $null) { return $null }
    return $e.Current.Name
}

# Name do visor = "A exibição é <texto>"; da expressao = "Expression é <texto>" (arvore-uia.txt)
function Sem-Prefixo([string]$nome) {
    if ($nome -eq $null) { return '(elemento ausente)' }
    $i = $nome.IndexOf(' é ')
    if ($i -ge 0) { return $nome.Substring($i + 3) }
    return $nome
}

function Ler-Estavel {
    $ant = $null
    for ($k = 0; $k -lt 40; $k++) {
        $v = Texto-Bruto 'CalculatorResults'; $x = Texto-Bruto 'CalculatorExpression'
        $atual = "$v`n$x"
        if ($atual -eq $ant) { break }
        $ant = $atual
        Start-Sleep -Milliseconds 150
    }
    return @($v, $x)
}

function Estado-Botoes {
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
    $hab = @(); $des = @()
    foreach ($b in (Nucleo).FindAll($Escopo::Descendants, $c)) {
        $id = $b.Current.AutomationId
        $nome = if ($NotacaoId.ContainsKey($id)) { $NotacaoId[$id] } else { $id }
        if ($b.Current.IsEnabled) { $hab += $nome } else { $des += $nome }
    }
    return "desabilitados: $($des -join ' ') ; habilitados: $($hab -join ' ')"
}

function Modo-Atual { return (Texto-Bruto 'Header') }

function Garantir-Modo([string]$tecla) {
    $alvo = if ($tecla -eq '1') { 'Padrão' } else { 'Científica' }
    for ($t = 0; $t -lt 3; $t++) {
        if ((Modo-Atual) -like "*$alvo") { return }
        Trocar-Modo (Obter-Janela) $tecla
    }
    throw "Nao consegui trocar para o modo $alvo (Header='$(Modo-Atual)')"
}

function Pressionar([string]$tok) {
    $id = $Teclas[$tok]
    $e = Elem $id
    if ($e -eq $null) { return "tecla $($Notacao[$tok]) ($id) ausente" }
    if (-not $e.Current.IsEnabled) { return "tecla $($Notacao[$tok]) desabilitada, nao pressionada" }
    $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    Start-Sleep -Milliseconds $PausaMs
    return $null
}

# O Name do UIA e o texto do Narrador ("quadrado (" no lugar de "sqr(", "de 0 ponto(s)" no lugar de "0,").
# O texto visivel do visor esta no filho bruto NormalOutput (RawView). A linha de expressao nao expoe
# texto visivel: e lida por captura de tela + OCR do Windows (Windows.Media.Ocr) e conferida na captura.
function Visor-Visivel {
    $w = [System.Windows.Automation.TreeWalker]::RawViewWalker
    $pilha = New-Object System.Collections.Stack
    $pilha.Push((Elem 'CalculatorResults'))
    while ($pilha.Count) {
        $e = $pilha.Pop()
        if ($e.Current.AutomationId -eq 'NormalOutput') { return $e.Current.Name }
        $f = $w.GetFirstChild($e)
        while ($f -ne $null) { $pilha.Push($f); $f = $w.GetNextSibling($f) }
    }
    return '(NormalOutput ausente)'
}

$AsTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Aguardar($op, [Type]$tipo) {
    $tarefa = $AsTask.MakeGenericMethod($tipo).Invoke($null, @($op))
    [void]$tarefa.Wait(-1)
    return $tarefa.Result
}
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$MotorOcr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$DirCapturas = Join-Path $DirScript 'capturas'
[void](New-Item -ItemType Directory -Force $DirCapturas)

function Ler-Png([string]$caminho) {
    $arq = Aguardar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($caminho)) ([Windows.Storage.StorageFile])
    $fluxo = Aguardar ($arq.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $dec = Aguardar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $sbmp = Aguardar ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $r = Aguardar ($MotorOcr.RecognizeAsync($sbmp)) ([Windows.Media.Ocr.OcrResult])
    $fluxo.Dispose()
    return $r.Text
}

# Captura visor + linha de expressao; devolve o OCR da faixa da expressao (ampliada 3x)
function Capturar([string]$nome) {
    Focar (Obter-Janela)
    $rr = (Elem 'CalculatorResults').Current.BoundingRectangle
    $topo = [int]$rr.Top - 34
    $larg = [int]$rr.Width; $alt = [int]$rr.Bottom - $topo
    $bmp = New-Object System.Drawing.Bitmap $larg, $alt
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen([int]$rr.Left, $topo, 0, 0, $bmp.Size)
    $bmp.Save((Join-Path $DirCapturas "$nome.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $faixa = 36
    $amp = New-Object System.Drawing.Bitmap ($larg * 3), ($faixa * 3)
    $g2 = [System.Drawing.Graphics]::FromImage($amp)
    $g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g2.DrawImage($bmp, (New-Object System.Drawing.Rectangle 0, 0, ($larg * 3), ($faixa * 3)),
        (New-Object System.Drawing.Rectangle 0, 0, $larg, $faixa), [System.Drawing.GraphicsUnit]::Pixel)
    $tmp = Join-Path $env:TEMP "calc-ocr-$nome.png"
    $amp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $g2.Dispose(); $bmp.Dispose(); $amp.Dispose()
    $t = Ler-Png $tmp
    Remove-Item $tmp
    return $t
}

function Eh-Erro([string]$visor) { return -not ($visor -match '^-?[0-9.,]+(e[+-][0-9]+)?$') }

# ---------------------------------------------------------------- Fase 3b (historico e memoria)
# AutomationIds de memoria: arvore-uia.txt; os dos submenus (HistoryListView, MemoryListView, ClearHistory...)
# sao os x:Name dos XBF (trabalho/pri/xbf-strings/Views/HistoryList.txt, Memory.txt) e sao conferidos na Etapa Arvore3b.
$Teclas['MS'] = 'memButton'; $Teclas['MR'] = 'MemRecall'; $Teclas['M+'] = 'MemPlus'; $Teclas['M-'] = 'MemMinus'
$Teclas['MC'] = 'ClearMemoryButton'
$Notacao['MS'] = 'MS'; $Notacao['MR'] = 'MR'; $Notacao['M+'] = 'M+'; $Notacao['M-'] = 'M−'; $Notacao['MC'] = 'MC'

function Elem-Raiz([string]$id) {
    # procura na CoreWindow e, se nao achar, em toda a janela (popups de flyout)
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::AutomationIdProperty, $id)
    $e = (Nucleo).FindFirst($Escopo::Descendants, $c)
    if ($e -eq $null) { $e = (Obter-Janela).FindFirst($Escopo::Descendants, $c) }
    return $e
}

if ($Etapa -eq 'Arvore3b') {
    $sb = New-Object System.Text.StringBuilder
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    [void]$sb.AppendLine("# Arvore UIA dos submenus de historico e memoria - Calculadora $($pkg.Version); $(Get-Date -Format s)")
    Garantir-Modo '1'
    foreach ($t in 'C', '7', '+', '5', '=', 'MS') { [void](Pressionar $t) }
    [void]$sb.AppendLine("visor antes: $(Visor-Visivel)")
    foreach ($par in @(@('HistoryButton', 'HistoryListView'), @('MemoryButton', 'MemoryListView'))) {
        $b = Elem $par[0]
        $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        Start-Sleep -Milliseconds 1200
        [void]$sb.AppendLine(''); [void]$sb.AppendLine("##### apos Invoke $($par[0]) #####")
        Despejar-Arvore (Obter-Janela) 0 $sb
        $l = Elem-Raiz $par[1]
        [void]$sb.AppendLine("$($par[1]) encontrado: $($l -ne $null)")
        # fecha invocando o mesmo botao de novo
        $b = Elem $par[0]
        try { $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { [void]$sb.AppendLine("Invoke para fechar falhou: $($_.Exception.Message)") }
        Start-Sleep -Milliseconds 1000
        [void]$sb.AppendLine("apos 2o Invoke: $($par[1]) ainda presente: $((Elem-Raiz $par[1]) -ne $null); visor: $(Visor-Visivel)")
    }
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'arvore-uia-3b.txt'), $sb.ToString(), $Utf8)
    Write-Output "arvore gravada: $(Join-Path $DirScript 'arvore-uia-3b.txt')"
    exit 0
}

# Texto visivel de um descendente (RawView) com o AutomationId dado; $null se nao houver
function Texto-Raw($elem, [string]$id) {
    $w = [System.Windows.Automation.TreeWalker]::RawViewWalker
    $pilha = New-Object System.Collections.Stack
    $pilha.Push($elem)
    while ($pilha.Count) {
        $e = $pilha.Pop()
        if ($e.Current.AutomationId -eq $id) { return $e.Current.Name }
        $f = $w.GetFirstChild($e)
        while ($f -ne $null) { $pilha.Push($f); $f = $w.GetNextSibling($f) }
    }
    return $null
}

function Invocar($e) { $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }

# Abre o submenu (botao HistoryButton/MemoryButton), executa o bloco com a lista e fecha invocando o botao de novo
function Com-Submenu([string]$botao, [string]$lista, [scriptblock]$bloco) {
    $b = Elem $botao
    if ($b -eq $null) { return '(botao ausente)' }
    if (-not $b.Current.IsEnabled) { return $null }
    Invocar $b
    $l = $null
    for ($k = 0; $k -lt 20 -and $l -eq $null; $k++) { Start-Sleep -Milliseconds 150; $l = Elem-Raiz $lista }
    if ($l -eq $null) { Start-Sleep -Milliseconds 300 }
    $r = & $bloco $l
    $b = Elem $botao
    if ($b.Current.Name -like 'Fechar*') { Invocar $b }
    for ($k = 0; $k -lt 20 -and (Elem-Raiz $lista) -ne $null; $k++) { Start-Sleep -Milliseconds 150 }
    if ((Elem-Raiz $lista) -ne $null) { throw "submenu $botao nao fechou" }
    Start-Sleep -Milliseconds 200
    return $r
}

# Todos os itens da lista, inclusive os virtualizados: ItemContainerPattern + VirtualizedItemPattern.Realize
# (a 1a execucao usou FindAll e leu so os itens realizados: 18 de 20 em 3b-08)
function Itens-Lista($l) {
    $res = New-Object System.Collections.Generic.List[object]
    $icp = $null
    try { $icp = $l.GetCurrentPattern([System.Windows.Automation.ItemContainerPattern]::Pattern) } catch {}
    if ($icp -eq $null) { foreach ($i in $l.FindAll($Escopo::Children, $CondItem)) { $res.Add($i) }; return $res }
    $ant = $null
    for ($k = 0; $k -lt 200; $k++) {
        $i = $icp.FindItemByProperty($ant, $null, $null)
        if ($i -eq $null) { break }
        try { $i.GetCurrentPattern([System.Windows.Automation.VirtualizedItemPattern]::Pattern).Realize(); Start-Sleep -Milliseconds 100 } catch {}
        $res.Add($i); $ant = $i
    }
    return $res
}

$CondItem = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, [System.Windows.Automation.ControlType]::ListItem)

# Historico: '[expressao | resultado]' por item (texto visivel dos TextBlocks), topo primeiro; Narrador no log
function Ler-Historico {
    $r = Com-Submenu 'HistoryButton' 'HistoryListView' {
        param($l)
        if ($l -eq $null) {
            $vazio = Texto-Raw (Obter-Janela) 'HistoryEmpty'
            return @{ Txt = "(vazia; HistoryEmpty='$vazio')"; N = 0; Narr = '' }
        }
        $itens = @(); $narr = @()
        foreach ($i in (Itens-Lista $l)) {
            $ex = Texto-Raw $i 'HistoryItemExpression'; $va = Texto-Raw $i 'HistoryItemValue'
            $itens += "[$ex | $va]"; $narr += "'$($i.Current.Name)'"
        }
        if ($itens.Count -eq 0) {
            $vazio = Texto-Raw (Obter-Janela) 'HistoryEmpty'
            return @{ Txt = "(vazia; HistoryEmpty='$vazio')"; N = 0; Narr = '' }
        }
        return @{ Txt = ($itens -join '; '); N = $itens.Count; Narr = ($narr -join ' ') }
    }
    if ($r -eq $null) { return @{ Txt = '(botao de historico desabilitado)'; N = 0; Narr = '' } }
    return $r
}

# Memoria: valores visiveis, topo primeiro
function Ler-Memoria {
    $r = Com-Submenu 'MemoryButton' 'MemoryListView' {
        param($l)
        if ($l -eq $null) { return @{ Txt = '(submenu aberto, lista ausente)'; Narr = '' } }
        $itens = @(); $narr = @()
        foreach ($i in (Itens-Lista $l)) {
            $v = Texto-Raw $i 'MemoryItemValue'
            $itens += "$v"; $narr += "'$($i.Current.Name)'"
        }
        return @{ Txt = ($itens -join '; '); Narr = ($narr -join ' ') }
    }
    if ($r -eq $null) { return @{ Txt = '(vazia; M▾ desabilitado)'; Narr = '' } }
    return $r
}

function Estado-Memoria {
    $s = @()
    foreach ($p in @(@('ClearMemoryButton', 'MC'), @('MemRecall', 'MR'), @('MemPlus', 'M+'), @('MemMinus', 'M−'), @('memButton', 'MS'), @('MemoryButton', 'M▾'))) {
        $e = Elem $p[0]
        $s += "$($p[1])=$(if ($e -eq $null) { '?' } elseif ($e.Current.IsEnabled) { 'hab' } else { 'des' })"
    }
    return ($s -join ' ')
}

# LH: abre o historico e aciona "Limpar todo o historico" (se a lista estiver vazia o botao nao existe)
function Limpar-Historico {
    $r = Com-Submenu 'HistoryButton' 'HistoryListView' {
        param($l)
        $b = Elem-Raiz 'ClearHistory'
        if ($b -ne $null -and $b.Current.IsEnabled) { Invocar $b; Start-Sleep -Milliseconds 500; return 'limpo' }
        return 'nada a limpar'
    }
    return $r
}

function Limpar-Estado([string]$modoCaso) {
    $log = @()
    foreach ($m in '2', '1') {
        Garantir-Modo $m
        $log += "historico modo $($m): $(Limpar-Historico)"
    }
    $mc = Elem 'ClearMemoryButton'
    if ($mc.Current.IsEnabled) { Invocar $mc; Start-Sleep -Milliseconds 300; $log += 'MC' }
    Garantir-Modo $modoCaso
    [void](Pressionar 'C'); Start-Sleep -Milliseconds 300
    $h = Ler-Historico; $mem = Ler-Memoria
    if ($h.N -ne 0 -or -not $mem.Txt.StartsWith('(vazia')) { throw "estado inicial nao ficou limpo: hist=$($h.Txt) mem=$($mem.Txt)" }
    return ($log -join '; ')
}

if ($Etapa -eq 'Casos3b') {
    $Seta3 = [char]0x2192
    $Casos3b = @(
        @{ Id = '3b-09'; Modo = '1'; Passos = '7 + 5 = > ALT2 > 1 + 1 = > ALT1' }
        @{ Id = '3b-11'; Modo = '1'; Passos = '7 MS' }
        @{ Id = '3b-18'; Modo = '1'; Passos = '7 MS > MC' }
        @{ Id = '3b-19'; Modo = '1'; Passos = '1 / 3 = MS C MR > * 3 =' }
        @{ Id = '3b-25'; Modo = '1'; Passos = '7 MS > ALT2 > MR' }
        @{ Id = '3b-26'; Modo = '1'; Passos = '7 MS 8 / 0 = > C MR' }
        @{ Id = '3b-01'; Modo = '1'; Passos = '7 + 5 =' }
        @{ Id = '3b-02'; Modo = '1'; Passos = '2 + 3 * > 4 =' }
        @{ Id = '3b-02c'; Modo = '2'; Passos = '2 + 3 * > 4 =' }
        @{ Id = '3b-03'; Modo = '1'; Passos = '2 + 3 = > =' }
        @{ Id = '3b-04'; Modo = '1'; Passos = '5 = > =' }
        @{ Id = '3b-05'; Modo = '1'; Passos = '8 / 0 = > C 1 + 1 =' }
        @{ Id = '3b-06'; Modo = '1'; Passos = '9 SQRT > 5' }
        @{ Id = '3b-07'; Modo = '1'; Passos = '9 SQRT =' }
        @{ Id = '3b-08'; Modo = '1'; Passos = ('1 + 1 =' + (' =' * 20)) }
        @{ Id = '3b-10'; Modo = '1'; Passos = '1 + 1 = > LH' }
        @{ Id = '3b-12'; Modo = '1'; Passos = '7 MS 3 MS' }
        @{ Id = '3b-13'; Modo = '1'; Passos = '7 MS 3 M+' }
        @{ Id = '3b-14'; Modo = '1'; Passos = '7 MS 3 M-' }
        @{ Id = '3b-15'; Modo = '1'; Passos = '5 M+' }
        @{ Id = '3b-16'; Modo = '1'; Passos = '5 M-' }
        @{ Id = '3b-17'; Modo = '1'; Passos = '7 MS 3 MS C MR' }
        @{ Id = '3b-20'; Modo = '1'; Passos = '1234 MS' }
        @{ Id = '3b-21'; Modo = '1'; Passos = '2 + 3 = > MS' }
        @{ Id = '3b-22'; Modo = '1'; Passos = '7 MS C 5 + MR =' }
        @{ Id = '3b-23'; Modo = '1'; Passos = '7 MS C 9 SQRT MR' }
        @{ Id = '3b-24'; Modo = '1'; Passos = '7 MS C 2 + 3 M+ > =' }
    )
    if ($env:CASOS3B) { $Casos3b = @($Casos3b | Where-Object { ($env:CASOS3B -split ',') -contains $_.Id }) }
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    $Linhas = New-Object System.Collections.Generic.List[string]
    L "# Execucao 3b $(Get-Date -Format s) - Calculadora $($pkg.Version) $($pkg.Architecture), cultura $((Get-Culture).Name), UI $((Get-UICulture).Name)"
    foreach ($arq in 'CalculatorApp.exe', 'CalculatorApp.dll', 'CalcViewModel.dll') {
        try { L "# SHA-256 instalado $arq = $((Get-FileHash -Algorithm SHA256 (Join-Path $pkg.InstallLocation $arq)).Hash.ToLower())" }
        catch { L "# SHA-256 instalado $arq = (sem acesso: $($_.Exception.Message))" }
    }
    $Linhas.Add("# Calculadora $($pkg.Version) $($pkg.Architecture); cultura $((Get-Culture).Name); UI $((Get-UICulture).Name); $(Get-Date -Format s)")
    $Linhas.Add("# Formato: ID [$($Seta3)n apos X]: visor | expressao(OCR) | hist: [expressao | resultado]; ... (topo primeiro) | mem: v1; v2 (topo primeiro) | botoes -- obs")
    $Linhas.Add("# visor = NormalOutput (UIA RawView); hist/mem = texto dos TextBlocks HistoryItemExpression/HistoryItemValue/MemoryItemValue (UIA RawView, sem transcricao); expressao = OCR da captura capturas/<ID>-<n|final>.png")
    foreach ($caso in $Casos3b) {
        L ''; L "== $($caso.Id) (modo Alt+$($caso.Modo)): $($caso.Passos)"
        L "   preparo: $(Limpar-Estado $caso.Modo)"
        $obs = New-Object System.Collections.Generic.List[string]
        $nLeitura = 0; $ultima = ''
        $toks = @($caso.Passos -split ' ' | Where-Object { $_ -ne '' }) + @('>FIM')
        foreach ($tok in $toks) {
            if ($tok -eq '>' -or $tok -eq '>FIM') {
                $r = Ler-Estavel
                $visor = Visor-Visivel
                $nomeCap = if ($tok -eq '>') { "$($caso.Id)-$($nLeitura + 1)" } else { "$($caso.Id)-final" }
                $expr = Capturar $nomeCap
                if ([string]::IsNullOrEmpty($expr)) { $expr = '(vazia)' }
                $bot = Estado-Memoria
                $h = Ler-Historico; $mem = Ler-Memoria
                $visor2 = Visor-Visivel
                if ($visor2 -ne $visor) { $obs.Add("ATENCAO: visor mudou ao ler as listas ('$visor' -> '$visor2')") }
                L "   leitura apos [$ultima]: NormalOutput='$visor' expressao.Name='$($r[1])' OCR='$expr' hist.N=$($h.N) narrador.hist=$($h.Narr) narrador.mem=$($mem.Narr) captura=capturas/$nomeCap.png"
                $extra = @()
                if ($obs.Count) { $extra += $obs; $obs.Clear() }
                $sufixo = if ($extra.Count) { ' -- ' + ($extra -join '; ') } else { '' }
                $corpo = "$visor | $expr | hist($($h.N)): $($h.Txt) | mem: $($mem.Txt) | $bot$sufixo"
                if ($tok -eq '>') { $nLeitura++; $Linhas.Add("$($caso.Id) $Seta3$nLeitura [apos $ultima]: $corpo") }
                else { $Linhas.Add("$($caso.Id): $corpo") }
                continue
            }
            if ($tok -eq 'ALT1' -or $tok -eq 'ALT2') {
                Garantir-Modo $tok.Substring(3); Start-Sleep -Milliseconds 500
                $ultima = "[Alt+$($tok.Substring(3))]"; continue
            }
            if ($tok -eq 'LH') { $obs.Add("LH: $(Limpar-Historico)"); $ultima = 'LH'; continue }
            $seq = if ($tok -match '^[0-9]{2,}$') { $tok.ToCharArray() | ForEach-Object { "$_" } } else { @($tok) }
            foreach ($t in $seq) {
                $p = Pressionar $t
                if ($p) { $obs.Add($p); L "   $p" }
                $ultima = $Notacao[$t]; if (-not $ultima) { $ultima = $t }
            }
        }
    }
    Garantir-Modo '1'
    $saida = Join-Path $DirProjeto 'relatorio\resultados-reais-3b.txt'
    [System.IO.File]::WriteAllText($saida, ($Linhas -join "`n") + "`n", $Utf8)
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'log-execucao-3b.txt'), $Log.ToString(), $Utf8)
    Write-Output "resultados gravados: $saida"
    exit 0
}

# ---------------------------------------------------------------- Fase 3c (modo cientifico)
# AutomationIds: arvore-uia.txt (painel) e xbf-strings/Views/CalculatorScientificOperators.txt (submenus), conferidos na Etapa Arvore3c.
function Padrao-Toggle($e) { try { return $e.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern) } catch { return $null } }
function Estado-Toggle([string]$id) {
    $e = Elem-Raiz $id
    if ($e -eq $null) { return $null }
    $t = Padrao-Toggle $e
    if ($t -eq $null) { return $null }
    return ($t.Current.ToggleState -eq [System.Windows.Automation.ToggleState]::On)
}
function Ajustar-Toggle([string]$id, [bool]$ligado) {
    for ($k = 0; $k -lt 3; $k++) {
        $s = Estado-Toggle $id
        if ($s -eq $null) { return "toggle $id ausente" }
        if ($s -eq $ligado) { return $null }
        (Padrao-Toggle (Elem-Raiz $id)).Toggle(); Start-Sleep -Milliseconds 400
    }
    return "toggle $id nao ficou em $ligado"
}
function Clicar([string]$id) {
    $e = Elem-Raiz $id
    if ($e -eq $null) { return "botao $id ausente" }
    if (-not $e.Current.IsEnabled) { return "botao $id desabilitado, nao pressionado" }
    try { Invocar $e } catch {
        $t = Padrao-Toggle $e
        if ($t -ne $null) { $t.Toggle() }
        else {
            try { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
            catch { return "botao $id sem Invoke/Toggle/SelectionItem" }
        }
    }
    Start-Sleep -Milliseconds $PausaMs
    return $null
}
function Visivel([string]$id) { $e = Elem-Raiz $id; return ($e -ne $null -and -not $e.Current.IsOffscreen) }
function Abrir-Trig {
    if ((Visivel 'sinButton') -or (Visivel 'invsinButton')) { return $null }
    $r = Clicar 'trigButton'
    for ($k = 0; $k -lt 20; $k++) { if ((Visivel 'sinButton') -or (Visivel 'invsinButton')) { return $r }; Start-Sleep -Milliseconds 150 }
    return "submenu Trigonometria nao abriu"
}
function Fechar-Trig {
    # Sonda3c: o submenu fecha sozinho apos uma funcao; Esc com foco no submenu o fecha sem limpar o visor
    foreach ($id in 'sinButton', 'invsinButton') {
        if (Visivel $id) {
            try { (Elem-Raiz $id).SetFocus() } catch {}
            [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep -Milliseconds 500
            break
        }
    }
    if ((Visivel 'sinButton') -or (Visivel 'invsinButton')) { throw 'submenu Trigonometria nao fechou' }
}
$Angulos = @{ 'DEG' = 'degButton'; 'RAD' = 'radButton'; 'GRAD' = 'gradButton' }
function Angulo-Atual { foreach ($k in $Angulos.Keys) { if ((Elem-Raiz $Angulos[$k]) -ne $null) { return $k } }; return '?' }
function Ajustar-Angulo([string]$alvo) {
    for ($k = 0; $k -lt 4; $k++) {
        $a = Angulo-Atual
        if ($a -eq $alvo) { return $null }
        if ($a -eq '?') { return 'botao de angulo ausente' }
        [void](Clicar $Angulos[$a]); Start-Sleep -Milliseconds 300
    }
    return "angulo nao chegou a $alvo"
}
$Teclas3c = @{
    'C' = 'clearButton'; 'NEG' = 'negateButton'; 'DEC' = 'decimalSeparatorButton'; '/' = 'divideButton'; '*' = 'multiplyButton'
    '-' = 'minusButton'; '+' = 'plusButton'; '=' = 'equalButton'; 'POW' = 'powerButton'; 'P10' = 'powerOf10Button'
    'LOG' = 'logBase10Button'; 'LN' = 'logBaseEButton'; 'FACT' = 'factorialButton'; 'MOD' = 'modButton'; 'EXP' = 'expButton'
    'ABS' = 'absButton'; '(' = 'openParenthesisButton'; ')' = 'closeParenthesisButton'; 'PI' = 'piButton'; 'E' = 'eulerButton'
}
0..9 | ForEach-Object { $Teclas3c["$_"] = "num$($_)Button" }
$Notacao3c = @{ 'NEG' = '±'; 'DEC' = ','; '/' = '÷'; '*' = '×'; '-' = '−'; 'POW' = 'x^y'; 'P10' = '10^x'; 'LOG' = 'log'; 'LN' = 'ln'
    'FACT' = 'n!'; 'MOD' = 'mod'; 'EXP' = 'exp'; 'ABS' = '|x|'; 'PI' = 'π'; 'E' = 'e'; 'SIN' = 'sin'; 'COS' = 'cos'; 'TAN' = 'tan'
    'ASIN' = 'sin⁻¹'; 'ACOS' = 'cos⁻¹'; 'ATAN' = 'tan⁻¹'; 'YROOT' = 'ʸ√x'; 'LOGY' = 'logᵧx'; 'EX' = 'eˣ'; 'FE' = 'F-E'; 'ANG' = '[angulo]' }
$Trig3c = @{ 'SIN' = @('sinButton', $false); 'COS' = @('cosButton', $false); 'TAN' = @('tanButton', $false)
    'ASIN' = @('invsinButton', $true); 'ACOS' = @('invcosButton', $true); 'ATAN' = @('invtanButton', $true) }
$Shift3c = @{ 'YROOT' = 'ySquareRootButton'; 'LOGY' = 'logBaseY'; 'EX' = 'powerOfEButton' }

function Pressionar3c([string]$tok) {
    if ($Trig3c.ContainsKey($tok)) {
        $r = Abrir-Trig; if ($r) { return $r }
        $r = Ajustar-Toggle 'trigShiftButton' $Trig3c[$tok][1]; if ($r) { return $r }
        $r = Clicar $Trig3c[$tok][0]
        Start-Sleep -Milliseconds 300
        if ((Visivel 'sinButton') -or (Visivel 'invsinButton')) { [void](Ajustar-Toggle 'trigShiftButton' $false); Fechar-Trig }
        return $r
    }
    if ($Shift3c.ContainsKey($tok)) {
        $r = Ajustar-Toggle 'shiftButton' $true; if ($r) { return $r }
        $r = Clicar $Shift3c[$tok]
        [void](Ajustar-Toggle 'shiftButton' $false)
        return $r
    }
    if ($tok -eq 'FE') { $e = Elem-Raiz 'ftoeButton'; (Padrao-Toggle $e).Toggle(); Start-Sleep -Milliseconds $PausaMs; return $null }
    if ($tok -eq 'ANG') { $a = Angulo-Atual; return (Clicar $Angulos[$a]) }
    return (Clicar $Teclas3c[$tok])
}

function Preparar3c([string]$angulo) {
    $log = @()
    Garantir-Modo '2'
    Fechar-Trig
    foreach ($t in 'shiftButton', 'trigShiftButton') { $s = Estado-Toggle $t; if ($s) { $log += "$t desligado"; [void](Ajustar-Toggle $t $false) } }
    if (Estado-Toggle 'ftoeButton') { $log += 'F-E desligado'; (Padrao-Toggle (Elem-Raiz 'ftoeButton')).Toggle(); Start-Sleep -Milliseconds 300 }
    # no Cientifico C e CE dividem a posicao: aperta o que estiver visivel ate o C aparecer e o visor zerar
    for ($k = 0; $k -lt 4; $k++) {
        foreach ($id in 'clearEntryButton', 'clearButton') { if (Visivel $id) { [void](Clicar $id); Start-Sleep -Milliseconds 300 } }
        if ((Visivel 'clearButton') -and (Visor-Visivel) -eq '0') { break }
    }
    $r = Ajustar-Angulo $angulo; if ($r) { throw $r }
    $log += "angulo $(Angulo-Atual)"
    if ((Visor-Visivel) -ne '0') { throw "estado inicial: visor '$(Visor-Visivel)'" }
    return ($log -join '; ')
}

if ($Etapa -eq 'Arvore3c') {
    $sb = New-Object System.Text.StringBuilder
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    [void]$sb.AppendLine("# Arvore UIA do modo Cientifico (submenus) - Calculadora $($pkg.Version); $(Get-Date -Format s)")
    Garantir-Modo '2'
    [void](Clicar 'clearButton')
    foreach ($id in 'trigButton', 'shiftButton', 'trigShiftButton', 'ftoeButton', 'degButton', 'radButton', 'gradButton') {
        $e = Elem-Raiz $id
        if ($e -eq $null) { [void]$sb.AppendLine("$id ausente"); continue }
        $pat = ($e.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }) -join ','
        [void]$sb.AppendLine("$id Name='$($e.Current.Name)' padroes=$pat toggle=$(Estado-Toggle $id)")
    }
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### angulo: 4 cliques #####')
    for ($k = 0; $k -lt 4; $k++) { $a = Angulo-Atual; [void]$sb.AppendLine("antes do clique $($k+1): $a"); [void](Clicar $Angulos[$a]); Start-Sleep -Milliseconds 300 }
    [void]$sb.AppendLine("final: $(Angulo-Atual)")
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### apos abrir Trigonometria #####')
    [void]$sb.AppendLine("Abrir-Trig: $(Abrir-Trig)")
    Despejar-Arvore (Obter-Janela) 0 $sb
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### apos ligar trigShiftButton #####')
    [void]$sb.AppendLine("Ajustar-Toggle: $(Ajustar-Toggle 'trigShiftButton' $true)")
    foreach ($id in 'sinButton', 'invsinButton', 'invcosButton', 'invtanButton') { [void]$sb.AppendLine("$id visivel=$(Visivel $id)") }
    [void](Ajustar-Toggle 'trigShiftButton' $false)
    Fechar-Trig
    [void]$sb.AppendLine("submenu fechado: $(-not ((Visivel 'sinButton') -or (Visivel 'invsinButton')))")
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### apos ligar shiftButton (2nd) #####')
    [void]$sb.AppendLine("Ajustar-Toggle: $(Ajustar-Toggle 'shiftButton' $true)")
    foreach ($id in 'ySquareRootButton', 'logBaseY', 'powerOfEButton', 'powerButton', 'logBaseEButton') { [void]$sb.AppendLine("$id visivel=$(Visivel $id)") }
    [void](Ajustar-Toggle 'shiftButton' $false)
    [void]$sb.AppendLine("visor no fim: $(Visivel 'clearButton') '$(Visor-Visivel)'")
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'arvore-uia-3c.txt'), $sb.ToString(), $Utf8)
    Write-Output "arvore gravada: $(Join-Path $DirScript 'arvore-uia-3c.txt')"
    exit 0
}


if ($Etapa -eq 'Sonda3c') {
    $sb = New-Object System.Text.StringBuilder
    function S([string]$t) { [void]$sb.AppendLine($t) }
    Garantir-Modo '2'; [void](Clicar 'clearButton'); [void](Clicar 'num5Button')
    S "visor inicial: $(Visor-Visivel)"
    S "abrir: $(Abrir-Trig) aberto=$(Visivel 'sinButton')"
    $t = Padrao-Toggle (Elem-Raiz 'trigButton'); S "trigButton toggle=$($t.Current.ToggleState)"
    $t.Toggle(); Start-Sleep -Milliseconds 800
    S "(a) apos Toggle no trigButton: aberto=$(Visivel 'sinButton') visor=$(Visor-Visivel)"
    if (Visivel 'sinButton') {
        $f = Elem-Raiz 'Trigflyout'
        $pats = ($f.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }) -join ','
        S "Trigflyout padroes=$pats"
        try { (Elem-Raiz 'sinButton').SetFocus() } catch {}
        [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep -Milliseconds 800
        S "(b) apos ESC com foco no submenu: aberto=$(Visivel 'sinButton') visor=$(Visor-Visivel)"
    }
    S "abrir de novo: $(Abrir-Trig) aberto=$(Visivel 'sinButton')"
    [void](Clicar 'cosButton'); Start-Sleep -Milliseconds 800
    S "(c) apos cos: aberto=$(Visivel 'cosButton') visor=$(Visor-Visivel) expr=$(Texto-Bruto 'CalculatorExpression')"
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'sonda-3c.txt'), $sb.ToString(), $Utf8)
    exit 0
}

if ($Etapa -eq 'Casos3c') {
    $Seta3 = [char]0x2192
    # Passos: tokens separados por espaco; numero com varios digitos = um botao por digito; '>' = leitura intermediaria
    $Casos3c = @(
        @{ Id = '3c-01'; Ang = 'DEG'; Passos = '90 COS' }
        @{ Id = '3c-02'; Ang = 'DEG'; Passos = '90 TAN' }
        @{ Id = '3c-03'; Ang = 'RAD'; Passos = 'PI SIN' }
        @{ Id = '3c-04'; Ang = 'DEG'; Passos = '180 SIN' }
        @{ Id = '3c-05'; Ang = 'RAD'; Passos = '0 COS' }
        @{ Id = '3c-06'; Ang = 'DEG'; Passos = '1 ASIN' }
        @{ Id = '3c-07'; Ang = 'DEG'; Passos = '2 ASIN' }
        @{ Id = '3c-08'; Ang = 'DEG'; Passos = '1 EXP 100 > SIN' }
        @{ Id = '3c-09'; Ang = 'DEG'; Passos = '1 ANG 2' }
        @{ Id = '3c-10'; Ang = 'DEG'; Passos = '5 FACT' }
        @{ Id = '3c-11'; Ang = 'DEG'; Passos = '0 FACT' }
        @{ Id = '3c-12'; Ang = 'DEG'; Passos = '20 FACT' }
        @{ Id = '3c-13'; Ang = 'DEG'; Passos = '1 NEG FACT' }
        @{ Id = '3c-14'; Ang = 'DEG'; Passos = '3250 FACT' }
        @{ Id = '3c-15'; Ang = 'DEG'; Passos = '7 MOD 3 =' }
        @{ Id = '3c-16'; Ang = 'DEG'; Passos = '7 NEG MOD 3 =' }
        @{ Id = '3c-17'; Ang = 'DEG'; Passos = '7 MOD 3 NEG =' }
        @{ Id = '3c-18'; Ang = 'DEG'; Passos = '7 DEC 5 MOD 2 =' }
        @{ Id = '3c-19'; Ang = 'DEG'; Passos = '5 MOD 0 =' }
        @{ Id = '3c-20'; Ang = 'DEG'; Passos = '2 POW 10 =' }
        @{ Id = '3c-21'; Ang = 'DEG'; Passos = '2 POW 1 NEG =' }
        @{ Id = '3c-22'; Ang = 'DEG'; Passos = '0 POW 1 NEG =' }
        @{ Id = '3c-23'; Ang = 'DEG'; Passos = '3 P10' }
        @{ Id = '3c-24'; Ang = 'DEG'; Passos = '31 P10' }
        @{ Id = '3c-25'; Ang = 'DEG'; Passos = '32 P10' }
        @{ Id = '3c-26'; Ang = 'DEG'; Passos = '0 LOG' }
        @{ Id = '3c-27'; Ang = 'DEG'; Passos = '1 NEG LN' }
        @{ Id = '3c-28'; Ang = 'DEG'; Passos = '2 EXP > 3 > =' }
        @{ Id = '3c-29'; Ang = 'DEG'; Passos = '1 EXP 4 NEG > =' }
        @{ Id = '3c-30'; Ang = 'DEG'; Passos = '123 = > FE > FE' }
        @{ Id = '3c-31'; Ang = 'DEG'; Passos = '5 NEG ABS' }
        @{ Id = '3c-32'; Ang = 'DEG'; Passos = '1 / 3 =' }
        @{ Id = '3c-33'; Ang = 'DEG'; Passos = '2 / 30 =' }
        @{ Id = '3c-34'; Ang = 'DEG'; Passos = '1 / 300 =' }
        @{ Id = '3c-35'; Ang = 'DEG'; Passos = '1 / 3000 =' }
        @{ Id = '3c-36'; Ang = 'DEG'; Passos = '12345678901234567890123456789012 > 3' }
        @{ Id = '3c-37'; Ang = 'DEG'; Passos = '2 * 3 + > 4 * 5 =' }
        @{ Id = '3c-38'; Ang = 'DEG'; Passos = '2 POW 3 POW > 2 =' }
        @{ Id = '3c-39'; Ang = 'DEG'; Passos = '2 + 3 * 4 POW 2 =' }
        @{ Id = '3c-40'; Ang = 'DEG'; Passos = '7 MOD 4 * 2 =' }
        @{ Id = '3c-41'; Ang = 'DEG'; Passos = '2 + 3 + * > 4 =' }
        @{ Id = '3c-42'; Ang = 'DEG'; Passos = '( 2 + 3 ) > * 4 =' }
        @{ Id = '3c-43'; Ang = 'DEG'; Passos = '( 2 + 3 =' }
        @{ Id = '3c-44'; Ang = 'DEG'; Passos = '2 * ( 3 + ( 4 - 1 =' }
        @{ Id = '3c-45'; Ang = 'DEG'; Passos = '2 ( 3 + 4 ) =' }
        @{ Id = '3c-46'; Ang = 'DEG'; Passos = '1 + ( 2 + 3 ) > 4 > =' }
        @{ Id = '3c-47'; Ang = 'DEG'; Passos = '2 + 3 ) * 4 =' }
        @{ Id = '3c-50'; Ang = 'DEG'; Passos = '30 SIN' }
        @{ Id = '3c-51'; Ang = 'DEG'; Passos = '60 COS' }
        @{ Id = '3c-52'; Ang = 'DEG'; Passos = '45 SIN' }
        @{ Id = '3c-53'; Ang = 'DEG'; Passos = '45 TAN' }
        @{ Id = '3c-54'; Ang = 'DEG'; Passos = '30 NEG SIN' }
        @{ Id = '3c-55'; Ang = 'RAD'; Passos = '1 SIN' }
        @{ Id = '3c-56'; Ang = 'RAD'; Passos = '1 TAN' }
        @{ Id = '3c-57'; Ang = 'GRAD'; Passos = '1 COS' }
        @{ Id = '3c-58'; Ang = 'GRAD'; Passos = '100 SIN' }
        @{ Id = '3c-59'; Ang = 'DEG'; Passos = '0 DEC 5 ASIN' }
        @{ Id = '3c-60'; Ang = 'RAD'; Passos = '0 DEC 5 ACOS' }
        @{ Id = '3c-61'; Ang = 'GRAD'; Passos = '1 ATAN' }
        @{ Id = '3c-62'; Ang = 'DEG'; Passos = '1 NEG EXP 100 > SIN' }
        @{ Id = '3c-63'; Ang = 'DEG'; Passos = 'PI > FE > FE' }
        @{ Id = '3c-64'; Ang = 'DEG'; Passos = 'E' }
        @{ Id = '3c-65'; Ang = 'DEG'; Passos = '1 EX' }
        @{ Id = '3c-66'; Ang = 'DEG'; Passos = '10 NEG EX' }
        @{ Id = '3c-67'; Ang = 'DEG'; Passos = '10 LN' }
        @{ Id = '3c-68'; Ang = 'DEG'; Passos = '2 LOG' }
        @{ Id = '3c-69'; Ang = 'DEG'; Passos = '1000 LOG' }
        @{ Id = '3c-70'; Ang = 'DEG'; Passos = '0 DEC 5 P10' }
        @{ Id = '3c-71'; Ang = 'DEG'; Passos = '2 POW 0 DEC 5 =' }
        @{ Id = '3c-72'; Ang = 'DEG'; Passos = '27 YROOT 3 =' }
        @{ Id = '3c-73'; Ang = 'DEG'; Passos = '8 NEG YROOT 3 =' }
        @{ Id = '3c-74'; Ang = 'DEG'; Passos = '8 LOGY 2 =' }
        @{ Id = '3c-75'; Ang = 'DEG'; Passos = '0 DEC 5 FACT' }
    )
    if ($env:CASOS3C) { $Casos3c = @($Casos3c | Where-Object { ($env:CASOS3C -split ',') -contains $_.Id }) }
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    $Linhas = New-Object System.Collections.Generic.List[string]
    L "# Execucao 3c $(Get-Date -Format s) - Calculadora $($pkg.Version) $($pkg.Architecture), cultura $((Get-Culture).Name), UI $((Get-UICulture).Name)"
    foreach ($arq in 'CalculatorApp.exe', 'CalculatorApp.dll', 'CalcViewModel.dll') {
        try { L "# SHA-256 instalado $arq = $((Get-FileHash -Algorithm SHA256 (Join-Path $pkg.InstallLocation $arq)).Hash.ToLower())" }
        catch { L "# SHA-256 instalado $arq = (sem acesso: $($_.Exception.Message))" }
    }
    $Linhas.Add("# Calculadora $($pkg.Version) $($pkg.Architecture); cultura $((Get-Culture).Name); UI $((Get-UICulture).Name); $(Get-Date -Format s)")
    $Linhas.Add("# Formato: ID [$($Seta3)n apos X]: visor | expressao(OCR) -- obs; visor = NormalOutput (UIA RawView); expressao = OCR de capturas/<ID>-<n|final>.png")
    foreach ($caso in $Casos3c) {
        L ''; L "== $($caso.Id) (Cientifico, $($caso.Ang)): $($caso.Passos)"
        L "   preparo: $(Preparar3c $caso.Ang)"
        $obs = New-Object System.Collections.Generic.List[string]
        $nLeitura = 0; $ultima = ''
        $toks = @($caso.Passos -split ' ' | Where-Object { $_ -ne '' }) + @('>FIM')
        foreach ($tok in $toks) {
            if ($tok -eq '>' -or $tok -eq '>FIM') {
                $r = Ler-Estavel
                $visor = Visor-Visivel
                $nomeCap = if ($tok -eq '>') { "$($caso.Id)-$($nLeitura + 1)" } else { "$($caso.Id)-final" }
                $expr = Capturar $nomeCap
                if ([string]::IsNullOrEmpty($expr)) { $expr = '(vazia)' }
                L "   leitura apos [$ultima]: NormalOutput='$visor' expressao.Name='$($r[1])' OCR='$expr' angulo=$(Angulo-Atual) captura=capturas/$nomeCap.png"
                $sufixo = if ($obs.Count) { ' -- ' + ($obs -join '; ') } else { '' }
                $obs.Clear()
                $corpo = "$visor | $expr$sufixo"
                if ($tok -eq '>') { $nLeitura++; $Linhas.Add("$($caso.Id) $Seta3$nLeitura [apos $ultima]: $corpo") }
                else { $Linhas.Add("$($caso.Id): $corpo") }
                continue
            }
            $seq = if ($tok -match '^[0-9]{2,}$') { $tok.ToCharArray() | ForEach-Object { "$_" } } else { @($tok) }
            foreach ($t in $seq) {
                $p = Pressionar3c $t
                if ($p) { $obs.Add($p); L "   $p" }
                $ultima = $Notacao3c[$t]; if (-not $ultima) { $ultima = $t }
            }
        }
    }
    Preparar3c 'DEG' | Out-Null
    $saida = Join-Path $DirProjeto 'relatorio\resultados-reais-3c.txt'
    [System.IO.File]::WriteAllText($saida, ($Linhas -join "`n") + "`n", $Utf8)
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'log-execucao-3c.txt'), $Log.ToString(), $Utf8)
    Write-Output "resultados gravados: $saida"
    exit 0
}

# ---------------------------------------------------------------- Fase 3d (modo programador)
function Garantir-Programador {
    for ($t = 0; $t -lt 3; $t++) {
        if ((Modo-Atual) -like '*Programador') { return }
        Trocar-Modo (Obter-Janela) '4'   # Alt+3 abre o modo Representacao grafica nesta versao
    }
    throw "Nao consegui trocar para o modo Programador (Header='$(Modo-Atual)')"
}
function Despejar-Raw($elem, [int]$nivel, [System.Text.StringBuilder]$sb) {
    $c = $elem.Current
    $tipo = $c.ControlType.ProgrammaticName -replace '^ControlType\.', ''
    $tg = ''; $t = Padrao-Toggle $elem; if ($t) { $tg = " toggle=$($t.Current.ToggleState)" }
    [void]$sb.AppendLine(('{0}[{1}] Name="{2}" AutomationId="{3}" Class="{4}" Enabled={5} Offscreen={6}{7}' -f
            ('  ' * $nivel), $tipo, $c.Name, $c.AutomationId, $c.ClassName, $c.IsEnabled, $c.IsOffscreen, $tg))
    if ($nivel -gt 40) { return }
    $w = [System.Windows.Automation.TreeWalker]::RawViewWalker
    $f = $w.GetFirstChild($elem)
    while ($f -ne $null) { Despejar-Raw $f ($nivel + 1) $sb; $f = $w.GetNextSibling($f) }
}

if ($Etapa -eq 'Arvore3d') {
    $sb = New-Object System.Text.StringBuilder
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    [void]$sb.AppendLine("# Arvore UIA do modo Programador - Calculadora $($pkg.Version); $(Get-Date -Format s)")
    Garantir-Programador
    [void](Clicar 'clearButton')
    [void]$sb.AppendLine("Header='$(Modo-Atual)'")
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### RawView da janela (teclado completo) #####')
    Despejar-Raw (Obter-Janela) 0 $sb
    foreach ($par in @(@('bitwiseButton', 'Bit a bit'), @('bitShiftButton', 'Bit-shift'))) {
        [void]$sb.AppendLine(''); [void]$sb.AppendLine("##### apos clicar $($par[0]) ($($par[1])) #####")
        [void]$sb.AppendLine("Clicar: $(Clicar $par[0])"); Start-Sleep -Milliseconds 800
        $c = New-Object System.Windows.Automation.PropertyCondition($AE::ClassNameProperty, 'Popup')
        foreach ($p in (Obter-Janela).FindAll($Escopo::Descendants, $c)) { Despejar-Raw $p 0 $sb }
        try { (Obter-Janela).SetFocus() } catch {}
        [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep -Milliseconds 600
    }
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### apos ligar bitFlip #####')
    [void]$sb.AppendLine("Clicar: $(Clicar 'bitFlip')"); Start-Sleep -Milliseconds 800
    Despejar-Raw (Nucleo) 0 $sb
    [void]$sb.AppendLine("Clicar fullKeypad: $(Clicar 'fullKeypad')"); Start-Sleep -Milliseconds 500
    [void]$sb.AppendLine(''); [void]$sb.AppendLine('##### botao de tamanho: 4 cliques (visor em 0) #####')
    for ($k = 0; $k -lt 4; $k++) {
        $vis = @('qwordButton', 'dwordButton', 'wordButton', 'byteButton' | Where-Object { Visivel $_ })
        [void]$sb.AppendLine("antes do clique $($k+1): visiveis=$($vis -join ',')")
        if ($vis.Count) { [void](Clicar $vis[0]); Start-Sleep -Milliseconds 500 }
    }
    $vis = @('qwordButton', 'dwordButton', 'wordButton', 'byteButton' | Where-Object { Visivel $_ })
    [void]$sb.AppendLine("final: visiveis=$($vis -join ',')")
    [void]$sb.AppendLine("visor no fim: '$(Visor-Visivel)'")
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'arvore-uia-3d.txt'), $sb.ToString(), $Utf8)
    Write-Output "arvore gravada: $(Join-Path $DirScript 'arvore-uia-3d.txt')"
    exit 0
}

# AutomationIds: arvore-uia-3d.txt (Etapa Arvore3d, depois do congelamento do 03d)
$Bases3d = @{ 'HEX' = 'hexButton'; 'DEC' = 'decimalButton'; 'OCT' = 'octolButton'; 'BIN' = 'binaryButton' }
$Tams3d = @('QWORD', 'DWORD', 'WORD', 'BYTE')
$TamId3d = @{ 'QWORD' = 'qwordButton'; 'DWORD' = 'dwordButton'; 'WORD' = 'wordButton'; 'BYTE' = 'byteButton' }
$Desl3d = @{ 'Arit' = 'arithmeticShiftButton'; 'Log' = 'logicalShiftButton'; 'Circ' = 'rotateCircularButton'; 'Carry' = 'rotateCarryShiftButton' }
$Bitwise3d = @{ 'AND' = 'andButton'; 'OR' = 'orButton'; 'XOR' = 'xorButton'; 'NAND' = 'nandButton'; 'NOR' = 'norButton'; 'NOT' = 'notButton' }
# deslocamento: token -> (AutomationId, trecho obrigatorio do Name pt-BR); RolC reaproveita o AutomationId rolButton (XBF)
$Shift3d = @{
    'Arit'  = @{ 'LSH' = @('lshButton', 'esquerda'); 'RSH' = @('rshButton', 'direita') }
    'Log'   = @{ 'LSH' = @('lshLogicalButton', 'esquerda'); 'RSH' = @('rshLogicalButton', 'direita') }
    'Circ'  = @{ 'ROL' = @('rolButton', 'Girar à esquerda'); 'ROR' = @('rorButton', 'Girar à direita') }
    'Carry' = @{ 'ROLC' = @('rolButton', 'com transporte'); 'RORC' = @('rorCarryButton', 'com transporte') }
}
$Teclas3d = @{ 'C' = 'clearButton'; 'NEG' = 'negateButton'; '/' = 'divideButton'; '*' = 'multiplyButton'; '-' = 'minusButton'
    '+' = 'plusButton'; '=' = 'equalButton'; '%' = 'modButton' }
$Notacao3d = @{ 'NEG' = '±'; '/' = '÷'; '*' = '×'; '-' = '−'; 'LSH' = 'Lsh'; 'RSH' = 'Rsh'; 'ROL' = 'Rol'; 'ROR' = 'Ror'; 'ROLC' = 'RolC'; 'RORC' = 'RorC' }
$DeslAtual = ''

function Abrir-Flyout([string]$botao, [string]$sonda) {
    if (Visivel $sonda) { return $null }
    $r = Clicar $botao
    for ($k = 0; $k -lt 20; $k++) { if (Visivel $sonda) { return $r }; Start-Sleep -Milliseconds 150 }
    return "submenu de $botao nao abriu"
}
function Fechar-Flyout([string]$sonda) {
    if (Visivel $sonda) {
        try { (Elem-Raiz $sonda).SetFocus() } catch {}
        [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep -Milliseconds 500
    }
    if (Visivel $sonda) { throw "submenu com $sonda nao fechou" }
}
function Fechar-Flyouts3d { Fechar-Flyout 'andButton'; Fechar-Flyout 'arithmeticShiftButton' }
function Tamanho-Atual { foreach ($t in $Tams3d) { if (Visivel $TamId3d[$t]) { return $t } }; return '?' }
function Ajustar-Tamanho([string]$alvo, [System.Collections.Generic.List[string]]$caminho) {
    for ($k = 0; $k -lt 5; $k++) {
        $t = Tamanho-Atual
        if ($t -eq $alvo) { return $null }
        if ($t -eq '?') { return 'botao de tamanho ausente' }
        [void](Clicar $TamId3d[$t]); Start-Sleep -Milliseconds 300
        if ($caminho -ne $null) { $caminho.Add("$(Tamanho-Atual) visor='$(Visor-Visivel)'") }
    }
    return "tamanho nao chegou a $alvo"
}
function Ajustar-Desl([string]$modo) {
    $r = Abrir-Flyout 'bitShiftButton' 'arithmeticShiftButton'; if ($r) { return $r }
    $r = Clicar $Desl3d[$modo]; Start-Sleep -Milliseconds 400
    Fechar-Flyout 'arithmeticShiftButton'
    foreach ($par in $Shift3d[$modo].Values) {
        $e = Elem-Raiz $par[0]
        if ($e -eq $null -or -not $e.Current.Name.Contains($par[1])) { return "desl. $($modo): botao $($par[0]) com '$($par[1])' nao visivel" }
    }
    $script:DeslAtual = $modo
    return $r
}
function Ler-Linhas {
    $out = @()
    foreach ($b in 'HEX', 'DEC', 'OCT', 'BIN') {
        $e = Elem-Raiz $Bases3d[$b]; $v = '(ausente)'
        if ($e -ne $null) {
            $w = [System.Windows.Automation.TreeWalker]::RawViewWalker
            $f = $w.GetFirstChild($e)
            while ($f -ne $null) { if ($f.Current.AutomationId -eq 'ContentPresenter') { $v = $f.Current.Name; break }; $f = $w.GetNextSibling($f) }
        }
        $out += "$($b.Substring(0,1))='$v'"
    }
    return ($out -join ' ')
}
function Ler-Bits {
    if (-not (Visivel 'Bit0')) { return '' }
    $on = @()
    for ($n = 0; $n -lt 64; $n++) { if (Estado-Toggle "Bit$n") { $on += $n } }
    return "{$($on -join ', ')}"
}
function Base-Atual { foreach ($b in $Bases3d.Keys) { $e = Elem-Raiz $Bases3d[$b]; try { if ($e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) { return $b } } catch {} }; return '?' }

function Pressionar3d([string]$tok) {
    if ($tok -like 'R:*') { return (Clicar $Bases3d[$tok.Substring(2)]) }
    if ($tok -like 'W:*') { return (Ajustar-Tamanho $tok.Substring(2) $script:Caminho) }
    if ($tok -eq 'KB:BITS') { return (Clicar 'bitFlip') }
    if ($tok -eq 'KB:FULL') { return (Clicar 'fullKeypad') }
    if ($tok -like 'BIT*') { $e = Elem-Raiz "Bit$($tok.Substring(3))"; if ($e -eq $null) { return "$tok ausente" }; (Padrao-Toggle $e).Toggle(); Start-Sleep -Milliseconds $PausaMs; return $null }
    if ($Bitwise3d.ContainsKey($tok)) {
        $r = Abrir-Flyout 'bitwiseButton' 'andButton'; if ($r) { return $r }
        $r = Clicar $Bitwise3d[$tok]; Start-Sleep -Milliseconds 300
        Fechar-Flyout 'andButton'
        return $r
    }
    if ($DeslAtual -and $Shift3d[$DeslAtual].ContainsKey($tok)) {
        $par = $Shift3d[$DeslAtual][$tok]; $e = Elem-Raiz $par[0]
        if ($e -eq $null -or -not $e.Current.Name.Contains($par[1])) { return "$tok ($($par[0])) ausente" }
        return (Clicar $par[0])
    }
    if ($tok -eq 'C' -and -not (Visivel 'clearButton')) {
        # C e CE dividem a posicao; com CE visivel, CE primeiro (execucao 1 do 3d-93 nao achou o C)
        $r = Clicar 'clearEntryButton'; if ($r) { return $r }
        Start-Sleep -Milliseconds 300
    }
    if ($tok -match '^D:[0-9]$') { return (Clicar "num$($tok.Substring(2))Button") }
    if ($tok -match '^D:[A-F]$') { return (Clicar "$($tok.Substring(2).ToLower())Button") }
    return (Clicar $Teclas3d[$tok])
}

function Preparar3d($caso) {
    $log = @()
    Garantir-Programador
    Fechar-Flyouts3d
    if (-not (Visivel 'clearButton')) { [void](Clicar 'fullKeypad'); $log += 'teclado completo' }
    for ($k = 0; $k -lt 4; $k++) {
        foreach ($id in 'clearEntryButton', 'clearButton') { if (Visivel $id) { [void](Clicar $id); Start-Sleep -Milliseconds 300 } }
        if ((Visivel 'clearButton') -and (Visor-Visivel) -eq '0') { break }
    }
    $r = Clicar $Bases3d[$caso.Base]; if ($r) { throw $r }
    $r = Ajustar-Tamanho $caso.Tam $null; if ($r) { throw $r }
    $script:DeslAtual = ''
    if ($caso.Desl) { $r = Ajustar-Desl $caso.Desl; if ($r) { throw $r } }
    $log += "base $(Base-Atual) tamanho $(Tamanho-Atual)" + $(if ($caso.Desl) { " desl $($caso.Desl)" } else { '' })
    if ((Visor-Visivel) -ne '0') { throw "estado inicial: visor '$(Visor-Visivel)'" }
    return ($log -join '; ')
}

if ($Etapa -eq 'Casos3d') {
    $Seta3 = [char]0x2192
    # Passos: '#<digitos>' = um botao por caractere; R:<base>; W:<tamanho> (cliques ate chegar); KB:BITS/KB:FULL; BITn; '>' = leitura
    $Casos3d = @(
        @{ Id = '3d-01'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#255' }
        @{ Id = '3d-02'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#1000' }
        @{ Id = '3d-03'; Base = 'HEX'; Tam = 'QWORD'; Passos = '#1A3' }
        @{ Id = '3d-04'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#255 > R:HEX > R:OCT > R:BIN > R:DEC' }
        @{ Id = '3d-05'; Base = 'HEX'; Tam = 'QWORD'; Passos = '#123456789ABCDEF01' }
        @{ Id = '3d-06'; Base = 'OCT'; Tam = 'QWORD'; Passos = '#1777777777777777777777' }
        @{ Id = '3d-07'; Base = 'OCT'; Tam = 'QWORD'; Passos = '#2777777777777777777777' }
        @{ Id = '3d-08'; Base = 'BIN'; Tam = 'QWORD'; Passos = '#1' + ('0' * 64) }
        @{ Id = '3d-09'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#9223372036854775808' }
        @{ Id = '3d-10'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#922337203685477580 NEG > #8' }
        @{ Id = '3d-11'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#9223372036854775807' }
        @{ Id = '3d-12'; Base = 'DEC'; Tam = 'BYTE'; Passos = '#128' }
        @{ Id = '3d-13'; Base = 'DEC'; Tam = 'BYTE'; Passos = '#200' }
        @{ Id = '3d-14'; Base = 'HEX'; Tam = 'WORD'; Passos = '#12345' }
        @{ Id = '3d-20'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#300 > W:BYTE' }
        @{ Id = '3d-21'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#200 > W:BYTE > W:QWORD' }
        @{ Id = '3d-22'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#65535 > W:WORD > W:QWORD' }
        @{ Id = '3d-23'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#2147483648 > W:DWORD' }
        @{ Id = '3d-24'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#4294967296 > W:DWORD' }
        @{ Id = '3d-25'; Base = 'DEC'; Tam = 'DWORD'; Passos = '#1 NEG > W:QWORD' }
        @{ Id = '3d-26'; Base = 'HEX'; Tam = 'QWORD'; Passos = '#FFFFFFFFFF > W:DWORD' }
        @{ Id = '3d-30'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#1 NEG' }
        @{ Id = '3d-31'; Base = 'HEX'; Tam = 'QWORD'; Passos = '#1 NEG' }
        @{ Id = '3d-32'; Base = 'HEX'; Tam = 'BYTE'; Passos = '#80' }
        @{ Id = '3d-33'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#9223372036854775807 + #1 =' }
        @{ Id = '3d-34'; Base = 'DEC'; Tam = 'DWORD'; Passos = '#2147483647 + #1 =' }
        @{ Id = '3d-35'; Base = 'DEC'; Tam = 'WORD'; Passos = '#32767 + #1 =' }
        @{ Id = '3d-36'; Base = 'DEC'; Tam = 'BYTE'; Passos = '#127 + #1 =' }
        @{ Id = '3d-37'; Base = 'DEC'; Tam = 'BYTE'; Passos = '#100 * #3 =' }
        @{ Id = '3d-38'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#4294967296 * #4294967296 =' }
        @{ Id = '3d-39'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#4294967295 * #4294967295 =' }
        @{ Id = '3d-40'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#7 / #2 =' }
        @{ Id = '3d-41'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#7 NEG / #2 =' }
        @{ Id = '3d-42'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#7 NEG % #3 =' }
        @{ Id = '3d-43'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#7 % #3 NEG =' }
        @{ Id = '3d-44'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 % #0 =' }
        @{ Id = '3d-45'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 / #0 =' }
        @{ Id = '3d-46'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#0 / #0 =' }
        @{ Id = '3d-47'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 / #0 = > R:HEX' }
        @{ Id = '3d-48'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#1 - #2 =' }
        @{ Id = '3d-50'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 AND #10 =' }
        @{ Id = '3d-51'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 OR #10 =' }
        @{ Id = '3d-52'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 XOR #10 =' }
        @{ Id = '3d-53'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 NAND #10 =' }
        @{ Id = '3d-54'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 NOR #10 =' }
        @{ Id = '3d-55'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 NOT' }
        @{ Id = '3d-56'; Base = 'DEC'; Tam = 'BYTE'; Passos = '#5 NOT' }
        @{ Id = '3d-57'; Base = 'HEX'; Tam = 'BYTE'; Passos = '#F0 NOT' }
        @{ Id = '3d-58'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#6 OR #1 AND #2 =' }
        @{ Id = '3d-59'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 XOR #10 AND #6 =' }
        @{ Id = '3d-60'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#1 OR #5 NAND #3 =' }
        @{ Id = '3d-61'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 + NOT > =' }
        @{ Id = '3d-62'; Base = 'HEX'; Tam = 'QWORD'; Passos = '#F AND #3 =' }
        @{ Id = '3d-70'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#1 LSH #4 =' }
        @{ Id = '3d-71'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#1 LSH #63 =' }
        @{ Id = '3d-72'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#1 LSH #64 =' }
        @{ Id = '3d-73'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#7 NEG RSH #1 =' }
        @{ Id = '3d-74'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#16 NEG RSH #2 =' }
        @{ Id = '3d-75'; Base = 'DEC'; Tam = 'BYTE'; Desl = 'Arit'; Passos = '#3 LSH #7 =' }
        @{ Id = '3d-76'; Base = 'DEC'; Tam = 'BYTE'; Desl = 'Arit'; Passos = '#1 LSH #8 =' }
        @{ Id = '3d-77'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Arit'; Passos = '#80 RSH #1 =' }
        @{ Id = '3d-78'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#8 RSH #64 =' }
        @{ Id = '3d-79'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#1 + #1 LSH #2 =' }
        @{ Id = '3d-80'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Arit'; Passos = '#8 LSH #1 NEG =' }
        @{ Id = '3d-81'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Log'; Passos = '#1 NEG RSH #1 =' }
        @{ Id = '3d-82'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Log'; Passos = '#16 NEG RSH #60 =' }
        @{ Id = '3d-83'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Log'; Passos = '#80 RSH #1 =' }
        @{ Id = '3d-84'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Log'; Passos = '#1 LSH #63 =' }
        @{ Id = '3d-85'; Base = 'DEC'; Tam = 'BYTE'; Desl = 'Log'; Passos = '#5 RSH #8 =' }
        @{ Id = '3d-86'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Circ'; Passos = '#81 ROL > ROR' }
        @{ Id = '3d-87'; Base = 'DEC'; Tam = 'QWORD'; Desl = 'Circ'; Passos = '#1 ROR' }
        @{ Id = '3d-88'; Base = 'DEC'; Tam = 'BYTE'; Desl = 'Circ'; Passos = '#1 ROR' }
        @{ Id = '3d-89'; Base = 'HEX'; Tam = 'QWORD'; Desl = 'Circ'; Passos = '#8000000000000000 ROL' }
        @{ Id = '3d-90'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Carry'; Passos = '#80 ROLC > ROLC > ROLC' }
        @{ Id = '3d-91'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Carry'; Passos = '#1 RORC > RORC > RORC' }
        @{ Id = '3d-92'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Carry'; Passos = '#80 ROLC > #5 ROLC' }
        @{ Id = '3d-93'; Base = 'HEX'; Tam = 'BYTE'; Desl = 'Carry'; Passos = '#80 ROLC > C #5 ROLC' }
        @{ Id = '3d-100'; Base = 'DEC'; Tam = 'QWORD'; Passos = 'KB:BITS BIT0 > BIT3' }
        @{ Id = '3d-101'; Base = 'DEC'; Tam = 'QWORD'; Passos = 'KB:BITS BIT63' }
        @{ Id = '3d-102'; Base = 'DEC'; Tam = 'BYTE'; Passos = 'KB:BITS BIT7' }
        @{ Id = '3d-103'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 KB:BITS > BIT2' }
        @{ Id = '3d-104'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#5 + KB:BITS BIT0 > KB:FULL =' }
        @{ Id = '3d-105'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#12 KB:BITS BIT0 > KB:FULL #4' }
        @{ Id = '3d-106'; Base = 'DEC'; Tam = 'QWORD'; Passos = '#1 NEG KB:BITS BIT63' }
        @{ Id = '3d-107'; Base = 'HEX'; Tam = 'QWORD'; Passos = 'KB:BITS BIT4 BIT0' }
    )
    if ($env:CASOS3D) { $Casos3d = @($Casos3d | Where-Object { ($env:CASOS3D -split ',') -contains $_.Id }) }
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    $Linhas = New-Object System.Collections.Generic.List[string]
    L "# Execucao 3d $(Get-Date -Format s) - Calculadora $($pkg.Version) $($pkg.Architecture), cultura $((Get-Culture).Name), UI $((Get-UICulture).Name)"
    foreach ($arq in 'CalculatorApp.exe', 'CalculatorApp.dll', 'CalcViewModel.dll') {
        try { L "# SHA-256 instalado $arq = $((Get-FileHash -Algorithm SHA256 (Join-Path $pkg.InstallLocation $arq)).Hash.ToLower())" }
        catch { L "# SHA-256 instalado $arq = (sem acesso: $($_.Exception.Message))" }
    }
    $Linhas.Add("# Calculadora $($pkg.Version) $($pkg.Architecture); cultura $((Get-Culture).Name); UI $((Get-UICulture).Name); $(Get-Date -Format s)")
    $Linhas.Add("# Formato: ID [$($Seta3)n apos X]: visor | expressao(OCR) | linhas | bits -- obs; visor = NormalOutput; linhas = ContentPresenter de hex/decimal/octol/binaryButton; bits = Bit0..63 ligados")
    foreach ($caso in $Casos3d) {
        L ''; L "== $($caso.Id) ($($caso.Base), $($caso.Tam)$(if ($caso.Desl) { ', ' + $caso.Desl })): $($caso.Passos) [$(Get-Date -Format HH:mm:ss)]"
        L "   preparo: $(Preparar3d $caso)"
        $obs = New-Object System.Collections.Generic.List[string]
        $script:Caminho = New-Object System.Collections.Generic.List[string]
        $nLeitura = 0; $ultima = ''
        $toks = @($caso.Passos -split ' ' | Where-Object { $_ -ne '' }) + @('>FIM')
        foreach ($tok in $toks) {
            if ($tok -eq '>' -or $tok -eq '>FIM') {
                $r = Ler-Estavel
                $visor = Visor-Visivel
                $nomeCap = if ($tok -eq '>') { "$($caso.Id)-$($nLeitura + 1)" } else { "$($caso.Id)-final" }
                $expr = Capturar $nomeCap
                if ([string]::IsNullOrEmpty($expr)) { $expr = '(vazia)' }
                $lin = Ler-Linhas; $bits = Ler-Bits
                L "   leitura apos [$ultima]: NormalOutput='$visor' expressao.Name='$($r[1])' OCR='$expr' $lin bits=$bits base=$(Base-Atual) tamanho=$(Tamanho-Atual) captura=capturas/$nomeCap.png"
                if ($script:Caminho.Count) { L "   caminho do tamanho: $($script:Caminho -join ' -> ')"; $script:Caminho.Clear() }
                $sufixo = if ($obs.Count) { ' -- ' + ($obs -join '; ') } else { '' }
                $obs.Clear()
                $corpo = "$visor | $expr | $lin | bits=$bits$sufixo"
                if ($tok -eq '>') { $nLeitura++; $Linhas.Add("$($caso.Id) $Seta3$nLeitura [apos $ultima]: $corpo") }
                else { $Linhas.Add("$($caso.Id): $corpo") }
                continue
            }
            $seq = if ($tok -like '#*') { $tok.Substring(1).ToCharArray() | ForEach-Object { "D:$_" } } else { @($tok) }
            foreach ($t in $seq) {
                $p = Pressionar3d $t
                if ($p) { $obs.Add($p); L "   $p" }
                $ultima = $Notacao3d[$t]; if (-not $ultima) { $ultima = ($t -replace '^D:', '') }
            }
        }
    }
    Preparar3d @{ Base = 'DEC'; Tam = 'QWORD' } | Out-Null
    $saida = Join-Path $DirProjeto 'relatorio\resultados-reais-3d.txt'
    [System.IO.File]::WriteAllText($saida, ($Linhas -join "`n") + "`n", $Utf8)
    [System.IO.File]::WriteAllText((Join-Path $DirScript 'log-execucao-3d.txt'), $Log.ToString(), $Utf8)
    Write-Output "resultados gravados: $saida"
    exit 0
}

# ---------------------------------------------------------------- Teste diferencial (03-diferencial-casos.json)
# Le so o visor final (NormalOutput, RawView) e o estado de erro (plusButton.IsEnabled; operadores desabilitados em
# erro, L19) pelo UIA. Sem capturas, sem OCR, sem transcricao.
# AutomationIds novos: xpower3Button, cubeRootButton, twoPowerXButton, hypShiftButton, sinh/cosh/tanhButton,
# floorButton, ceilButton = x:Name de trabalho/pri/xbf-strings/Views/CalculatorScientificOperators.txt.
$Teclas3c['SQR'] = 'xpower2Button'; $Teclas3c['SQRT'] = 'squareRootButton'; $Teclas3c['INV'] = 'invertButton'
$Teclas3c['BS'] = 'backSpaceButton'; $Teclas3c['MS'] = 'memButton'; $Teclas3c['MR'] = 'MemRecall'
$Teclas3c['M+'] = 'MemPlus'; $Teclas3c['M-'] = 'MemMinus'; $Teclas3c['MC'] = 'ClearMemoryButton'
$Shift3c['CUBE'] = 'xpower3Button'; $Shift3c['CBRT'] = 'cubeRootButton'; $Shift3c['2^X'] = 'twoPowerXButton'
$TrigDif = @{ 'SIN' = @('sinButton', $false, $false); 'COS' = @('cosButton', $false, $false); 'TAN' = @('tanButton', $false, $false)
    'ASIN' = @('invsinButton', $true, $false); 'ACOS' = @('invcosButton', $true, $false); 'ATAN' = @('invtanButton', $true, $false)
    'SINH' = @('sinhButton', $false, $true); 'COSH' = @('coshButton', $false, $true); 'TANH' = @('tanhButton', $false, $true) }
$FuncDif = @{ 'FLOOR' = 'floorButton'; 'CEIL' = 'ceilButton' }
$Teclas3d['BS'] = 'backSpaceButton'; $Teclas3d['('] = 'openParenthesisButton'; $Teclas3d[')'] = 'closeParenthesisButton'
$SondasTrig = @('sinButton', 'invsinButton', 'sinhButton', 'invsinhButton')

function Trig-Aberto { foreach ($s in $SondasTrig) { if (Visivel $s) { return $true } }; return $false }
function Fechar-TrigDif {
    foreach ($s in $SondasTrig) {
        if (Visivel $s) {
            try { (Elem-Raiz $s).SetFocus() } catch {}
            [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep -Milliseconds 500
            break
        }
    }
    if (Trig-Aberto) { throw 'submenu Trigonometria nao fechou' }
}
function Pressionar-TrigDif([string]$tok) {
    $id, $inv, $hyp = $TrigDif[$tok]
    if (-not (Trig-Aberto)) {
        $r = Clicar 'trigButton'; if ($r) { return $r }
        for ($k = 0; $k -lt 20 -and -not (Trig-Aberto); $k++) { Start-Sleep -Milliseconds 150 }
        if (-not (Trig-Aberto)) { return 'submenu Trigonometria nao abriu' }
    }
    $r = Ajustar-Toggle 'trigShiftButton' $inv; if ($r) { return $r }
    $r = Ajustar-Toggle 'hypShiftButton' $hyp; if ($r) { return $r }
    $r = Clicar $id
    Start-Sleep -Milliseconds 300
    if (Trig-Aberto) {
        # nao fechou sozinho (botao desabilitado?): desliga 2nd/hyp e fecha com Esc
        [void](Ajustar-Toggle 'trigShiftButton' $false); [void](Ajustar-Toggle 'hypShiftButton' $false)
        Fechar-TrigDif
    }
    return $r
}
function Pressionar-Ci([string]$tok) {
    if ($TrigDif.ContainsKey($tok)) { return (Pressionar-TrigDif $tok) }
    if ($FuncDif.ContainsKey($tok)) {
        $r = Abrir-Flyout 'funcButton' 'floorButton'; if ($r) { return $r }
        $r = Clicar $FuncDif[$tok]; Start-Sleep -Milliseconds 300
        Fechar-Flyout 'floorButton'
        return $r
    }
    if ($Shift3c.ContainsKey($tok) -or $tok -eq 'FE') {
        $id = if ($tok -eq 'FE') { 'ftoeButton' } else { 'shiftButton' }
        $e = Elem-Raiz $id
        if ($e -eq $null) { return "$id ausente" }
        if (-not $e.Current.IsEnabled) { return "tecla $tok ($id) desabilitada, nao pressionada" }
    }
    if ($tok -eq 'C' -and -not (Visivel 'clearButton')) {
        # C e CE dividem a posicao no Cientifico: CE e depois C equivale a C
        $r = Clicar 'clearEntryButton'; if ($r) { return $r }
        Start-Sleep -Milliseconds 300
    }
    return (Pressionar3c $tok)
}
function Limpar-Memoria {
    $mc = Elem 'ClearMemoryButton'
    if ($mc -ne $null -and $mc.Current.IsEnabled) { Invocar $mc; Start-Sleep -Milliseconds 300; return 'MC' }
    return ''
}
# Fecha a janela e relanca a Calculadora (zera o estado dos motores; usado quando a verificacao do preparo falha)
function Reiniciar-Calculadora {
    $j = Obter-Janela
    try { $j.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() }
    catch { Stop-Process -Name CalculatorApp -Force -ErrorAction SilentlyContinue }
    for ($k = 0; $k -lt 40; $k++) {
        $ainda = $false
        foreach ($w in $Raiz.FindAll($Escopo::Children, [System.Windows.Automation.Condition]::TrueCondition)) {
            if ($w.Current.Name -match '^(Calculadora|Calculator)$') { $ainda = $true }
        }
        if (-not $ainda) { break }
        Start-Sleep -Milliseconds 250
    }
    if ($ainda) { Stop-Process -Name CalculatorApp -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 1000 }
    Start-Sleep -Milliseconds 800
    [void](Obter-Janela)
    Start-Sleep -Milliseconds 1500
}
# Verificacao pelo UIA antes de cada caso (segunda passada em diante). Devolve a lista de problemas (vazia = ok).
# F-E: o toggle sozinho nao basta (C desliga so a propriedade da VM, L25; F-E em erro marca o botao sem chegar ao
# motor, dif-Ci-061): com o motor em F-E o visor zerado e '0,e+0', entao exige toggle desligado E visor exatamente '0'.
function Verificar-Preparo($caso) {
    $p = $caso.preparo; $prob = @()
    $modo = Modo-Atual
    $alvo = @{ 'padrao' = '*Padrão'; 'cientifico' = '*Científica'; 'programador' = '*Programador' }[$caso.modo]
    if (-not ($modo -like $alvo)) { $prob += "modo '$modo'" }
    $v = Visor-Visivel
    if ($v -ne '0') { $prob += "visor '$v'" }
    if ($caso.modo -eq 'cientifico') {
        $fe = Estado-Toggle 'ftoeButton'
        if ($fe -ne $false) { $prob += "F-E toggle=$fe" }
        $a = Angulo-Atual
        if ($a -ne $p.angulo) { $prob += "angulo $a (esperado $($p.angulo))" }
        if (Estado-Toggle 'shiftButton') { $prob += '2nd ligado' }
    }
    if ($caso.modo -eq 'programador') {
        if ((Base-Atual) -ne $p.base) { $prob += "base $(Base-Atual)" }
        if ((Tamanho-Atual) -ne $p.tamanho) { $prob += "tamanho $(Tamanho-Atual)" }
    }
    return $prob
}
function Preparar-Uma($caso) {
    $p = $caso.preparo
    switch ($caso.modo) {
        'padrao' {
            Garantir-Modo '1'
            $m = Limpar-Memoria
            [void](Pressionar 'C'); Start-Sleep -Milliseconds 300
            if ((Visor-Visivel) -ne '0') { throw "estado inicial: visor '$(Visor-Visivel)'" }
            return "Padrao $m"
        }
        'cientifico' {
            Garantir-Modo '2'
            if (Trig-Aberto) { [void](Ajustar-Toggle 'trigShiftButton' $false); [void](Ajustar-Toggle 'hypShiftButton' $false); Fechar-TrigDif }
            if (Visivel 'floorButton') { Fechar-Flyout 'floorButton' }
            $m = Limpar-Memoria
            return "$(Preparar3c $p.angulo) $m"
        }
        'programador' { return (Preparar3d @{ Base = $p.base; Tam = $p.tamanho; Desl = $p.deslocamento }) }
    }
    throw "modo desconhecido: $($caso.modo)"
}
function Preparar-Dif($caso) {
    if (-not $VerificarPreparo) { return (Preparar-Uma $caso) }
    $log = @()
    for ($tent = 0; $tent -lt 2; $tent++) {
        try { Focar (Obter-Janela) } catch {}   # janela minimizada fica sem CoreWindow na arvore UIA
        try { $log += (Preparar-Uma $caso) } catch { $log += "preparo: $($_.Exception.Message)" }
        try { $prob = @(Verificar-Preparo $caso) } catch { $prob = @("verificacao: $($_.Exception.Message)") }
        if ($prob.Count -eq 0) { $log += 'verificado (modo, visor 0' + $(if ($caso.modo -eq 'cientifico') { ', F-E desligado, angulo' } else { '' }) + ')'; return ($log -join '; ') }
        $log += "verificacao falhou: $($prob -join ', ')"
        if ($tent -eq 0) { $log += 'Calculadora reiniciada'; Reiniciar-Calculadora }
    }
    throw "preparo invalido: $($log -join '; ')"
}
function Pressionar-Dif([string]$modo, [string]$tok) {
    switch ($modo) {
        'padrao' { return (Pressionar $tok) }
        'cientifico' { return (Pressionar-Ci $tok) }
        'programador' {
            if ($tok -eq 'TAM') { $t = Tamanho-Atual; if ($t -eq '?') { return 'botao de tamanho ausente' }; return (Clicar $TamId3d[$t]) }
            if ($tok -like '#*') { $tok = 'D:' + $tok.Substring(1) }
            return (Pressionar3d $tok)
        }
    }
}

if ($Etapa -eq 'Diferencial') {
    # DIFCASOS / DIFSAIDA: nomes de arquivo em relatorio\ (padrao: o diferencial 1); DIFVERIFICAR=1 liga a verificacao
    # do preparo (segunda passada do diferencial 1 em diante); DIF=id1,id2 filtra
    $arqCasos = Join-Path $DirProjeto ('relatorio\' + $(if ($env:DIFCASOS) { $env:DIFCASOS } else { '03-diferencial-casos.json' }))
    $doc = [System.IO.File]::ReadAllText($arqCasos, $Utf8) | ConvertFrom-Json
    $CasosDif = @($doc.casos)
    if ($env:DIF) { $CasosDif = @($CasosDif | Where-Object { ($env:DIF -split ',') -contains $_.id }) }
    $saida = Join-Path $DirProjeto ('relatorio\' + $(if ($env:DIFSAIDA) { $env:DIFSAIDA } else { 'resultados-reais-diferencial.jsonl' }))
    $VerificarPreparo = ($env:DIFVERIFICAR -eq '1')
    $pkg = Get-AppxPackage Microsoft.WindowsCalculator
    $cab = "# Calculadora $($pkg.Version) $($pkg.Architecture); cultura $((Get-Culture).Name); UI $((Get-UICulture).Name); " +
        "inicio $(Get-Date -Format o); casos SHA-256 $((Get-FileHash -Algorithm SHA256 $arqCasos).Hash.ToLower()); semente $($doc.semente); $($CasosDif.Count) casos; verificar preparo=$VerificarPreparo"
    [System.IO.File]::AppendAllText($saida, $cab + "`n", $Utf8)
    L $cab
    foreach ($arq in 'CalculatorApp.exe', 'CalculatorApp.dll', 'CalcViewModel.dll') {
        try { L "# SHA-256 instalado $arq = $((Get-FileHash -Algorithm SHA256 (Join-Path $pkg.InstallLocation $arq)).Hash.ToLower())" }
        catch { L "# SHA-256 instalado $arq = (sem acesso: $($_.Exception.Message))" }
    }
    $logArq = if ($env:DIFSAIDA) { Join-Path $DirScript ('log-' + [System.IO.Path]::GetFileNameWithoutExtension($saida) + '.txt') }
              else { Join-Path $DirScript 'log-execucao-diferencial.txt' }
    foreach ($caso in $CasosDif) {
        $ini = Get-Date -Format o
        $notas = New-Object System.Collections.Generic.List[string]
        $falha = $null; $visor = $null; $mais = $null
        try {
            L ''; L "== $($caso.id) ($($caso.modo) $(($caso.preparo | ConvertTo-Json -Compress))): $($caso.passos -join ' ') [$ini]"
            L "   preparo: $(Preparar-Dif $caso)"
            foreach ($tok in $caso.passos) {
                try {
                    $p = Pressionar-Dif $caso.modo $tok
                    if ($p) { $notas.Add("${tok}: $p"); L "   ${tok}: $p" }
                } catch { $notas.Add("${tok}: excecao $($_.Exception.Message)"); L "   ${tok}: excecao $($_.Exception.Message)" }
            }
            [void](Ler-Estavel)
            $visor = Visor-Visivel
            $e = Elem 'plusButton'
            $mais = if ($e -eq $null) { $null } else { [bool]$e.Current.IsEnabled }
            L "   leitura: NormalOutput='$visor' plusButton.IsEnabled=$mais"
        } catch { $falha = $_.Exception.Message; L "   FALHA: $falha" }
        $obj = [ordered]@{ id = $caso.id; visor = $visor; mais_habilitado = $mais; notas = @($notas); falha = $falha
            inicio = $ini; fim = (Get-Date -Format o) }
        [System.IO.File]::AppendAllText($saida, ((New-Object PSObject -Property $obj) | ConvertTo-Json -Compress) + "`n", $Utf8)
        [System.IO.File]::WriteAllText($logArq, $Log.ToString(), $Utf8)
    }
    try { Preparar3d @{ Base = 'DEC'; Tam = 'QWORD' } | Out-Null; Garantir-Modo '1' } catch {}
    L "# fim $(Get-Date -Format o)"
    [System.IO.File]::WriteAllText($logArq, $Log.ToString(), $Utf8)
    Write-Output "resultados gravados: $saida"
    exit 0
}

$Seta = [char]0x2192
$Linhas = New-Object System.Collections.Generic.List[string]
$pkg = Get-AppxPackage Microsoft.WindowsCalculator
L "# Execucao $(Get-Date -Format s) - Calculadora $($pkg.Version) $($pkg.Architecture), cultura $((Get-Culture).Name), UI $((Get-UICulture).Name)"
foreach ($arq in 'CalculatorApp.exe', 'CalculatorApp.dll', 'CalcViewModel.dll') {
    try { L "# SHA-256 instalado $arq = $((Get-FileHash -Algorithm SHA256 (Join-Path $pkg.InstallLocation $arq)).Hash.ToLower())" }
    catch { L "# SHA-256 instalado $arq = (sem acesso: $($_.Exception.Message))" }
}

Garantir-Modo '1'
[void](Pressionar 'C'); Start-Sleep -Milliseconds 300
$Linhas.Add("# Calculadora $($pkg.Version) $($pkg.Architecture); cultura $((Get-Culture).Name); UI $((Get-UICulture).Name); $(Get-Date -Format s)")
$Linhas.Add("# Formato: ID: visor | expressao -- observacoes. 'ID $($Seta)n [apos X]' = leitura intermediaria n.")
$Linhas.Add("# visor = texto de NormalOutput (UIA RawView); expressao = OCR da captura (trabalho/automacao/capturas/<ID>-<n|final>.png)")
$Linhas.Add("BASE (Padrao, apos C): $(Estado-Botoes)")

foreach ($caso in $Casos) {
    Garantir-Modo $caso.Modo
    L ''; L "== $($caso.Id) (modo Alt+$($caso.Modo)): $($caso.Passos)"
    $obs = New-Object System.Collections.Generic.List[string]
    $nLeitura = 0; $ultima = ''
    $toks = @($caso.Passos -split ' ' | Where-Object { $_ -ne '' }) + @('>FIM')
    foreach ($tok in $toks) {
        if ($tok -eq '>' -or $tok -eq '>FIM') {
            $r = Ler-Estavel
            $visor = Visor-Visivel
            $nomeCap = if ($tok -eq '>') { "$($caso.Id)-$($nLeitura + 1)" } else { "$($caso.Id)-final" }
            $expr = Capturar $nomeCap
            if ([string]::IsNullOrEmpty($expr)) { $expr = '(vazia)' }
            L "   leitura apos [$ultima]: NormalOutput='$visor' visor.Name='$($r[0])' expressao.Name='$($r[1])' OCR='$expr' captura=capturas/$nomeCap.png"
            $extra = @()
            if ($obs.Count) { $extra += $obs; $obs.Clear() }
            if (Eh-Erro $visor) { $extra += "em erro, $(Estado-Botoes)" }
            $sufixo = if ($extra.Count) { ' -- ' + ($extra -join '; ') } else { '' }
            if ($tok -eq '>') {
                $nLeitura++
                $Linhas.Add("$($caso.Id) $Seta$nLeitura [apos $ultima]: $visor | $expr$sufixo")
            } else {
                $Linhas.Add("$($caso.Id): $visor | $expr$sufixo")
            }
            continue
        }
        $seq = if ($tok -match '^[0-9]{2,}$') { $tok.ToCharArray() | ForEach-Object { "$_" } } else { @($tok) }
        foreach ($t in $seq) {
            $p = Pressionar $t
            if ($p) { $obs.Add($p); L "   $p" }
            $ultima = $Notacao[$t]; if (-not $ultima) { $ultima = $t }
        }
    }
}
Garantir-Modo '1'

$saida = Join-Path $DirProjeto 'relatorio\resultados-reais.txt'
[System.IO.File]::WriteAllText($saida, ($Linhas -join "`n") + "`n", $Utf8)
[System.IO.File]::WriteAllText((Join-Path $DirScript 'log-execucao.txt'), $Log.ToString(), $Utf8)
Write-Output "resultados gravados: $saida"
