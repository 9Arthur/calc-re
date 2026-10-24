#!/bin/bash
# Gera a demonstração visual do README (docs/assets/) a partir de capturas reais das duas calculadoras.
#
#   trabalho/demo/gerar-demo.sh              captura (Windows, via WSL) e monta
#   trabalho/demo/gerar-demo.sh --so-montar  só monta, a partir de quadros/ já capturados
#
# Captura (caixa-preta, como no CLAUDE.md: só entrada de teclado/UI Automation e cópia da tela; nenhuma previsão,
# relatório ou resultado registrado depende disto):
#   - a Calculadora instalada (11.2607.0.0, Windows pt-BR, tema escuro, 96 DPI) em x=300;
#   - a GUI da reimplementação (reimpl/calculadora/gui, fora do repositório público: .gitignore §8) em x=1000,
#     aberta por reimpl/ferramentas/abrir_gui.sh com o Python do Windows.
#   As duas recebem o mesmo roteiro-padrao-cientifico.tsv, uma depois da outra; o quadro N de cada uma é capturado
#   depois da linha N. O Programador só existe na original: o painel da direita é a saída de texto real da CLI.
# Montagem: ImageMagick 6 (convert/compare), já presente no sistema; nada é adicionado ao projeto.
# Os quadros brutos (capturas da original) ficam em quadros/, ignorado pelo git; só o resultado vai para docs/assets.
set -e
D="$(cd "$(dirname "$0")" && pwd)"
R="$(cd "$D/../.." && pwd)"
Q="$D/quadros"
SAIDA="$R/docs/assets"
FONTE=DejaVu-Sans
MONO=DejaVu-Sans-Mono
FUNDO='#161616'
TEXTO='#e6e6e6'

capturar() {   # janela pasta x roteiro
    rm -rf "$Q/$2"
    powershell.exe -ExecutionPolicy Bypass -File "$(wslpath -w "$D/capturar-demo.ps1")" -Janela "$1" \
        -Roteiro "$(wslpath -w "$D/$4")" -Saida "$(wslpath -w "$Q")\\$2" -X "$3" </dev/null | tr -d '\r'
}

if [ "$1" != --so-montar ]; then
    mkdir -p "$Q"
    powershell.exe -NoProfile -Command "Get-Process python,pythonw -ErrorAction SilentlyContinue | Where-Object { \$_.MainWindowTitle -eq 'Calculadora (reimpl)' } | Stop-Process" </dev/null 2>/dev/null || true
    [ -x "$R/reimpl/ferramentas/abrir_gui.sh" ] || { echo "falta reimpl/ferramentas/abrir_gui.sh (GUI fora do repositório público)" >&2; exit 1; }
    nohup "$R/reimpl/ferramentas/abrir_gui.sh" --pos 1000,100 --tamanho 482x689 >"$Q/gui.log" 2>&1 &
    sleep 6
    capturar 'Calculadora' original 300 roteiro-padrao-cientifico.tsv
    capturar 'Calculadora (reimpl)' reimpl 1000 roteiro-padrao-cientifico.tsv
    capturar 'Calculadora' programador 300 roteiro-programador.tsv
fi

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$SAIDA"

cabecalho() {   # imagem texto saída: faixa de 30 px acima do painel
    convert "$1" -background "$FUNDO" -gravity north -splice 0x30 \
        -font "$FONTE" -pointsize 15 -fill "$TEXTO" -annotate +0+7 "$2" "$3"
}
diferenca() {   # % de pixels com diferença > 24 em algum canal, sem a última linha (borda semitransparente),
                # em 16 bits por canal (ImageMagick Q16): 6168 = 24 × 257
    convert "$1" "$2" -crop 482x688+0+0 +repage -compose difference -composite -separate \
        -evaluate-sequence max -threshold 6168 -format '%[fx:100*mean]' info:
}

# 1. GIF Padrão + Científico
mapfile -t LINHAS < <(grep -v '^#' "$D/roteiro-padrao-cientifico.tsv" | grep -v '^$')
QUADROS=()
{
echo "# Diferença por quadro entre a original e a GUI da reimplementação (pixels com diferença > 24 em algum canal,"
echo "# sem a última linha, que é a borda semitransparente da janela). Gerado por gerar-demo.sh."
for i in "${!LINHAS[@]}"; do
    n=$(printf %03d "$i")
    IFS=$'\t' read -r _ legenda ms <<< "${LINHAS[$i]}"
    cabecalho "$Q/original/$n.png" 'Windows Calculator 11.2607 (original)' "$T/a.png"
    cabecalho "$Q/reimpl/$n.png" 'Python reimplementation (GUI)' "$T/b.png"
    convert "$T/a.png" \( -size 12x719 xc:"$FUNDO" \) "$T/b.png" +append +repage \
        -background "$FUNDO" -gravity south -splice 0x34 \
        -font "$FONTE" -pointsize 15 -fill "$TEXTO" -annotate +0+9 "Same input to both:  $legenda" "$T/q$n.png"
    QUADROS+=(-delay $((ms / 10)) "$T/q$n.png")
    printf '%s\t%s%%\t%s\n' "$n" "$(diferenca "$Q/original/$n.png" "$Q/reimpl/$n.png")" "$legenda"
done
} > "$D/diferencas.txt"
convert "${QUADROS[@]}" -loop 0 +dither -layers OptimizePlus "$SAIDA/demo-standard-scientific.gif"

# 2. Programador: captura da original | saída de texto real da CLI (a GUI não tem este modo)
CMD=(-m calculadora -m programador -- R:HEX '#F0' NOT)
{
    echo "\$ python -m calculadora -m programador -- R:HEX '#F0' NOT"
    echo
    (cd "$R/reimpl" && .venv/bin/python "${CMD[@]}")
} > "$T/cli.txt"
convert -background '#202020' -fill "$TEXTO" -font "$MONO" -pointsize 12 -interline-spacing 4 \
    label:"$(cat "$T/cli.txt")" -bordercolor '#202020' -border 14 \
    -gravity north -extent 'x689' "$T/cli.png"
cabecalho "$Q/programador/002.png" 'Windows Calculator 11.2607 (original)' "$T/a.png"
cabecalho "$T/cli.png" 'Python reimplementation (CLI text output)' "$T/b.png"
convert "$T/a.png" \( -size 12x719 xc:"$FUNDO" \) "$T/b.png" -gravity north +append +repage \
    -background "$FUNDO" -gravity south -splice 0x34 \
    -font "$FONTE" -pointsize 15 -fill "$TEXTO" -annotate +0+9 \
    "Programmer mode, same input: HEX, F, 0, NOT  (the GUI has no Programmer mode)" \
    "$SAIDA/programmer-original-vs-cli.png"
cp "$T/cli.txt" "$D/programador-cli.txt"

ls -l "$SAIDA"
cat "$D/diferencas.txt"
