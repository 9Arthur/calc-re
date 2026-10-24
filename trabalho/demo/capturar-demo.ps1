# capturar-demo.ps1 - quadros da demonstracao do README (caixa-preta: SendKeys/UI Automation e captura de tela).
# Uso (do WSL):
#   powershell.exe -ExecutionPolicy Bypass -File "$(wslpath -w trabalho/demo/capturar-demo.ps1)" `
#       -Janela Calculadora -Roteiro <roteiro.tsv> -Saida <pasta> -X 300
# -Janela: titulo exato da janela (Calculadora = a original; "Calculadora (reimpl)" = a GUI da reimplementacao).
# Roteiro: uma linha por quadro, "acoes<TAB>legenda<TAB>ms"; acoes separadas por ';':
#   tecla:<SendKeys> | clica:<x>,<y> (relativo ao canto visivel) | espera:<ms> | seleciona:<AutomationId> | invoca:<AutomationId>
#   | alterna:<AutomationId> (ToggleButton) ('-' = nenhuma acao). seleciona/invoca/alterna so funcionam na original (a GUI nao expoe UIA).
# Grava <Saida>\NNN.png (janela inteira, sem a sombra) depois de executar as acoes de cada linha.
# Nao altera nada no sistema: so posiciona a janela, envia entrada e copia a tela.
param(
    [string]$Janela = 'Calculadora',
    [Parameter(Mandatory = $true)][string]$Roteiro,
    [Parameter(Mandatory = $true)][string]$Saida,
    [int]$X = 300, [int]$Y = 100, [int]$Largura = 482, [int]$Altura = 689
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms, System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class D32 {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int hh, uint f);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, IntPtr e);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int a, out RECT r, int s);
}
'@
[void][D32]::SetProcessDPIAware()
$AE = [System.Windows.Automation.AutomationElement]
$Esc = [System.Windows.Automation.TreeScope]
New-Item -ItemType Directory -Force -Path $Saida | Out-Null

function Achar-Janela {
    for ($i = 0; $i -lt 60; $i++) {
        foreach ($j in $AE::RootElement.FindAll($Esc::Children, [System.Windows.Automation.Condition]::TrueCondition)) {
            if ($j.Current.Name -eq $Janela) { return $j }
        }
        if ($i -eq 0 -and $Janela -eq 'Calculadora') { Start-Process 'explorer.exe' 'shell:AppsFolder\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App' }
        Start-Sleep -Milliseconds 500
    }
    throw "Janela '$Janela' nao encontrada"
}
function Moldura($h) {
    $r = New-Object D32+RECT
    [void][D32]::DwmGetWindowAttribute($h, 9, [ref]$r, 16)   # DWMWA_EXTENDED_FRAME_BOUNDS
    return $r
}
function Mover-Para([int]$x, [int]$y) {
    # SetCursorPos sozinho nao gera evento de ponteiro na CoreWindow: termina com movimentos relativos reais
    [void][D32]::SetCursorPos($x - 4, $y - 4); Start-Sleep -Milliseconds 60
    for ($i = 0; $i -lt 4; $i++) { [D32]::mouse_event(1, 1, 1, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 40 }
}
function Elem([string]$id) {
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::AutomationIdProperty, $id)
    $e = $j.FindFirst($Esc::Descendants, $c)
    if ($e -eq $null) { throw "elemento $id nao encontrado" }
    return $e
}

$j = Achar-Janela
$h = [IntPtr]$j.Current.NativeWindowHandle
[void][D32]::ShowWindow($h, 9)
# tamanho visivel exato (DWM extended frame bounds): compensa a borda invisivel de redimensionamento
[void][D32]::SetWindowPos($h, [IntPtr]::Zero, $X, $Y, $Largura, $Altura, 0x0004)
Start-Sleep -Milliseconds 300
$wr = New-Object D32+RECT; [void][D32]::GetWindowRect($h, [ref]$wr); $fb = Moldura $h
$dl = ($fb.L - $wr.L); $dt = ($fb.T - $wr.T); $dw = ($wr.R - $wr.L) - ($fb.R - $fb.L); $dh = ($wr.B - $wr.T) - ($fb.B - $fb.T)
[void][D32]::SetWindowPos($h, [IntPtr]::Zero, ($X - $dl), ($Y - $dt), ($Largura + $dw), ($Altura + $dh), 0x0004)
[void][D32]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 700

$n = 0
foreach ($linha in [System.IO.File]::ReadAllLines($Roteiro)) {
    if ($linha -eq '' -or $linha.StartsWith('#')) { continue }
    $acoes = ($linha -split "`t")[0]
    foreach ($a in ($acoes -split ';' | Where-Object { $_ -ne '' -and $_ -ne '-' })) {
        $k, $v = $a -split ':', 2
        switch ($k) {
            'tecla' { [System.Windows.Forms.SendKeys]::SendWait($v); Start-Sleep -Milliseconds 400 }
            'espera' { Start-Sleep -Milliseconds ([int]$v) }
            'clica' { $m = Moldura $h; $p = $v -split ','; Mover-Para ($m.L + [int]$p[0]) ($m.T + [int]$p[1]); Start-Sleep -Milliseconds 150
                      [D32]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 80
                      [D32]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 400 }
            'seleciona' { (Elem $v).GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select(); Start-Sleep -Milliseconds 500 }
            'invoca' { (Elem $v).GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); Start-Sleep -Milliseconds 500 }
            'alterna' { (Elem $v).GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Toggle(); Start-Sleep -Milliseconds 700 }
            default { throw "acao desconhecida: $a" }
        }
    }
    # ponteiro fora das duas janelas (original em x=300, reimplementacao em x=1000) para nao haver hover
    Mover-Para 1750 950; Start-Sleep -Milliseconds 300
    $m = Moldura $h
    $bmp = New-Object System.Drawing.Bitmap ($m.R - $m.L), ($m.B - $m.T)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($m.L, $m.T, 0, 0, $bmp.Size)
    $bmp.Save((Join-Path $Saida ('{0:D3}.png' -f $n)), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    $n++
}
Write-Output "ok $Janela $n quadros em $Saida"
