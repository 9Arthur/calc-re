#!/usr/bin/env python3
"""Previsões da Fase 3d (modo programador): emulação das regras do motor lidas no binário (02d).
Cada função cita a rotina que emula. Não usa nada observado em execução.

Representação [O, 02d §2]: no modo inteiro o valor atual fica, depois de DisplayNum, como inteiro sem sinal
truncado à largura (FUN_18012b790: int → se negativo, (|x|−1) XOR máscara → AND máscara).
Uso: python3 -I prog3d.py  → imprime cada caso com as leituras previstas."""

W = {'QWORD': 64, 'DWORD': 32, 'WORD': 16, 'BYTE': 8}
CICLO = ['QWORD', 'DWORD', 'WORD', 'BYTE']          # [I] ordem do botão de tamanho (02d §3.2)


def chop(x, w):
    """FUN_18012b790: trunca para int (em direção a zero) e reduz módulo 2^w."""
    return int(x) % (1 << w)


def signed(v, w):
    """FUN_180116f90 em base 10 / FUN_18012d140: bit w−1 ligado → v − 2^w."""
    return v - (1 << w) if (v >> (w - 1)) & 1 else v


def agrupa(s, n, sep):
    out = []
    while len(s) > n:
        out.insert(0, s[-n:])
        s = s[:-n]
    out.insert(0, s)
    return sep.join(out)


def fmt(v, base, w):
    """NumberToString inteiro (FUN_180116f90) + agrupamento (FUN_18012c350): 16 e 2 em grupos de 4, 8 em grupos
    de 3, separador espaço (0x18017cb14); base 10 com sinal e milhar '.' (pt-BR, grupos de 3)."""
    if base == 10:
        s = signed(v, w)
        t = agrupa(str(abs(s)), 3, '.')
        return ('-' if s < 0 else '') + t
    dig = {16: '%X', 8: '%o', 2: None}[base]
    t = format(v, 'b') if base == 2 else dig % v
    return agrupa(t, 4 if base in (16, 2) else 3, ' ')


def linhas(v, w):
    return {'HEX': fmt(v, 16, w), 'DEC': fmt(v, 10, w), 'OCT': fmt(v, 8, w), 'BIN': fmt(v, 2, w)}


def limite_dec(w):
    """FUN_180111fe0: texto-limite = int(máscara/2) em decimal; e2c = len − 1 (SetMaxDigits 0x18012d820)."""
    return str(((1 << w) - 1) // 2)


def digita(digitos, base, w, negativo=False):
    """FUN_180121670 no modo inteiro: aceita até e2c dígitos; no limite, base 8 aceita mais um se a largura mod 3
    = 1 e o 1º dígito é '1', ou = 2 e o 1º dígito < '4'; base 10 compara com o texto-limite (com sinal negativo,
    o último dígito pode passar 1 do limite); bases 16 e 2 recusam. Zeros à esquerda não entram."""
    if base == 10:
        lim = limite_dec(w)
        e2c = len(lim) - 1
    else:
        bits = {16: 4, 8: 3, 2: 1}[base]
        e2c = w // bits
    txt = ''
    for d in digitos:
        if txt == '' and d == '0':
            continue
        if len(txt) < e2c:
            txt += d
            continue
        if len(txt) != e2c:
            continue
        if base == 8:
            r = w % 3
            ok = (r == 1 and txt[0] == '1') or (r == 2 and txt[0] < '4')
            if ok:
                txt += d
        elif base == 10:
            if len(txt) >= len(lim):
                continue
            k = next((i for i in range(len(txt)) if txt[i] != lim[i]), None)
            if k is None:
                if d > lim[len(txt)]:
                    if not negativo or ord(d) > ord(lim[len(txt)]) + 1:
                        continue
                txt += d
            elif lim[k] <= txt[k]:
                continue
            else:
                txt += d
    return txt


def valor_digitado(txt, base, negativo=False):
    v = int(txt, base) if txt else 0
    return -v if negativo else v


def troca_tamanho(v, w_de, w_para):
    """FUN_18012d140 + DisplayNum: bit de sinal na largura antiga → valor negativo; depois trunca na nova."""
    return chop(signed(v, w_de), w_para)


def caminho(de, para):
    """[I] cliques no botão de tamanho seguindo CICLO."""
    i = CICLO.index(de)
    p = []
    while CICLO[i] != para:
        i = (i + 1) % 4
        p.append(CICLO[i])
    return p


def shl(a, n, w):            # DoOperation 0x59: n ≥ w → 0x80000009; senão a·2^n
    return None if n >= w else chop(a << n, w)


def shr_arit(a, n, w):       # DoOperation 0x5a: a/2^n truncado; bit de sinal → OR com NOT(máscara>>n)
    if n >= w:
        return None
    m = (1 << w) - 1
    r = a >> n
    if (a >> (w - 1)) & 1:
        r |= (m >> n) ^ m
    return r


def shr_log(a, n, w):        # DoOperation 0x1f9
    return None if n >= w else a >> n


def rol(a, w, carry=None):   # SciCalcFunctions 0x63 / 0x1a0
    msb = (a >> (w - 1)) & 1
    ent = msb if carry is None else carry
    return chop((a << 1) | ent, w), msb


def ror(a, w, carry=None):   # SciCalcFunctions 0x64 / 0x1a1
    lsb = a & 1
    ent = lsb if carry is None else carry
    return (ent << (w - 1)) | (a >> 1), lsb


def nao(a, w):               # SciCalcFunctions 0x65 no modo inteiro: XOR máscara
    return a ^ ((1 << w) - 1)


def divide(a, b, w):         # DoOperation 0x5b inteiro: magnitudes, quociente truncado, sinal pelo XOR
    sa, sb = signed(a, w), signed(b, w)
    if sb == 0:
        return 'Resultado indefinido' if sa == 0 else 'Não é possível dividir por zero'
    q = abs(sa) // abs(sb)
    return chop(-q if (sa < 0) != (sb < 0) else q, w)


def resto(a, b, w):          # DoOperation 0x5f inteiro: rem das magnitudes, sinal do dividendo; b = 0 → 0x80000002
    sa, sb = signed(a, w), signed(b, w)
    if sb == 0:
        return 'Resultado indefinido'
    r = abs(sa) % abs(sb)
    return chop(-r if sa < 0 else r, w)


if __name__ == '__main__':
    Q = 64
    m1 = chop(-1, Q)
    print('-- bases --')
    for v in (255, 1000, 0x1A3, m1):
        print(v, linhas(chop(v, Q), Q))
    t = digita('123456789ABCDEF01', 16, Q); print('HEX 17 díg ->', t, linhas(int(t, 16), Q))
    t = digita('1777777777777777777777', 8, Q); print('OCT 1777.. ->', t, linhas(int(t, 8), Q))
    t = digita('2777777777777777777777', 8, Q); print('OCT 2777.. ->', t, linhas(int(t, 8), Q))
    t = digita('1' + '0' * 64, 2, Q); print('BIN 65 díg ->', len(t), linhas(int(t, 2), Q))
    t = digita('9223372036854775808', 10, Q); print('DEC 2^63 ->', t)
    t = digita('9223372036854775808', 10, Q, negativo=True); print('DEC -2^63 ->', t)
    t = digita('9223372036854775807', 10, Q); print('DEC 2^63-1 ->', t, linhas(int(t), Q))
    print('BYTE 128 ->', digita('128', 10, 8), ' BYTE 200 ->', digita('200', 10, 8), ' BYTE 127 ->', digita('127', 10, 8))
    t = digita('12345', 16, 16); print('WORD HEX 12345 ->', t, linhas(int(t, 16), 16))
    print('-- tamanhos --')
    for v0, de, para in ((300, 'QWORD', 'BYTE'), (200, 'QWORD', 'BYTE'), (65535, 'QWORD', 'BYTE'), (2147483648, 'QWORD', 'DWORD'),
                         (4294967296, 'QWORD', 'DWORD'), (2**40 - 1, 'QWORD', 'DWORD')):
        v, w = chop(v0, W[de]), W[de]
        seq = []
        for tam in caminho(de, para):
            v = troca_tamanho(v, w, W[tam]); w = W[tam]
            seq.append((tam, fmt(v, 10, w), fmt(v, 16, w)))
        print(v0, de, '->', seq)
    v, w = chop(200, 64), 64
    for tam in caminho('QWORD', 'BYTE') + caminho('BYTE', 'QWORD'):
        v = troca_tamanho(v, w, W[tam]); w = W[tam]
    print('200 Q->B->Q', fmt(v, 10, w), fmt(v, 16, w))
    v, w = chop(65535, 64), 64
    for tam in caminho('QWORD', 'BYTE') + caminho('BYTE', 'QWORD'):
        v = troca_tamanho(v, w, W[tam]); w = W[tam]; print('  65535 ->', tam, fmt(v, 10, w), fmt(v, 16, w))
    v, w = chop(-1, 32), 32
    for tam in caminho('DWORD', 'QWORD'):
        v = troca_tamanho(v, w, W[tam]); w = W[tam]; print('  DWORD -1 ->', tam, fmt(v, 10, w), fmt(v, 16, w))
    print('-- estouro / ÷ / mod --')
    print('2^63-1 + 1', fmt(chop(2**63, 64), 10, 64))
    print('D 2^31-1 + 1', fmt(chop(2**31, 32), 10, 32), ' W', fmt(chop(2**15, 16), 10, 16), ' B', fmt(chop(128, 8), 10, 8))
    print('B 100×3', fmt(chop(300, 8), 10, 8), ' 2^32·2^32', fmt(chop(2**64, 64), 10, 64), ' (2^32−1)^2', fmt(chop((2**32 - 1)**2, 64), 10, 64))
    print('7÷2', fmt(divide(7, 2, Q), 10, Q), ' −7÷2', fmt(divide(chop(-7, Q), 2, Q), 10, Q))
    print('−7 mod 3', fmt(resto(chop(-7, Q), 3, Q), 10, Q), ' 7 mod −3', fmt(resto(7, chop(-3, Q), Q), 10, Q),
          ' 5 mod 0', resto(5, 0, Q), ' 5÷0', divide(5, 0, Q), ' 0÷0', divide(0, 0, Q))
    print('1−2', linhas(chop(-1, Q), Q)['HEX'])
    print('-- bit a bit --')
    print('AND', 12 & 10, 'OR', 12 | 10, 'XOR', 12 ^ 10, 'NAND', fmt(nao(12 & 10, Q), 10, Q), fmt(nao(12 & 10, Q), 16, Q),
          'NOR', fmt(nao(12 | 10, Q), 10, Q))
    print('NOT 5', fmt(nao(5, Q), 10, Q), fmt(nao(5, Q), 16, Q), ' B NOT 5', fmt(nao(5, 8), 10, 8), fmt(nao(5, 8), 16, 8),
          ' B NOT F0', fmt(nao(0xF0, 8), 16, 8), fmt(nao(0xF0, 8), 10, 8))
    print('6 OR (1 AND 2)', 6 | (1 & 2), ' esq', (6 | 1) & 2)
    print('12 XOR (10 AND 6)', 12 ^ (10 & 6), ' esq', (12 ^ 10) & 6)
    print('1 OR (5 NAND 3)', fmt(1 | nao(5 & 3, Q), 10, Q), ' esq', fmt(nao((1 | 5) & 3, Q), 10, Q))
    print('5 + NOT(5)', fmt(nao(5, Q), 10, Q), fmt(chop(5 + signed(nao(5, Q), Q), Q), 10, Q))
    print('-- deslocamentos --')
    print('1<<4', shl(1, 4, Q), ' 1<<63', fmt(shl(1, 63, Q), 10, Q), ' 1<<64', shl(1, 64, Q))
    print('−7 >>a 1', fmt(shr_arit(chop(-7, Q), 1, Q), 10, Q), ' −16 >>a 2', fmt(shr_arit(chop(-16, Q), 2, Q), 10, Q))
    print('B 3<<7', fmt(shl(3, 7, 8), 10, 8), ' B 1<<8', shl(1, 8, 8), ' B 80 >>a 1', fmt(shr_arit(0x80, 1, 8), 16, 8),
          fmt(shr_arit(0x80, 1, 8), 10, 8), ' 8>>a64', shr_arit(8, 64, Q))
    print('1+(1<<2)', 1 + (1 << 2))
    print('−1 >>l 1', fmt(shr_log(chop(-1, Q), 1, Q), 10, Q), ' −16 >>l 60', shr_log(chop(-16, Q), 60, Q),
          ' B 80>>l1', fmt(shr_log(0x80, 1, 8), 16, 8), fmt(shr_log(0x80, 1, 8), 10, 8), ' B 5>>l8', shr_log(5, 8, 8))
    a, _ = rol(0x81, 8); b, _ = ror(a, 8); print('B 81 RoL', fmt(a, 16, 8), 'RoR', fmt(b, 16, 8), fmt(b, 10, 8))
    print('Q 1 RoR', fmt(ror(1, Q)[0], 10, Q), fmt(ror(1, Q)[0], 16, Q), ' B 1 RoR', fmt(ror(1, 8)[0], 10, 8),
          ' Q 8000.. RoL', rol(1 << 63, Q)[0])
    c = 0; v = 0x80; s = []
    for _ in range(3):
        v, c = rol(v, 8, c); s.append(fmt(v, 16, 8))
    print('B 80 RolC×3', s)
    c = 0; v = 1; s = []
    for _ in range(3):
        v, c = ror(v, 8, c); s.append(fmt(v, 16, 8))
    print('B 1 RorC×3', s)
    v, c = rol(0x80, 8, 0); v2, c = rol(5, 8, c); print('B 80 RolC, 5 RolC', fmt(v, 16, 8), fmt(v2, 16, 8))
    print('B C zera carry: 5 RolC', fmt(rol(5, 8, 0)[0], 16, 8))
    print('-- bits --')
    print('bit0+bit3', 9, ' bit63', fmt(1 << 63, 10, Q), ' B bit7', fmt(0x80, 10, 8), ' 5^bit2', 5 ^ 4,
          ' 5 + (5^1)', 5 + (5 ^ 1), ' −1^bit63', fmt(chop(-1, Q) ^ (1 << 63), 10, Q), ' 12^bit0', 12 ^ 1)
