"""Executa um caso na reimplementação e compara cada leitura com o oráculo."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calculadora import Calculadora, pressionar  # noqa: E402

_DESL = {'Arit': 'Arit', 'Log': 'Log', 'Circ': 'Circ', 'Carry': 'Carry'}


def foto(vm):
    return {'visor': vm.visor, 'expr': vm.texto_expressao, 'historico': vm.historico, 'memoria': list(vm.memoria),
            'botoes': vm.estado_botoes(), 'linhas': vm.linhas(),
            'bits': vm.bits() if vm.modo == 'programador' else set()}


def executar(caso):
    """Estado inicial = o preparo da automação: modo do caso, C, ângulo (3c), base/tamanho/deslocamento (3d).
    Uma calculadora nova equivale a esse preparo (memória e histórico vazios)."""
    vm = Calculadora(caso['modo'])
    if caso.get('angulo'):
        vm.definir_angulo(caso['angulo'])
    if caso.get('base'):
        vm.definir_base(caso['base'])
    if caso.get('tamanho'):
        vm.definir_tamanho(caso['tamanho'])
    if caso.get('deslocamento'):
        vm.deslocamento = _DESL[caso['deslocamento']]
    fotos, notas = [], []
    for tok in caso['passos'] + ['>FIM']:
        if tok in ('>', '>FIM'):
            fotos.append(foto(vm))
        elif not pressionar(vm, tok):
            notas.append(f'{tok} desabilitado, não pressionado')
    return fotos, notas


def _sem_espaco(s):
    return re.sub(r'\s+', '', s)


def comparar(fotos, reais):
    """Visor, histórico, memória, linhas e bits: exatos. Expressão: sem espaços (L20); `‹` = linha cortada na tela,
    o visível tem de ser sufixo. Botões: os que a leitura real registrou."""
    div = []
    if len(fotos) != len(reais):
        div.append(f'{len(fotos)} leituras (reais {len(reais)})')
    for i, (f, r) in enumerate(zip(fotos, reais), 1):
        tag = f"L{i} ({r['captura']})"
        if f['visor'] != r['visor']:
            div.append(f"{tag} visor {f['visor']!r} ≠ real {r['visor']!r}")
        if r.get('expr') is not None:
            e, re_ = _sem_espaco(f['expr']), _sem_espaco(r['expr'])
            ok = e.endswith(re_[1:]) if re_.startswith('‹') else e == re_
            if not ok:
                div.append(f"{tag} expressão {f['expr']!r} ≠ real {r['expr']!r} [{r['origem_expr']}]")
        if 'historico' in r and f['historico'] != r['historico']:
            div.append(f"{tag} histórico {f['historico']} ≠ real {r['historico']}")
        if 'memoria' in r and f['memoria'] != r['memoria']:
            div.append(f"{tag} memória {f['memoria']} ≠ real {r['memoria']}")
        if r.get('botoes'):
            ruins = [f"{b}={'hab' if f['botoes'].get(b) else 'des'} (real {'hab' if v else 'des'})"
                     for b, v in r['botoes'].items() if f['botoes'].get(b) != v]
            if ruins:
                div.append(f"{tag} botões " + ', '.join(ruins))
        if r.get('linhas'):
            for k, v in r['linhas'].items():
                if f['linhas'].get(k) != v:
                    div.append(f"{tag} linha {k} {f['linhas'].get(k)!r} ≠ real {v!r}")
        if r.get('bits') is not None and f['bits'] != r['bits']:
            div.append(f"{tag} bits {sorted(f['bits'])} ≠ real {sorted(r['bits'])}")
    return div
